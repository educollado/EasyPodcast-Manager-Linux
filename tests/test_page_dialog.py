"""Tests para PageDialog — validación, población de campos y get_data."""
import pytest


FULL_PAGE = {
    "title": "About",
    "slug": "about",
    "content": "Content here",
    "status": "published",
    "menu_order": 2,
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

    def test_menu_order_empty(self, dialog):
        assert dialog.menu_order_edit.text() == ""


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

    def test_menu_order_populated(self, edit_dialog):
        assert edit_dialog.menu_order_edit.text() == "2"

    def test_window_title_edit(self, edit_dialog):
        assert "Editar página" in edit_dialog.windowTitle()

    def test_status_draft_populated(self, qapp):
        from ui.page_dialog import PageDialog
        dlg = PageDialog(page={"title": "X", "status": "draft"})
        assert dlg.status_combo.currentText() == "draft"

    def test_menu_order_zero(self, qapp):
        from ui.page_dialog import PageDialog
        dlg = PageDialog(page={"title": "X", "menu_order": 0})
        assert dlg.menu_order_edit.text() == ""  # 0 is falsy → stored as "" via `or ""`


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

    def test_menu_order_as_int(self, edit_dialog):
        data = edit_dialog.get_data()
        assert data["menu_order"] == 2
        assert isinstance(data["menu_order"], int)

    def test_no_empty_strings_in_result(self, dialog):
        dialog.title_edit.setText("Test")
        for v in dialog.get_data().values():
            assert v != ""

    def test_non_numeric_menu_order_excluded(self, dialog):
        dialog.title_edit.setText("Test")
        dialog.menu_order_edit.setText("abc")
        assert "menu_order" not in dialog.get_data()

    def test_negative_menu_order_included(self, qapp):
        from ui.page_dialog import PageDialog
        page = {"title": "Footer", "menu_order": -1}
        dlg = PageDialog(page=page)
        data = dlg.get_data()
        assert data["menu_order"] == -1

    def test_empty_slug_excluded(self, dialog):
        dialog.title_edit.setText("Title")
        # slug is empty by default
        data = dialog.get_data()
        assert "slug" not in data or data.get("slug") != ""

    def test_status_always_included(self, dialog):
        """status tiene un combo con valor por defecto, nunca debería faltar."""
        dialog.title_edit.setText("X")
        assert "status" in dialog.get_data()

    def test_positive_menu_order(self, dialog):
        dialog.title_edit.setText("Home")
        dialog.menu_order_edit.setText("10")
        assert dialog.get_data()["menu_order"] == 10
