"""Pruebas de la selección y edición de perfiles multipodcast."""
from unittest.mock import MagicMock, patch

from PySide6.QtWidgets import QLabel

import config


def _profile_paths(tmp_path):
    return (
        patch.object(config, "CONFIG_FILE", str(tmp_path / "config.ini")),
        patch.object(config, "CONFIG_DIR", str(tmp_path)),
    )


def test_setup_lists_profiles_and_selects_active(qapp, tmp_path):
    p1, p2 = _profile_paths(tmp_path)
    with p1, p2:
        config.save_profile("Uno", "https://example.test/uno", "token-1")
        active_id = config.save_profile(
            "Dos", "https://example.test/dos", "token-2"
        )

        from ui.setup_dialog import SetupDialog
        dialog = SetupDialog()

        assert dialog.profile_combo.count() == 2
        assert dialog.profile_combo.currentData() == active_id
        assert dialog.name_edit.text() == "Dos"


def test_setup_creates_and_activates_profile_after_connection_test(qapp, tmp_path):
    p1, p2 = _profile_paths(tmp_path)
    with p1, p2:
        from ui.setup_dialog import SetupDialog
        dialog = SetupDialog()
        dialog.name_edit.setText("A Ratos Podcast")
        dialog.url_edit.setText("https://www.aratospodcast.com/aratos/")
        dialog.token_edit.setText("content-token")

        with patch("ui.setup_dialog.EasyPodcastAPI") as api_class:
            api_class.return_value.get_podcast.return_value = {"title": "A Ratos"}
            dialog._on_accept()

        active = config.get_active_profile()
        assert active["name"] == "A Ratos Podcast"
        assert active["base_url"] == "https://www.aratospodcast.com/aratos"
        api_class.assert_called_once_with(
            "https://www.aratospodcast.com/aratos/", "content-token"
        )


def test_main_window_switches_active_profile(qapp, tmp_path):
    p1, p2 = _profile_paths(tmp_path)
    with p1, p2:
        first_id = config.save_profile(
            "Uno", "https://example.test/uno", "token-1"
        )
        config.save_profile("Dos", "https://example.test/dos", "token-2")

        tab_widget = lambda *_args, **_kwargs: QLabel("tab")
        with (
            patch("ui.main_window.EasyPodcastAPI", return_value=MagicMock()),
            patch("ui.main_window.EpisodesTab", side_effect=tab_widget),
            patch("ui.main_window.PodcastTab", side_effect=tab_widget),
            patch("ui.main_window.PagesTab", side_effect=tab_widget),
            patch("ui.main_window.SocialTab", side_effect=tab_widget),
            patch("ui.main_window.ToolsTab", side_effect=tab_widget),
        ):
            from ui.main_window import MainWindow
            window = MainWindow()
            window.profile_combo.setCurrentIndex(
                window.profile_combo.findData(first_id)
            )

        assert config.get_active_profile()["id"] == first_id
        assert "Uno" in window.status.currentMessage()
