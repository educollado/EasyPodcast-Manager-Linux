"""Tests para api.py — construcción de URLs, manejo de respuestas y errores."""
import pytest
import requests
from unittest.mock import MagicMock

from api import EasyPodcastAPI, APIError

BASE_URL = "https://podcast.example.com"
TOKEN = "test-token"


def make_api():
    return EasyPodcastAPI(BASE_URL, TOKEN)


def mock_ok(json_data, status_code=200):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.content = b"data"
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


def mock_no_content():
    resp = MagicMock(spec=requests.Response)
    resp.status_code = 204
    resp.content = b""
    resp.raise_for_status = MagicMock()
    return resp


def mock_error(status_code, json_data=None, text="Error"):
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.content = b"err"
    resp.text = text
    if json_data is not None:
        resp.json.return_value = json_data
    else:
        resp.json.side_effect = ValueError("no json")
    resp.raise_for_status.side_effect = requests.HTTPError(response=resp)
    return resp


# ---------------------------------------------------------------------------
# Construcción de URLs y cabeceras
# ---------------------------------------------------------------------------

class TestInit:
    def test_trailing_slash_stripped(self):
        api = EasyPodcastAPI("https://example.com/", TOKEN)
        assert api.base_url == "https://example.com"

    def test_multiple_trailing_slashes_stripped(self):
        api = EasyPodcastAPI("https://example.com///", TOKEN)
        assert api.base_url == "https://example.com"

    def test_url_format(self):
        api = make_api()
        assert api._url("/episodes") == f"{BASE_URL}/api/v1/episodes"

    def test_auth_header(self):
        api = make_api()
        assert api.session.headers["Authorization"] == f"Bearer {TOKEN}"

    def test_accept_header(self):
        api = make_api()
        assert api.session.headers["Accept"] == "application/json"


# ---------------------------------------------------------------------------
# _handle: desempaquetado y errores
# ---------------------------------------------------------------------------

class TestHandle:
    def test_returns_data_from_success_wrapper(self):
        api = make_api()
        resp = mock_ok({"success": True, "data": [1, 2, 3]})
        assert api._handle(resp) == [1, 2, 3]

    def test_returns_body_without_wrapper(self):
        api = make_api()
        resp = mock_ok({"title": "Podcast"})
        assert api._handle(resp) == {"title": "Podcast"}

    def test_returns_list_body_directly(self):
        api = make_api()
        episodes = [{"id": 1}, {"id": 2}]
        resp = mock_ok(episodes)
        assert api._handle(resp) == episodes

    def test_204_returns_empty_dict(self):
        api = make_api()
        assert api._handle(mock_no_content()) == {}

    def test_empty_content_returns_empty_dict(self):
        api = make_api()
        resp = MagicMock(spec=requests.Response)
        resp.status_code = 200
        resp.content = b""
        resp.raise_for_status = MagicMock()
        assert api._handle(resp) == {}

    def test_http_error_raises_api_error(self):
        api = make_api()
        with pytest.raises(APIError):
            api._handle(mock_error(500))

    def test_http_error_includes_status_code(self):
        api = make_api()
        with pytest.raises(APIError, match="422"):
            api._handle(mock_error(422, json_data={"message": "Validation failed"}))

    def test_http_error_includes_message_from_json(self):
        api = make_api()
        with pytest.raises(APIError, match="Validation failed"):
            api._handle(mock_error(422, json_data={"message": "Validation failed"}))

    def test_http_error_uses_error_key(self):
        api = make_api()
        with pytest.raises(APIError, match="Forbidden") as exc:
            api._handle(mock_error(403, json_data={"error": "Forbidden"}))
        assert exc.value.status_code == 403

    def test_http_error_falls_back_to_text(self):
        api = make_api()
        with pytest.raises(APIError):
            api._handle(mock_error(500, text="Internal Server Error"))

    def test_success_false_not_unwrapped(self):
        """Si success=False, no desempaquetar data."""
        api = make_api()
        body = {"success": False, "data": []}
        resp = mock_ok(body)
        assert api._handle(resp) == body


# ---------------------------------------------------------------------------
# Episodios
# ---------------------------------------------------------------------------

class TestEpisodes:
    def test_get_episodes_no_filter(self):
        api = make_api()
        episodes = [{"id": 1, "title": "Ep 1"}]
        api.session.get = MagicMock(return_value=mock_ok(episodes))
        result = api.get_episodes()
        api.session.get.assert_called_once_with(
            f"{BASE_URL}/api/v1/episodes",
            params={"page": 1, "limit": 100},
        )
        assert result == episodes

    def test_get_episodes_with_status_filter(self):
        api = make_api()
        api.session.get = MagicMock(return_value=mock_ok([]))
        api.get_episodes(status="published")
        api.session.get.assert_called_once_with(
            f"{BASE_URL}/api/v1/episodes",
            params={"status": "published", "page": 1, "limit": 100},
        )

    def test_get_episodes_draft_filter(self):
        api = make_api()
        api.session.get = MagicMock(return_value=mock_ok([]))
        api.get_episodes(status="draft")
        _, kwargs = api.session.get.call_args
        assert kwargs["params"]["status"] == "draft"

    def test_get_episodes_combines_all_pages(self):
        api = make_api()
        first = {
            "items": [{"id": 1}],
            "total": 2,
            "page": 1,
            "limit": 1,
            "total_pages": 2,
        }
        second = {
            "items": [{"id": 2}],
            "total": 2,
            "page": 2,
            "limit": 1,
            "total_pages": 2,
        }
        api.session.get = MagicMock(
            side_effect=[mock_ok(first), mock_ok(second)]
        )

        result = api.get_episodes()

        assert result["items"] == [{"id": 1}, {"id": 2}]
        assert api.session.get.call_count == 2
        assert api.session.get.call_args_list[1].kwargs["params"]["page"] == 2

    def test_get_episode_by_id(self):
        api = make_api()
        ep = {"id": 5, "title": "Test"}
        api.session.get = MagicMock(return_value=mock_ok(ep))
        result = api.get_episode(5)
        api.session.get.assert_called_once_with(f"{BASE_URL}/api/v1/episodes/5")
        assert result == ep

    def test_create_episode_json(self):
        api = make_api()
        data = {"title": "New Ep", "status": "draft"}
        api.session.post = MagicMock(return_value=mock_ok({"id": 10, **data}))
        api.create_episode(data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/episodes", json=data
        )

    def test_update_episode_json(self):
        api = make_api()
        data = {"title": "Updated"}
        api.session.post = MagicMock(return_value=mock_ok({"id": 1, **data}))
        api.update_episode(1, data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/episodes/1", json=data
        )

    def test_episode_multipart_preserves_empty_explicit(self, tmp_path):
        api = make_api()
        audio = tmp_path / "episode.mp3"
        audio.write_bytes(b"audio")
        api.session.post = MagicMock(return_value=mock_ok({"id": 1}))

        api.create_episode(
            {"title": "Episode", "content": "Body", "explicit": ""},
            audio_path=str(audio),
        )

        call = api.session.post.call_args
        assert call.kwargs["data"]["explicit"] == ""
        assert call.kwargs["files"]["audio_file"][1].closed

    def test_delete_episode(self):
        api = make_api()
        api.session.delete = MagicMock(return_value=mock_no_content())
        api.delete_episode(3)
        api.session.delete.assert_called_once_with(f"{BASE_URL}/api/v1/episodes/3")

    def test_get_episodes_raises_on_401(self):
        api = make_api()
        api.session.get = MagicMock(
            return_value=mock_error(401, json_data={"message": "Unauthorized"})
        )
        with pytest.raises(APIError):
            api.get_episodes()

    def test_get_episodes_raises_on_network_error(self):
        api = make_api()
        api.session.get = MagicMock(side_effect=requests.ConnectionError("unreachable"))
        with pytest.raises(requests.ConnectionError):
            api.get_episodes()


# ---------------------------------------------------------------------------
# Podcast
# ---------------------------------------------------------------------------

class TestPodcast:
    def test_get_podcast(self):
        api = make_api()
        pod = {"title": "My Podcast"}
        api.session.get = MagicMock(return_value=mock_ok(pod))
        assert api.get_podcast() == pod
        api.session.get.assert_called_once_with(f"{BASE_URL}/api/v1/podcast")

    def test_update_podcast(self):
        api = make_api()
        data = {"title": "Updated Podcast"}
        api.session.post = MagicMock(return_value=mock_ok(data))
        api.update_podcast(data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/podcast", json=data
        )

    def test_update_podcast_with_hero_image(self, tmp_path):
        api = make_api()
        hero = tmp_path / "hero.png"
        hero.write_bytes(b"fake image")
        updated = {"title": "Podcast", "hero_image_url": "/images/hero.webp"}
        api.session.post = MagicMock(return_value=mock_ok(updated))

        result = api.update_podcast(
            {"title": "Podcast", "hero_image_url": ""},
            hero_image_path=str(hero),
        )

        assert result == updated
        call = api.session.post.call_args
        assert call.args == (f"{BASE_URL}/api/v1/podcast",)
        assert call.kwargs["data"] == {
            "title": "Podcast",
            "hero_image_url": "",
        }
        filename, file_object, mime = call.kwargs["files"]["hero_image_file"]
        assert filename == "hero.png"
        assert file_object.closed
        assert mime == "image/png"
        assert call.kwargs["headers"] == {"Content-Type": None}


# ---------------------------------------------------------------------------
# Páginas
# ---------------------------------------------------------------------------

class TestPages:
    def test_get_pages(self):
        api = make_api()
        pages = [{"id": 1, "title": "About"}]
        api.session.get = MagicMock(return_value=mock_ok(pages))
        assert api.get_pages() == pages
        api.session.get.assert_called_once_with(
            f"{BASE_URL}/api/v1/pages",
            params={"page": 1, "limit": 100},
        )

    def test_get_pages_combines_all_pages(self):
        api = make_api()
        api.session.get = MagicMock(side_effect=[
            mock_ok({
                "items": [{"id": 1}],
                "total": 2,
                "total_pages": 2,
            }),
            mock_ok({
                "items": [{"id": 2}],
                "total": 2,
                "total_pages": 2,
            }),
        ])

        result = api.get_pages()

        assert [page["id"] for page in result["items"]] == [1, 2]

    def test_get_page_by_id(self):
        api = make_api()
        page = {"id": 2, "title": "Contact"}
        api.session.get = MagicMock(return_value=mock_ok(page))
        assert api.get_page(2) == page
        api.session.get.assert_called_once_with(f"{BASE_URL}/api/v1/pages/2")

    def test_create_page(self):
        api = make_api()
        data = {"title": "New Page", "status": "draft"}
        api.session.post = MagicMock(return_value=mock_ok({"id": 2, **data}))
        api.create_page(data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/pages", json=data
        )

    def test_update_page(self):
        api = make_api()
        data = {"title": "Updated Page"}
        api.session.post = MagicMock(return_value=mock_ok(data))
        api.update_page(7, data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/pages/7", json=data
        )

    def test_delete_page(self):
        api = make_api()
        api.session.delete = MagicMock(return_value=mock_no_content())
        api.delete_page(2)
        api.session.delete.assert_called_once_with(f"{BASE_URL}/api/v1/pages/2")


# ---------------------------------------------------------------------------
# Social
# ---------------------------------------------------------------------------

class TestSocial:
    def test_get_social(self):
        api = make_api()
        social = {"twitter": "https://twitter.com/me"}
        api.session.get = MagicMock(return_value=mock_ok(social))
        assert api.get_social() == social
        api.session.get.assert_called_once_with(f"{BASE_URL}/api/v1/social")

    def test_update_social(self):
        api = make_api()
        data = {"twitter": "https://twitter.com/me"}
        api.session.post = MagicMock(return_value=mock_ok(data))
        api.update_social(data)
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/social", json=data
        )


# ---------------------------------------------------------------------------
# Herramientas
# ---------------------------------------------------------------------------

class TestTools:
    def test_clear_cache(self):
        api = make_api()
        api.session.post = MagicMock(return_value=mock_ok({"cleared": True}))
        api.clear_cache()
        api.session.post.assert_called_once_with(f"{BASE_URL}/api/v1/cache/clear")

    def test_regenerate_feed(self):
        api = make_api()
        api.session.post = MagicMock(return_value=mock_ok({}))
        api.regenerate_feed()
        api.session.post.assert_called_once_with(f"{BASE_URL}/api/v1/feed/regenerate")

    def test_regenerate_images(self):
        api = make_api()
        api.session.post = MagicMock(return_value=mock_ok({}))
        api.regenerate_images()
        api.session.post.assert_called_once_with(
            f"{BASE_URL}/api/v1/cache/regenerate-images"
        )

    def test_get_stats_returns_nested_dict(self):
        api = make_api()
        stats = {
            "episodes": {"published": 10, "drafts": 2, "total": 12},
            "cache": {"enabled": True, "files": 45, "size_bytes": 987654},
        }
        api.session.get = MagicMock(return_value=mock_ok(stats))
        result = api.get_stats()
        assert result["episodes"]["total"] == 12
        assert result["cache"]["enabled"] is True
        api.session.get.assert_called_once_with(
            f"{BASE_URL}/api/v1/stats", params=None
        )

    def test_get_stats_filters_by_year(self):
        api = make_api()
        api.session.get = MagicMock(return_value=mock_ok({}))

        api.get_stats(year=2026)

        api.session.get.assert_called_once_with(
            f"{BASE_URL}/api/v1/stats", params={"year": 2026}
        )


# ---------------------------------------------------------------------------
# Sistema
# ---------------------------------------------------------------------------

class TestSystem:
    def test_get_system_version(self):
        api = make_api()
        version_data = {
            "current_version": "1.2.3",
            "latest_version": "1.2.3",
            "update_available": False,
        }
        api.session.get = MagicMock(return_value=mock_ok(version_data))
        result = api.get_system_version()
        assert result["current_version"] == "1.2.3"
        assert result["update_available"] is False

    def test_system_update(self):
        api = make_api()
        update_data = {
            "message": "Updated",
            "updated_from": "1.0.0",
            "updated_to": "1.1.0",
        }
        api.session.post = MagicMock(return_value=mock_ok(update_data))
        result = api.system_update()
        assert result["updated_to"] == "1.1.0"
        api.session.post.assert_called_once_with(f"{BASE_URL}/api/v1/system/update")
