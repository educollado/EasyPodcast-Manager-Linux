import os
import mimetypes
from contextlib import ExitStack

import requests


class APIError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class EasyPodcastAPI:
    def __init__(self, base_url, token):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def _url(self, path):
        return f"{self.base_url}/api/v1{path}"

    def _handle(self, response):
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            try:
                detail = response.json()
                msg = detail.get("message") or detail.get("error") or str(detail)
            except Exception:
                msg = response.text or str(e)
            raise APIError(
                f"HTTP {response.status_code}: {msg}",
                status_code=response.status_code,
            ) from e
        if response.status_code == 204 or not response.content:
            return {}
        body = response.json()
        if isinstance(body, dict) and body.get("success") and "data" in body:
            return body["data"]
        return body

    # --- Episodes ---

    def _get_all_pages(self, path, params=None):
        """Obtiene todos los elementos de un endpoint paginado de EasyPodcast."""
        request_params = dict(params or {})
        request_params.update({"page": 1, "limit": 100})
        response = self._handle(
            self.session.get(self._url(path), params=request_params)
        )

        # Compatibilidad con versiones antiguas de la API que devolvían una lista.
        if not isinstance(response, dict) or not isinstance(response.get("items"), list):
            return response

        combined = dict(response)
        items = list(response["items"])
        total_pages = max(1, int(response.get("total_pages") or 1))

        for page in range(2, total_pages + 1):
            request_params["page"] = page
            page_data = self._handle(
                self.session.get(self._url(path), params=dict(request_params))
            )
            if not isinstance(page_data, dict) or not isinstance(page_data.get("items"), list):
                break
            items.extend(page_data["items"])

        combined["items"] = items
        combined["page"] = 1
        combined["limit"] = 100
        combined["total"] = int(combined.get("total") or len(items))
        return combined

    def get_episodes(self, status=None):
        params = {}
        if status:
            params["status"] = status
        return self._get_all_pages("/episodes", params)

    def get_episode(self, episode_id):
        r = self.session.get(self._url(f"/episodes/{episode_id}"))
        return self._handle(r)

    def _post_multipart(self, url, data, audio_path=None, image_path=None):
        form_data = {k: str(v) for k, v in data.items() if v is not None and v != ""}
        with ExitStack() as stack:
            files = {}
            if audio_path:
                mime = mimetypes.guess_type(audio_path)[0] or "audio/mpeg"
                audio_file = stack.enter_context(open(audio_path, "rb"))
                files["audio_file"] = (os.path.basename(audio_path), audio_file, mime)
                form_data["audio_size_bytes"] = str(os.path.getsize(audio_path))
                form_data["audio_mime_type"] = mime
            if image_path:
                mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
                image_file = stack.enter_context(open(image_path, "rb"))
                files["image_file"] = (os.path.basename(image_path), image_file, mime)
            r = self.session.post(
                url,
                data=form_data,
                files=files,
                headers={"Content-Type": None},
            )
            return self._handle(r)

    def create_episode(self, data, audio_path=None, image_path=None):
        if audio_path or image_path:
            return self._post_multipart(self._url("/episodes"), data, audio_path, image_path)
        r = self.session.post(self._url("/episodes"), json=data)
        return self._handle(r)

    def update_episode(self, episode_id, data, audio_path=None, image_path=None):
        if audio_path or image_path:
            return self._post_multipart(self._url(f"/episodes/{episode_id}"), data, audio_path, image_path)
        r = self.session.post(self._url(f"/episodes/{episode_id}"), json=data)
        return self._handle(r)

    def delete_episode(self, episode_id):
        r = self.session.delete(self._url(f"/episodes/{episode_id}"))
        return self._handle(r)

    # --- Podcast metadata ---

    def get_podcast(self):
        r = self.session.get(self._url("/podcast"))
        return self._handle(r)

    def update_podcast(self, data, image_path=None, hero_image_path=None):
        """Actualiza el podcast y sube opcionalmente sus imágenes."""
        if not image_path and not hero_image_path:
            r = self.session.post(self._url("/podcast"), json=data)
            return self._handle(r)

        form_data = {k: str(v) for k, v in data.items() if v is not None}
        with ExitStack() as stack:
            files = {}
            if image_path:
                mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
                image_file = stack.enter_context(open(image_path, "rb"))
                files["image_file"] = (
                    os.path.basename(image_path), image_file, mime,
                )
            if hero_image_path:
                mime = mimetypes.guess_type(hero_image_path)[0] or "image/jpeg"
                hero_file = stack.enter_context(open(hero_image_path, "rb"))
                files["hero_image_file"] = (
                    os.path.basename(hero_image_path), hero_file, mime,
                )
            r = self.session.post(
                self._url("/podcast"),
                data=form_data,
                files=files,
                headers={"Content-Type": None},
            )
            return self._handle(r)

    # --- Pages ---

    def get_pages(self):
        return self._get_all_pages("/pages")

    def get_page(self, page_id):
        r = self.session.get(self._url(f"/pages/{page_id}"))
        return self._handle(r)

    def create_page(self, data):
        r = self.session.post(self._url("/pages"), json=data)
        return self._handle(r)

    def update_page(self, page_id, data):
        r = self.session.post(self._url(f"/pages/{page_id}"), json=data)
        return self._handle(r)

    def delete_page(self, page_id):
        r = self.session.delete(self._url(f"/pages/{page_id}"))
        return self._handle(r)

    # --- Social networks ---

    def get_social(self):
        r = self.session.get(self._url("/social"))
        return self._handle(r)

    def update_social(self, data):
        r = self.session.post(self._url("/social"), json=data)
        return self._handle(r)

    # --- Tools ---

    def clear_cache(self):
        r = self.session.post(self._url("/cache/clear"))
        return self._handle(r)

    def regenerate_feed(self):
        r = self.session.post(self._url("/feed/regenerate"))
        return self._handle(r)

    def regenerate_images(self):
        r = self.session.post(self._url("/cache/regenerate-images"))
        return self._handle(r)

    def get_stats(self, year=None):
        params = {"year": year} if year else None
        r = self.session.get(self._url("/stats"), params=params)
        return self._handle(r)

    # --- Sistema ---

    def get_system_version(self):
        r = self.session.get(self._url("/system/version"))
        return self._handle(r)

    def system_update(self):
        r = self.session.post(self._url("/system/update"))
        return self._handle(r)
