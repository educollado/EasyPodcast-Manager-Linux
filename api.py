import os
import mimetypes
import requests


class APIError(Exception):
    pass


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
            raise APIError(f"HTTP {response.status_code}: {msg}") from e
        if response.status_code == 204 or not response.content:
            return {}
        body = response.json()
        if isinstance(body, dict) and body.get("success") and "data" in body:
            return body["data"]
        return body

    # --- Episodes ---

    def get_episodes(self, status=None):
        params = {}
        if status:
            params["status"] = status
        r = self.session.get(self._url("/episodes"), params=params)
        return self._handle(r)

    def get_episode(self, episode_id):
        r = self.session.get(self._url(f"/episodes/{episode_id}"))
        return self._handle(r)

    def _post_multipart(self, url, data, audio_path=None, image_path=None):
        files = {}
        form_data = {k: str(v) for k, v in data.items() if v is not None and v != ""}
        if audio_path:
            mime = mimetypes.guess_type(audio_path)[0] or "audio/mpeg"
            files["audio_file"] = (os.path.basename(audio_path), open(audio_path, "rb"), mime)
            form_data["audio_size_bytes"] = str(os.path.getsize(audio_path))
            form_data["audio_mime_type"] = mime
        if image_path:
            mime = mimetypes.guess_type(image_path)[0] or "image/jpeg"
            files["image_file"] = (os.path.basename(image_path), open(image_path, "rb"), mime)
        r = self.session.post(url, data=form_data, files=files, headers={"Content-Type": None})
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

    def update_podcast(self, data):
        r = self.session.post(self._url("/podcast"), json=data)
        return self._handle(r)

    # --- Pages ---

    def get_pages(self):
        r = self.session.get(self._url("/pages"))
        return self._handle(r)

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

    def get_stats(self):
        r = self.session.get(self._url("/stats"))
        return self._handle(r)

    # --- Sistema ---

    def get_system_version(self):
        r = self.session.get(self._url("/system/version"))
        return self._handle(r)

    def system_update(self):
        r = self.session.post(self._url("/system/update"))
        return self._handle(r)
