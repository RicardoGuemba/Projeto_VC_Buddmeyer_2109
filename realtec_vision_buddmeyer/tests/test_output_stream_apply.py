# -*- coding: utf-8 -*-
"""Testes unitários de apply_output_stream_settings (hot-apply MJPEG)."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.pages.operation_page import OperationPage


@pytest.fixture
def operation_page(qtbot):
    page = OperationPage()
    qtbot.addWidget(page)
    return page


class TestApplyOutputStreamSettings:
    """apply_output_stream_settings liga stream mesmo sem Operação ▶ Iniciar."""

    def test_not_running_enabled_starts_server(self, operation_page):
        operation_page._is_running = False
        operation_page._mjpeg_server = None
        operation_page._settings.output.rtsp_enabled = True
        operation_page._settings.output.http_port = 19999
        operation_page._settings.output.http_path = "/stream"

        mock_instance = MagicMock()
        mock_instance.start.return_value = True
        mock_instance.verify_listening.return_value = True
        mock_instance.get_stream_urls.return_value = (
            "http://127.0.0.1:19999/stream",
            "http://192.168.0.1:19999/stream",
        )
        mock_instance.port = 19999
        mock_instance.path = "/stream"

        with patch(
            "ui.pages.operation_page.MjpegServer", return_value=mock_instance
        ) as ctor:
            operation_page.apply_output_stream_settings()

        ctor.assert_called_once()
        assert operation_page._mjpeg_server is mock_instance

    def test_not_running_disabled_stops_server(self, operation_page):
        mock_srv = MagicMock()
        operation_page._is_running = False
        operation_page._mjpeg_server = mock_srv
        operation_page._settings.output.rtsp_enabled = False

        operation_page.apply_output_stream_settings()

        mock_srv.stop.assert_called_once()
        assert operation_page._mjpeg_server is None

    def test_running_disabled_stops_server(self, operation_page):
        mock_srv = MagicMock()
        operation_page._is_running = True
        operation_page._mjpeg_server = mock_srv
        operation_page._settings.output.rtsp_enabled = False

        operation_page.apply_output_stream_settings()

        mock_srv.stop.assert_called_once()
        assert operation_page._mjpeg_server is None

    def test_running_enabled_starts_server(self, operation_page):
        operation_page._is_running = True
        operation_page._mjpeg_server = None
        operation_page._settings.output.rtsp_enabled = True
        operation_page._settings.output.http_port = 19999
        operation_page._settings.output.http_path = "/stream"

        mock_instance = MagicMock()
        mock_instance.start.return_value = True
        mock_instance.verify_listening.return_value = True
        mock_instance.get_stream_urls.return_value = (
            "http://127.0.0.1:19999/stream",
            "http://192.168.0.1:19999/stream",
        )
        mock_instance.port = 19999
        mock_instance.path = "/stream"

        with patch(
            "ui.pages.operation_page.MjpegServer", return_value=mock_instance
        ) as ctor:
            operation_page.apply_output_stream_settings()

        ctor.assert_called_once()
        assert operation_page._mjpeg_server is mock_instance

    def test_running_port_change_restarts(self, operation_page):
        old = MagicMock()
        old.port = 19999
        old.path = "/stream"
        operation_page._is_running = True
        operation_page._mjpeg_server = old
        operation_page._settings.output.rtsp_enabled = True
        operation_page._settings.output.http_port = 20000
        operation_page._settings.output.http_path = "/stream"

        new = MagicMock()
        new.start.return_value = True
        new.verify_listening.return_value = True
        new.get_stream_urls.return_value = (
            "http://127.0.0.1:20000/stream",
            "http://192.168.0.1:20000/stream",
        )
        new.port = 20000
        new.path = "/stream"

        with patch("ui.pages.operation_page.MjpegServer", return_value=new):
            operation_page.apply_output_stream_settings()

        old.stop.assert_called_once()
        new.start.assert_called_once()
        assert operation_page._mjpeg_server is new

    def test_restore_output_stream_if_configured(self, operation_page):
        operation_page._settings.output.rtsp_enabled = True
        operation_page._settings.output.http_port = 19990
        operation_page._settings.output.http_path = "/stream"

        mock_instance = MagicMock()
        mock_instance.start.return_value = True
        mock_instance.verify_listening.return_value = True
        mock_instance.get_stream_urls.return_value = (
            "http://127.0.0.1:19990/stream",
            "http://192.168.0.1:19990/stream",
        )
        mock_instance.port = 19990
        mock_instance.path = "/stream"

        with patch(
            "ui.pages.operation_page.MjpegServer", return_value=mock_instance
        ):
            operation_page.restore_output_stream_if_configured()

        assert operation_page._mjpeg_server is mock_instance

    def test_restore_skipped_when_disabled(self, operation_page):
        operation_page._settings.output.rtsp_enabled = False
        with patch("ui.pages.operation_page.MjpegServer") as ctor:
            operation_page.restore_output_stream_if_configured()
        ctor.assert_not_called()

    def test_running_same_settings_no_restart(self, operation_page):
        srv = MagicMock()
        srv.port = 19999
        srv.path = "/stream"
        operation_page._is_running = True
        operation_page._mjpeg_server = srv
        operation_page._settings.output.rtsp_enabled = True
        operation_page._settings.output.http_port = 19999
        operation_page._settings.output.http_path = "/stream"

        with patch("ui.pages.operation_page.MjpegServer") as ctor:
            operation_page.apply_output_stream_settings()

        ctor.assert_not_called()
        srv.stop.assert_not_called()
        assert operation_page._mjpeg_server is srv
