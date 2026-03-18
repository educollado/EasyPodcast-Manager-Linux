"""Tests para EpisodeDialog — validación, población de campos y get_data."""
import pytest
from unittest.mock import patch


FULL_EPISODE = {
    "title": "Ep 1",
    "slug": "ep-1",
    "description": "Test description",
    "content": "Long content",
    "audio_url": "https://example.com/audio.mp3",
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

    def test_slug_field_empty(self, dialog):
        assert dialog.slug_edit.text() == ""

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


# ---------------------------------------------------------------------------
# Validación — _on_accept
# ---------------------------------------------------------------------------

class TestEpisodeValidation:
    def _fill_valid(self, dialog):
        dialog.title_edit.setText("Título válido")
        dialog.description_edit.setPlainText("Descripción válida")
        dialog.audio_url_edit.setText("https://example.com/audio.mp3")

    def test_warning_when_title_empty(self, dialog):
        dialog.description_edit.setPlainText("desc")
        dialog.audio_url_edit.setText("https://x.com/a.mp3")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_called_once()

    def test_warning_when_description_empty(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.audio_url_edit.setText("https://x.com/a.mp3")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_called_once()

    def test_warning_when_no_audio(self, dialog):
        dialog.title_edit.setText("Title")
        dialog.description_edit.setPlainText("Desc")
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
        dialog.description_edit.setPlainText("Desc")
        dialog._audio_path = "/tmp/audio.mp3"
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            mock_warn.assert_not_called()

    def test_all_three_fields_missing_listed(self, dialog):
        """Si faltan los tres campos, el mensaje los menciona."""
        with patch("PySide6.QtWidgets.QMessageBox.warning") as mock_warn:
            dialog._on_accept()
            call_args = str(mock_warn.call_args)
            assert "Título" in call_args
            assert "Descripción" in call_args
            assert "Audio" in call_args


# ---------------------------------------------------------------------------
# Población de campos — _populate
# ---------------------------------------------------------------------------

class TestEpisodeDialogPopulate:
    def test_title_populated(self, edit_dialog):
        assert edit_dialog.title_edit.text() == "Ep 1"

    def test_slug_populated(self, edit_dialog):
        assert edit_dialog.slug_edit.text() == "ep-1"

    def test_description_populated(self, edit_dialog):
        assert edit_dialog.description_edit.toPlainText() == "Test description"

    def test_content_populated(self, edit_dialog):
        assert edit_dialog.content_edit.toPlainText() == "Long content"

    def test_duration_populated(self, edit_dialog):
        assert edit_dialog.duration_edit.text() == "00:30:00"

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

    def test_returns_slug(self, edit_dialog):
        assert edit_dialog.get_data()["slug"] == "ep-1"

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
