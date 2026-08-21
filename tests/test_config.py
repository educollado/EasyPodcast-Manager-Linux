"""Tests para config.py — carga, guardado y validación de credenciales."""
import configparser
import os
from unittest.mock import patch

import pytest

import config as cfg


def _patch_paths(tmp_path):
    """Context manager que redirige CONFIG_FILE y CONFIG_DIR a tmp_path."""
    config_file = str(tmp_path / "config.ini")
    config_dir = str(tmp_path)
    return (
        patch.object(cfg, "CONFIG_FILE", config_file),
        patch.object(cfg, "CONFIG_DIR", config_dir),
    )


# ---------------------------------------------------------------------------
# has_config
# ---------------------------------------------------------------------------

class TestHasConfig:
    def test_false_when_file_missing(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.has_config() is False

    def test_false_when_file_empty(self, tmp_path):
        (tmp_path / "config.ini").write_text("")
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.has_config() is False

    def test_false_when_section_missing(self, tmp_path):
        (tmp_path / "config.ini").write_text("[other]\nkey=val\n")
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.has_config() is False

    def test_false_when_url_empty(self, tmp_path):
        (tmp_path / "config.ini").write_text(
            "[easypodcast]\nbase_url=\ntoken=abc\n"
        )
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.has_config() is False

    def test_false_when_token_empty(self, tmp_path):
        (tmp_path / "config.ini").write_text(
            "[easypodcast]\nbase_url=https://x.com\ntoken=\n"
        )
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.has_config() is False

    def test_true_after_save(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://podcast.com", "tok123")
            assert cfg.has_config() is True


# ---------------------------------------------------------------------------
# save_credentials
# ---------------------------------------------------------------------------

class TestSaveCredentials:
    def test_creates_file(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://example.com", "mytoken")
            assert os.path.exists(str(tmp_path / "config.ini"))

    def test_strips_trailing_slash_from_url(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://example.com////", "tok")
            url, _ = cfg.get_credentials()
            assert not url.endswith("/")
            assert url == "https://example.com"

    def test_token_saved_verbatim(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://example.com", "super-secret-token")
            _, token = cfg.get_credentials()
            assert token == "super-secret-token"

    def test_ini_section_name(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://example.com", "tok")
            c = configparser.ConfigParser()
            c.read(str(tmp_path / "config.ini"))
            assert "easypodcast" in c


# ---------------------------------------------------------------------------
# get_credentials
# ---------------------------------------------------------------------------

class TestGetCredentials:
    def test_returns_none_none_when_no_file(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            url, token = cfg.get_credentials()
            assert url is None
            assert token is None

    def test_returns_saved_values(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://mypodcast.com", "xyz")
            url, token = cfg.get_credentials()
            assert url == "https://mypodcast.com"
            assert token == "xyz"

    def test_strips_whitespace(self, tmp_path):
        (tmp_path / "config.ini").write_text(
            "[easypodcast]\nbase_url=  https://example.com  \ntoken=  abc  \n"
        )
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            url, token = cfg.get_credentials()
            assert url == "https://example.com"
            assert token == "abc"

    def test_overwrite_preserves_latest(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            cfg.save_credentials("https://old.com", "old-token")
            cfg.save_credentials("https://new.com", "new-token")
            url, token = cfg.get_credentials()
            assert url == "https://new.com"
            assert token == "new-token"


class TestProfiles:
    def test_multiple_profiles_and_active_selection(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            first = cfg.save_profile(
                "Podcast uno", "https://example.com/uno", "token-1"
            )
            second = cfg.save_profile(
                "Podcast dos", "https://example.com/dos", "token-2"
            )

            assert len(cfg.get_profiles()) == 2
            assert cfg.get_active_profile()["id"] == second
            assert cfg.set_active_profile(first) is True
            assert cfg.get_credentials() == ("https://example.com/uno", "token-1")

    def test_update_profile_keeps_identifier(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            profile_id = cfg.save_profile("Original", "https://x.test/one", "a")
            cfg.save_profile(
                "Renombrado", "https://x.test/two/", "b", profile_id=profile_id
            )

            profiles = cfg.get_profiles()
            assert profiles == [{
                "id": profile_id,
                "name": "Renombrado",
                "base_url": "https://x.test/two",
                "token": "b",
            }]

    def test_delete_active_profile_selects_remaining(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            first = cfg.save_profile("Uno", "https://x.test/uno", "a")
            second = cfg.save_profile("Dos", "https://x.test/dos", "b")
            cfg.delete_profile(second)

            assert cfg.get_active_profile()["id"] == first

    def test_legacy_configuration_is_exposed_as_profile(self, tmp_path):
        (tmp_path / "config.ini").write_text(
            "[easypodcast]\nbase_url=https://example.com/aratos\ntoken=abc\n"
        )
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            profile = cfg.get_active_profile()
            assert profile["id"] == "legacy"
            assert profile["name"] == "aratos"

            cfg.save_profile(
                "A Ratos Podcast", profile["base_url"], profile["token"],
                profile_id=profile["id"],
            )
            assert cfg.get_active_profile()["name"] == "A Ratos Podcast"
            assert "base_url" not in cfg.load_config()["easypodcast"]

    def test_unknown_profile_cannot_be_activated(self, tmp_path):
        p1, p2 = _patch_paths(tmp_path)
        with p1, p2:
            assert cfg.set_active_profile("missing") is False
