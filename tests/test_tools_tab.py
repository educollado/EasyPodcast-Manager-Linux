"""Tests para ToolsTab — formateo de valores y renderizado de estadísticas."""
import pytest
from unittest.mock import MagicMock, patch


@pytest.fixture
def tab(qapp):
    from ui.tools_tab import ToolsTab
    return ToolsTab(MagicMock())


# ---------------------------------------------------------------------------
# _fmt_value
# ---------------------------------------------------------------------------

class TestFmtValue:
    def test_bool_true(self, tab):
        assert tab._fmt_value("x", True) == "Sí"

    def test_bool_false(self, tab):
        assert tab._fmt_value("x", False) == "No"

    def test_bytes_b(self, tab):
        assert tab._fmt_value("size_bytes", 512) == "512.0 B"

    def test_bytes_kb(self, tab):
        assert tab._fmt_value("size_bytes", 2048) == "2.0 KB"

    def test_bytes_mb(self, tab):
        assert tab._fmt_value("size_bytes", 1024 * 1024) == "1.0 MB"

    def test_bytes_gb(self, tab):
        assert tab._fmt_value("size_bytes", 1024 ** 3) == "1.0 GB"

    def test_bytes_tb(self, tab):
        result = tab._fmt_value("size_bytes", 1024 ** 4)
        assert "TB" in result

    def test_int_with_thousands_separator(self, tab):
        # Spanish locale: 1000 -> "1.000"
        result = tab._fmt_value("count", 1000)
        assert result == "1.000"

    def test_float_formatted(self, tab):
        result = tab._fmt_value("ratio", 3.5)
        assert "3" in result

    def test_string_passthrough(self, tab):
        assert tab._fmt_value("title", "Hello world") == "Hello world"

    def test_non_bytes_int_not_converted(self, tab):
        # 2048 without _bytes suffix → integer format, NOT "2.0 KB"
        result = tab._fmt_value("total", 2048)
        assert "KB" not in result

    def test_bool_takes_priority_over_int(self, tab):
        # True is an int in Python, must be handled as bool first
        assert tab._fmt_value("flag", True) == "Sí"
        assert tab._fmt_value("flag", False) == "No"


# ---------------------------------------------------------------------------
# _show_stats — entradas inválidas
# ---------------------------------------------------------------------------

class TestShowStatsInvalidInput:
    def test_none_shows_sin_datos(self, tab):
        tab._show_stats(None)
        assert "Sin datos" in tab.output.toHtml()

    def test_empty_dict_shows_sin_datos(self, tab):
        tab._show_stats({})
        assert "Sin datos" in tab.output.toHtml()

    def test_non_dict_shows_sin_datos(self, tab):
        tab._show_stats([1, 2, 3])
        assert "Sin datos" in tab.output.toHtml()


# ---------------------------------------------------------------------------
# _show_stats — sección episodios
# ---------------------------------------------------------------------------

class TestShowStatsEpisodes:
    def _ep_data(self, **overrides):
        base = {
            "episodes": {
                "published": 10,
                "drafts": 2,
                "total": 12,
                "last_title": "Episodio final",
                "last_pub_date": "2024-01-15",
                "audio_size_bytes": 123456789,
            }
        }
        base["episodes"].update(overrides)
        return base

    def test_published_count_shown(self, tab):
        tab._show_stats(self._ep_data())
        assert "10" in tab.output.toHtml()

    def test_total_count_shown(self, tab):
        tab._show_stats(self._ep_data())
        assert "12" in tab.output.toHtml()

    def test_last_title_shown(self, tab):
        tab._show_stats(self._ep_data())
        assert "Episodio final" in tab.output.toHtml()

    def test_last_pub_date_shown(self, tab):
        tab._show_stats(self._ep_data())
        assert "2024-01-15" in tab.output.toHtml()

    def test_audio_size_shown_in_mb(self, tab):
        tab._show_stats(self._ep_data(audio_size_bytes=1024 * 1024))
        assert "MB" in tab.output.toHtml()

    def test_no_last_title_does_not_crash(self, tab):
        data = {"episodes": {"published": 3, "drafts": 0, "total": 3}}
        tab._show_stats(data)
        assert "3" in tab.output.toHtml()

    def test_section_header_shown(self, tab):
        tab._show_stats(self._ep_data())
        assert "Episodios" in tab.output.toHtml()


# ---------------------------------------------------------------------------
# _show_stats — sección caché
# ---------------------------------------------------------------------------

class TestShowStatsCache:
    def test_cache_enabled_shows_activa(self, tab):
        tab._show_stats({"cache": {"enabled": True, "files": 10, "size_bytes": 1024}})
        assert "Activa" in tab.output.toHtml()

    def test_cache_disabled_shows_inactiva(self, tab):
        tab._show_stats({"cache": {"enabled": False, "files": 0, "size_bytes": 0}})
        assert "Inactiva" in tab.output.toHtml()

    def test_files_count_shown(self, tab):
        tab._show_stats({"cache": {"enabled": True, "files": 45, "size_bytes": 0}})
        assert "45" in tab.output.toHtml()

    def test_cache_size_shown(self, tab):
        tab._show_stats({"cache": {"enabled": True, "files": 5, "size_bytes": 2048}})
        assert "KB" in tab.output.toHtml()

    def test_section_header_shown(self, tab):
        tab._show_stats({"cache": {"enabled": True, "files": 0, "size_bytes": 0}})
        assert "Caché" in tab.output.toHtml()


# ---------------------------------------------------------------------------
# _show_stats — respuesta completa (episodios + caché)
# ---------------------------------------------------------------------------

class TestShowStatsFull:
    FULL_DATA = {
        "episodes": {
            "published": 5,
            "drafts": 1,
            "total": 6,
            "last_title": "Último episodio",
            "last_pub_date": "2025-01-01",
            "audio_size_bytes": 500_000,
        },
        "cache": {
            "enabled": True,
            "files": 10,
            "size_bytes": 20_000,
        },
    }

    def test_both_sections_rendered(self, tab):
        tab._show_stats(self.FULL_DATA)
        html = tab.output.toHtml()
        assert "Episodios" in html
        assert "Caché" in html

    def test_episode_and_cache_data_coexist(self, tab):
        tab._show_stats(self.FULL_DATA)
        html = tab.output.toHtml()
        assert "6" in html       # total episodios
        assert "Activa" in html  # caché habilitada


# ---------------------------------------------------------------------------
# _show_stats — descargas y reproducciones de EasyPodcast 1.8.11+
# ---------------------------------------------------------------------------

class TestShowStatsDownloads:
    DATA = {
        "downloads": {
            "daily": {
                "items": [
                    {"action_type": "download"},
                    {"action_type": "download"},
                    {"action_type": "play"},
                ],
                "total": 3,
            },
            "summary": {
                "items": [
                    {"episode_title": "Uno", "total_downloads": 7},
                    {"episode_title": "Dos", "total_downloads": 5},
                ],
                "total": 2,
            },
        }
    }

    def test_downloads_section_rendered(self, tab):
        tab._show_stats(self.DATA)
        assert "Descargas y reproducciones" in tab.output.toHtml()

    def test_event_counts_rendered(self, tab):
        tab._show_stats(self.DATA)
        html = tab.output.toHtml()
        assert "Eventos registrados" in html
        assert "Reproducciones recientes" in html

    def test_accumulated_downloads_rendered(self, tab):
        tab._show_stats(self.DATA)
        html = tab.output.toHtml()
        assert "Descargas acumuladas" in html
        assert "12" in html


# ---------------------------------------------------------------------------
# _show_stats — fallback para diccionarios planos
# ---------------------------------------------------------------------------

class TestShowStatsFallback:
    def test_flat_string_value_shown(self, tab):
        tab._show_stats({"version": "1.0.0"})
        assert "1.0.0" in tab.output.toHtml()

    def test_flat_int_value_shown(self, tab):
        tab._show_stats({"uptime": 3600})
        assert "3.600" in tab.output.toHtml()

    def test_unknown_keys_capitalized(self, tab):
        tab._show_stats({"my_custom_key": "hello"})
        html = tab.output.toHtml()
        assert "hello" in html


class TestServerUpdate:
    def test_admin_scope_message_on_403(self, tab):
        from api import APIError
        from PySide6.QtWidgets import QMessageBox

        tab.api.system_update.side_effect = APIError(
            "HTTP 403: Alcance insuficiente", status_code=403
        )
        with (
            patch(
                "PySide6.QtWidgets.QMessageBox.warning",
                return_value=QMessageBox.StandardButton.Yes,
            ),
            patch("PySide6.QtWidgets.QMessageBox.critical") as critical,
        ):
            tab._on_do_update()

        assert "admin" in str(critical.call_args)
