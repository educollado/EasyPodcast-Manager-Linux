"""Tests para PageDialog — validación, población de campos y get_data."""
import pytest
from unittest.mock import patch


FULL_PAGE = {
    "id": 7,
    "title": "About",
    "slug": "about",
    "content": "Content here",
    "status": "published",
    "parent_id": 3,
    "sort_order": 2,
    "full_path": "about",
}


@pytest.fixture
def dialog(qapp):
    from ui.page_dialog import PageDialog
    return PageDialog()


@pytest.fixture
def edit_dialog(qapp):
    from ui.page_dialog import PageDialog
    return PageDialog(page=FULL_PAGE)


# ---------------------------------------------------------------------------
# Diálogo nuevo
# ---------------------------------------------------------------------------

class TestNewPageDialog:
    def test_window_title(self, dialog):
        assert "Nueva página" in dialog.windowTitle()

    def test_title_empty(self, dialog):
        assert dialog.title_edit.text() == ""

    def test_slug_empty(self, dialog):
        assert dialog.slug_edit.text() == ""

    def test_content_empty(self, dialog):
        assert dialog.content_edit.toPlainText() == ""

    def test_default_status_is_draft(self, dialog):
        assert dialog.status_combo.currentText() == "draft"

    def test_sort_order_empty(self, dialog):
        assert dialog.sort_order_edit.text() == ""

    def test_parent_id_empty(self, dialog):
        assert dialog.parent_id_edit.text() == ""


# ---------------------------------------------------------------------------
# Población de campos — _populate
# ---------------------------------------------------------------------------

class TestPageDialogPopulate:
    def test_title_populated(self, edit_dialog):
        assert edit_dialog.title_edit.text() == "About"

    def test_slug_populated(self, edit_dialog):
        assert edit_dialog.slug_edit.text() == "about"

    def test_content_populated(self, edit_dialog):
        assert edit_dialog.content_edit.toPlainText() == "Content here"

    def test_status_published(self, edit_dialog):
        assert edit_dialog.status_combo.currentText() == "published"

    def test_sort_order_populated(self, edit_dialog):
        assert edit_dialog.sort_order_edit.text() == "2"

    def test_parent_id_populated(self, edit_dialog):
        assert edit_dialog.parent_id_edit.text() == "3"

    def test_window_title_edit(self, edit_dialog):
        assert "Editar página" in edit_dialog.windowTitle()

    def test_status_draft_populated(self, qapp):
        from ui.page_dialog import PageDialog
        dlg = PageDialog(page={"title": "X", "status": "draft"})
        assert dlg.status_combo.currentText() == "draft"

    def test_sort_order_zero(self, qapp):
        from ui.page_dialog import PageDialog
        dlg = PageDialog(page={"title": "X", "sort_order": 0})
        assert dlg.sort_order_edit.text() == "0"


# ---------------------------------------------------------------------------
# get_data
# ---------------------------------------------------------------------------

class TestPageGetData:
    def test_title_included(self, edit_dialog):
        assert edit_dialog.get_data()["title"] == "About"

    def test_slug_included(self, edit_dialog):
        assert edit_dialog.get_data()["slug"] == "about"

    def test_content_included(self, edit_dialog):
        assert edit_dialog.get_data()["content"] == "Content here"

    def test_status_included(self, edit_dialog):
        assert edit_dialog.get_data()["status"] == "published"

    def test_sort_order_as_int(self, edit_dialog):
        data = edit_dialog.get_data()
        assert data["sort_order"] == 2
        assert isinstance(data["sort_order"], int)

    def test_parent_id_as_int(self, edit_dialog):
        assert edit_dialog.get_data()["parent_id"] == 3

    def test_current_full_path_preserved_when_editing(self, edit_dialog):
        assert edit_dialog.get_data()["current_full_path"] == "about"

    def test_no_empty_strings_in_result(self, dialog):
        dialog.title_edit.setText("Test")
        for v in dialog.get_data().values():
            assert v != ""

    def test_non_numeric_sort_order_excluded(self, dialog):
        dialog.title_edit.setText("Test")
        dialog.sort_order_edit.setText("abc")
        assert "sort_order" not in dialog.get_data()

    def test_negative_sort_order_included(self, qapp):
        from ui.page_dialog import PageDialog
        page = {"title": "Footer", "sort_order": -1}
        dlg = PageDialog(page=page)
        data = dlg.get_data()
        assert data["sort_order"] == -1

    def test_empty_slug_excluded(self, dialog):
        dialog.title_edit.setText("Title")
        # slug is empty by default
        data = dialog.get_data()
        assert "slug" not in data or data.get("slug") != ""

    def test_status_always_included(self, dialog):
        """status tiene un combo con valor por defecto, nunca debería faltar."""
        dialog.title_edit.setText("X")
        assert "status" in dialog.get_data()

    def test_positive_sort_order(self, dialog):
        dialog.title_edit.setText("Home")
        dialog.sort_order_edit.setText("10")
        assert dialog.get_data()["sort_order"] == 10

    def test_invalid_parent_id_excluded(self, dialog):
        dialog.parent_id_edit.setText("-1")
        assert "parent_id" not in dialog.get_data()

    def test_parent_can_be_cleared_when_editing(self, edit_dialog):
        edit_dialog.parent_id_edit.clear()
        assert edit_dialog.get_data()["parent_id"] is None


class TestPageValidation:
    def test_title_and_slug_are_required(self, dialog):
        with patch("PySide6.QtWidgets.QMessageBox.warning") as warning:
            dialog._on_accept()
        message = str(warning.call_args)
        assert "Título" in message
        assert "Slug" in message

    def test_valid_page_is_accepted(self, dialog):
        dialog.title_edit.setText("Acerca de")
        dialog.slug_edit.setText("acerca-de")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as warning:
            dialog._on_accept()
        warning.assert_not_called()
        assert dialog.result() == dialog.DialogCode.Accepted

    def test_slug_format_is_validated(self, dialog):
        dialog.title_edit.setText("Acerca de")
        dialog.slug_edit.setText("Acerca De")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as warning:
            dialog._on_accept()
        assert "minúsculas" in str(warning.call_args)

    def test_parent_id_must_be_positive_integer(self, dialog):
        dialog.title_edit.setText("Acerca de")
        dialog.slug_edit.setText("acerca-de")
        dialog.parent_id_edit.setText("-3")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as warning:
            dialog._on_accept()
        assert "numérico positivo" in str(warning.call_args)

    def test_page_cannot_be_its_own_parent(self, edit_dialog):
        edit_dialog.parent_id_edit.setText("7")
        with patch("PySide6.QtWidgets.QMessageBox.warning") as warning:
            edit_dialog._on_accept()
        assert "propia página padre" in str(warning.call_args)
