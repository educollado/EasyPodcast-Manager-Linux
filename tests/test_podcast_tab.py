"""Tests para la edición de metadatos e imagen Hero del podcast."""
from unittest.mock import MagicMock, patch


PODCAST = {
    "title": "Mi podcast",
    "description": "Descripción",
    "hero_image_url": "https://example.com/hero.jpg",
    "rss_item_limit": 50,
    "home_items_per_page": 12,
    "write_audio_metadata": True,
    "cache_enabled": False,
    "app_language": "es",
}


def make_tab(qapp):
    from ui.podcast_tab import PodcastTab

    api = MagicMock()
    api.get_podcast.return_value = dict(PODCAST)
    return PodcastTab(api), api


class TestPodcastHero:
    def test_refresh_populates_hero_url(self, qapp):
        tab, _ = make_tab(qapp)

        assert tab.hero_image_url_edit.text() == PODCAST["hero_image_url"]
        assert tab._hero_image_path is None

    def test_refresh_populates_new_api_fields(self, qapp):
        tab, _ = make_tab(qapp)

        assert tab.rss_item_limit_edit.text() == "50"
        assert tab.home_items_per_page_edit.text() == "12"
        assert tab.write_audio_metadata_combo.currentData() is True
        assert tab.cache_enabled_combo.currentData() is False
        assert tab.app_language_edit.text() == "es"

    def test_save_sends_hero_url_as_json(self, qapp):
        tab, api = make_tab(qapp)
        api.update_podcast.return_value = dict(PODCAST)
        tab.hero_image_url_edit.setText("https://example.com/new-hero.webp")

        with patch("ui.podcast_tab.QMessageBox.information"):
            tab._on_save()

        data = api.update_podcast.call_args.args[0]
        assert data["hero_image_url"] == "https://example.com/new-hero.webp"
        assert "hero_image_path" not in api.update_podcast.call_args.kwargs

    def test_save_sends_new_api_fields(self, qapp):
        tab, api = make_tab(qapp)
        api.update_podcast.return_value = dict(PODCAST)

        with patch("ui.podcast_tab.QMessageBox.information"):
            tab._on_save()

        data = api.update_podcast.call_args.args[0]
        assert data["rss_item_limit"] == 50
        assert data["home_items_per_page"] == 12
        assert data["write_audio_metadata"] is True
        assert data["cache_enabled"] is False
        assert data["app_language"] == "es"

    def test_save_uploads_selected_hero_file(self, qapp, tmp_path):
        tab, api = make_tab(qapp)
        hero = tmp_path / "cabecera.png"
        hero.write_bytes(b"image")
        api.update_podcast.return_value = {
            **PODCAST,
            "hero_image_url": "/images/cabecera.webp",
        }
        tab._hero_image_path = str(hero)
        tab.hero_file_label.setText(hero.name)
        tab.hero_image_url_edit.setText("")

        with patch("ui.podcast_tab.QMessageBox.information"):
            tab._on_save()

        call = api.update_podcast.call_args
        assert call.args[0]["hero_image_url"] == ""
        assert call.kwargs["hero_image_path"] == str(hero)
        assert tab.hero_image_url_edit.text() == "/images/cabecera.webp"
        assert tab._hero_image_path is None

    def test_clearing_url_removes_hero(self, qapp):
        tab, api = make_tab(qapp)
        api.update_podcast.return_value = {**PODCAST, "hero_image_url": ""}
        tab._clear_hero()

        with patch("ui.podcast_tab.QMessageBox.information"):
            tab._on_save()

        assert api.update_podcast.call_args.args[0]["hero_image_url"] == ""

    def test_editing_url_cancels_selected_file(self, qapp):
        tab, _ = make_tab(qapp)
        tab._hero_image_path = "/tmp/hero.png"

        tab._on_hero_url_edited("https://example.com/other.jpg")

        assert tab._hero_image_path is None
