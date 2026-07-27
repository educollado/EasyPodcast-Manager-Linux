"""Tests para EpisodeDialog — validación, población de campos y get_data."""
import pytest
from unittest.mock import MagicMock, patch


FULL_EPISODE = {
    "title": "Ep 1",
    "description": "Test description",
    "content": "Long content",
    "audio_url": "https://example.com/audio.mp3",
    "audio_size_bytes": 5_000_000,
    "audio_mime_type": "audio/mpeg",
    "image_url": "https://example.com/image.jpg",
    "duration": "00:30:00",
    "season_number": 2,
    "episode_number": 5,
    "episode_type": "full",
    "status": "published",
    "published_at": "2024-01-15 10:00:00",
}


@pytest.fixture
def dialog(qapp):
    from ui.episode_dialog import EpisodeDialog
    return EpisodeDialog()


@pytest.fixture
def edit_dialog(qapp):
    from ui.episode_dialog import EpisodeDialog
    return EpisodeDialog(episode=FULL_EPISODE)


# ---------------------------------------------------------------------------
# Diálogo nuevo (sin datos previos)
# ---------------------------------------------------------------------------

class TestNewEpisodeDialog:
    def test_window_title_new(self, dialog):
        assert "Nuevo episodio" in dialog.windowTitle()

    def test_title_field_empty(self, dialog):
        assert dialog.title_edit.text() == ""

    def test_description_field_empty(self, dialog):
        assert dialog.description_edit.toPlainText() == ""

    def test_default_status_is_draft(self, dialog):
        assert dialog.status_combo.currentText() == "draft"

    def test_default_type_is_full(self, dialog):
        assert dialog.episode_type_combo.currentText() == "full"

    def test_audio_path_none_initially(self, dialog):
        assert dialog._audio_path is None

    def test_image_path_none_initially(self, dialog):
        assert dialog._image_path is None

    def test_get_files_returns_none_audio(self, dialog):
        assert dialog.get_files()["audio"] is None

    def test_get_files_returns_none_image(self, dialog):
        assert dialog.get_files()["image"] is None

    def test_audio_player_is_lazy(self, dialog):
        assert dialog.audio_url_edit._player is None


# ---------------------------------------------------------------------------
# Validación — _on_accept
# ---------------------------------------------------------------------------

class TestEpisodeValidation:
    def _fill_valid(self, dialog):
        dialog.title_edit.setText("Título válido")
        dialog.content_edit.setPlainText("Contenido válido")
        dialog.audio_url_edit.setText("https://example.com/audio.mp3")
        dialog.audio_size_edit.setText("5000000")
        dialog.status_combo.setCurrentText("published")

    def test_warning_when_title_empty(self, dialog):
        dialog.description_edit.setPlainText("desc")
        dialog.audio_url_edit.setText("https://x.com/a.mp3")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_called_once()

    def test_warning_when_content_empty_for_published(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.audio_url_edit.setText("https://x.com/a.mp3")
        dialog.audio_size_edit.setText("1000")
        dialog.status_combo.setCurrentText("published")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_called_once()

    def test_warning_when_no_audio(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.content_edit.setPlainText("Contenido")
        dialog.status_combo.setCurrentText("published")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            assert "Audio" in str(mock_warn.call_args)

    def test_no_warning_with_audio_url(self, dialog):
        self._fill_valid(dialog)
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_not_called()

    def test_no_warning_with_audio_file(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.content_edit.setPlainText("Contenido")
        dialog._audio_path = "/tmp/audio.mp3"
        dialog.status_combo.setCurrentText("published")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_not_called()

    def test_draft_only_requires_title(self, dialog):
        dialog.title_edit.setText("Idea para un episodio")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_not_called()

    def test_published_lists_title_content_and_audio(self, dialog):
        dialog.status_combo.setCurrentText("published")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            call_args = str(mock_warn.call_args)
            assert "Título" in call_args
            assert "Contenido" in call_args
            assert "Audio" in call_args

    def test_remote_audio_requires_positive_size(self, dialog):
        dialog.title_edit.setText("Título")
        dialog.content_edit.setPlainText("Contenido")
        dialog.audio_url_edit.setText("https://example.com/audio.mp3")
        dialog.status_combo.setCurrentText("published")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            assert "Tamaño" in str(mock_warn.call_args)


class TestRemoteAudioMetadata:
    def test_probe_fills_size_and_mime(self, dialog):
        response = MagicMock()
        response.status_code = 200
        response.headers = {
            "Content-Length": "5000000",
            "Content-Type": "audio/ogg; charset=binary",
        }
        dialog.audio_url_edit.setText("https://example.com/audio.ogg")

        with patch("ui.episode_dialog.requests.head", return_value=response):
            dialog._probe_remote_audio()

        assert dialog.audio_size_edit.text() == "5000000"
        assert dialog.audio_mime_edit.text() == "audio/ogg"
        response.close.assert_called_once()

    def test_probe_falls_back_to_streamed_get_without_length(self, dialog):
        head_response = MagicMock()
        head_response.status_code = 200
        head_response.headers = {}
        get_response = MagicMock()
        get_response.headers = {
            "Content-Length": "42",
            "Content-Type": "audio/mpeg",
        }
        dialog.audio_url_edit.setText("https://example.com/audio.mp3")

        with (
            patch("ui.episode_dialog.requests.head", return_value=head_response),
            patch("ui.episode_dialog.requests.get", return_value=get_response) as get,
        ):
            dialog._probe_remote_audio()

        get.assert_called_once_with(
            "https://example.com/audio.mp3",
            allow_redirects=True,
            timeout=10,
            stream=True,
        )
        assert dialog.audio_size_edit.text() == "42"


# ---------------------------------------------------------------------------
# Población de campos — _populate
# ---------------------------------------------------------------------------

class TestEpisodeDialogPopulate:
    def test_title_populated(self, edit_dialog):
        assert edit_dialog.title_edit.text() == "Ep 1"

    def test_description_populated(self, edit_dialog):
        assert edit_dialog.description_edit.toPlainText() == "Test description"

    def test_content_populated(self, edit_dialog):
        assert edit_dialog.content_edit.toPlainText() == "Long content"

    def test_duration_populated(self, edit_dialog):
        assert edit_dialog.duration_edit.text() == "00:30:00"

    def test_audio_size_populated(self, edit_dialog):
        assert edit_dialog.audio_size_edit.text() == "5000000"

    def test_audio_mime_populated(self, edit_dialog):
        assert edit_dialog.audio_mime_edit.text() == "audio/mpeg"

    def test_season_populated(self, edit_dialog):
        assert edit_dialog.season_edit.text() == "2"

    def test_episode_number_populated(self, edit_dialog):
        assert edit_dialog.episode_num_edit.text() == "5"

    def test_status_published(self, edit_dialog):
        assert edit_dialog.status_combo.currentText() == "published"

    def test_episode_type_full(self, edit_dialog):
        assert edit_dialog.episode_type_combo.currentText() == "full"

    def test_window_title_edit(self, edit_dialog):
        assert "Editar episodio" in edit_dialog.windowTitle()

    def test_pub_date_populated_from_published_at(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        ep = {"title": "X", "description": "Y", "published_at": "2024-06-01"}
        dlg = EpisodeDialog(episode=ep)
        assert "2024-06-01" in dlg.published_at_edit.text()

    def test_pub_date_populated_from_pub_date_key(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        ep = {"title": "X", "description": "Y", "pub_date": "2024-07-15"}
        dlg = EpisodeDialog(episode=ep)
        assert "2024-07-15" in dlg.published_at_edit.text()

    def test_episode_type_trailer(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        ep = {"title": "X", "episode_type": "trailer"}
        dlg = EpisodeDialog(episode=ep)
        assert dlg.episode_type_combo.currentText() == "trailer"


# ---------------------------------------------------------------------------
# get_data
# ---------------------------------------------------------------------------

class TestEpisodeGetData:
    def test_returns_title(self, edit_dialog):
        assert edit_dialog.get_data()["title"] == "Ep 1"

    def test_season_number_as_int(self, edit_dialog):
        data = edit_dialog.get_data()
        assert data["season_number"] == 2
        assert isinstance(data["season_number"], int)

    def test_episode_number_as_int(self, edit_dialog):
        data = edit_dialog.get_data()
        assert data["episode_number"] == 5
        assert isinstance(data["episode_number"], int)

    def test_no_empty_strings_in_result(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.description_edit.setPlainText("Desc")
        dialog.audio_url_edit.setText("https://example.com/a.mp3")
        data = dialog.get_data()
        for v in data.values():
            assert v != ""

    def test_non_digit_season_excluded(self, dialog):
        dialog.season_edit.setText("abc")
        assert "season_number" not in dialog.get_data()

    def test_non_digit_episode_number_excluded(self, dialog):
        dialog.episode_num_edit.setText("--")
        assert "episode_number" not in dialog.get_data()

    def test_status_included(self, edit_dialog):
        assert edit_dialog.get_data()["status"] == "published"

    def test_episode_type_included(self, edit_dialog):
        assert edit_dialog.get_data()["episode_type"] == "full"

    def test_audio_url_included(self, edit_dialog):
        assert "audio_url" in edit_dialog.get_data()

    def test_audio_size_included_as_int(self, edit_dialog):
        assert edit_dialog.get_data()["audio_size_bytes"] == 5_000_000

    def test_audio_mime_included(self, edit_dialog):
        assert edit_dialog.get_data()["audio_mime_type"] == "audio/mpeg"

    def test_pub_date_key_in_get_data(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        ep = {**FULL_EPISODE, "pub_date": "2024-01-15 10:00:00"}
        dlg = EpisodeDialog(episode=ep)
        assert "pub_date" in dlg.get_data()
        assert "published_at" not in dlg.get_data()


# ---------------------------------------------------------------------------
# Estado scheduled
# ---------------------------------------------------------------------------

class TestScheduledEpisode:
    def test_scheduled_in_status_options(self, dialog):
        items = [dialog.status_combo.itemText(i) for i in range(dialog.status_combo.count())]
        assert "scheduled" in items

    def test_label_changes_when_scheduled(self, dialog):
        dialog.status_combo.setCurrentText("scheduled")
        assert "*" in dialog.pub_date_label.text()

    def test_label_restored_when_not_scheduled(self, dialog):
        dialog.status_combo.setCurrentText("scheduled")
        dialog.status_combo.setCurrentText("draft")
        assert "*" not in dialog.pub_date_label.text()

    def test_warning_when_scheduled_without_pub_date(self, dialog):
        dialog.title_edit.setText("Título")
        dialog.content_edit.setPlainText("Contenido")
        dialog.audio_url_edit.setText("https://example.com/a.mp3")
        dialog.audio_size_edit.setText("1000")
        dialog.status_combo.setCurrentText("scheduled")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_called_once()
            assert "programada" in str(mock_warn.call_args).lower()

    def test_no_warning_when_scheduled_with_pub_date(self, dialog):
        dialog.title_edit.setText("Título")
        dialog.content_edit.setPlainText("Contenido")
        dialog.audio_url_edit.setText("https://example.com/a.mp3")
        dialog.audio_size_edit.setText("1000")
        dialog.status_combo.setCurrentText("scheduled")
        dialog.published_at_edit.setText("2025-06-01T10:00:00")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_not_called()

    def test_scheduled_episode_populates_status(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        ep = {"title": "X", "content": "Y", "status": "scheduled", "pub_date": "2025-06-01T10:00:00"}
        dlg = EpisodeDialog(episode=ep)
        assert dlg.status_combo.currentText() == "scheduled"
        assert "2025-06-01" in dlg.published_at_edit.text()


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

class TestEpisodeDialogDefaults:
    def test_season_default_applied(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        dlg = EpisodeDialog(defaults={"season_number": 3, "episode_number": 7})
        assert dlg.season_edit.text() == "3"

    def test_episode_number_default_applied(self, qapp):
        from ui.episode_dialog import EpisodeDialog
        dlg = EpisodeDialog(defaults={"season_number": 3, "episode_number": 7})
        assert dlg.episode_num_edit.text() == "7"

    def test_defaults_ignored_when_episode_provided(self, qapp):
        """Si se pasa episode, los defaults no deben aplicarse."""
        from ui.episode_dialog import EpisodeDialog
        ep = {"title": "X", "season_number": 1, "episode_number": 1}
        dlg = EpisodeDialog(episode=ep, defaults={"season_number": 99})
        assert dlg.season_edit.text() == "1"
