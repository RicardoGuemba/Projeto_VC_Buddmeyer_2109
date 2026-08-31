# -*- coding: utf-8 -*-
"""Testes de shutdown estável do sistema."""

import sys
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestShutdownStability:
    """Testes de estabilidade ao parar e sair."""

    def test_stop_system_idempotent(self, qtbot):
        """Chamar _stop_system duas vezes não causa erro."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._stop_system()
        page._stop_system()
        assert not page._is_running

    def test_stop_system_when_not_running(self, qtbot):
        """_stop_system quando não está rodando retorna imediatamente."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        assert not page._is_running
        page._stop_system()
        assert not page._is_running

    def test_handlers_ignore_when_not_running(self, qtbot):
        """Handlers retornam cedo quando _is_running é False."""
        from datetime import datetime

        from detection.events import DetectionEvent
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._is_running = False

        page._on_cycle_summary([])
        page._on_cycle_summary([{"step": "x", "timestamp": datetime.now()}])
        page._on_cycle_step("test")

        evt = DetectionEvent(
            detected=True,
            class_name="test",
            confidence=0.9,
            centroid=(0.0, 0.0),
            detection_count=1,
        )
        page._on_detection(evt)

        assert not page._is_running

    def test_main_window_close_without_running(self, qtbot):
        """MainWindow inicia shutdown unificado ao fechar sem sistema rodando."""
        from ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitExposed(window)
        window.close()
        assert window._exit_in_progress
        qtbot.wait(250)
        window._complete_exit()
        assert window.isHidden() or not window.isVisible()

    def test_shutdown_cancels_model_loading(self, qtbot):
        """shutdown() limpa estado de carregamento do modelo sem QThread pendente."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._model_loading = True
        page._pending_start_source_label = "USB"
        page.shutdown()
        assert not page._model_loading
        assert page._pending_start_source_label is None

    def test_shutdown_stops_cip_timers(self, qtbot):
        """shutdown() chama shutdown_for_exit no cliente CIP."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._cip_client._start_heartbeat()
        assert page._cip_client._heartbeat_timer is not None
        page.shutdown()
        assert page._cip_client._heartbeat_timer is None

    def test_main_window_begin_exit_idempotent(self, qtbot):
        """_begin_exit pode ser chamado uma vez sem erro."""
        from ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        window.show()
        qtbot.waitExposed(window)
        window._begin_exit()
        assert window._exit_in_progress
        window._begin_exit()
        assert window._exit_in_progress

    def test_is_busy_for_exit_model_loading(self, qtbot):
        """Carregamento de modelo exige confirmação de saída."""
        from ui.main_window import MainWindow

        window = MainWindow()
        qtbot.addWidget(window)
        window._operation_page._model_loading = True
        assert window._is_busy_for_exit()

    def test_diagnostics_stop_timers(self, qtbot):
        """DiagnosticsPage para timer de atualização."""
        from ui.pages.diagnostics_page import DiagnosticsPage

        page = DiagnosticsPage()
        qtbot.addWidget(page)
        assert page._update_timer.isActive()
        page.stop_timers()
        assert not page._update_timer.isActive()

    def test_model_load_skipped_after_shutdown(self, qtbot):
        """Carregamento do modelo não continua após shutdown."""
        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._model_loading = True
        page.shutdown()
        page._run_model_load_on_main_thread()
        assert not page._model_loading

    def test_shutdown_while_running_skips_async_plc_and_stream_restart(self, qtbot):
        """Saída com sistema activo não agenda disconnect CIP nem recovery de stream."""
        from unittest.mock import patch

        from ui.pages.operation_page import OperationPage

        page = OperationPage()
        qtbot.addWidget(page)
        page._is_running = True
        page._stream_manager._is_running = True
        page._inference_engine._is_running = False

        with patch.object(page._stream_manager, "stop") as stop_stream, \
             patch.object(page._inference_engine, "stop") as stop_inf, \
             patch.object(page, "_run_shutdown_plc_sync") as plc_sync, \
             patch.object(page._stream_manager, "start") as start_stream:
            page.shutdown()
            stop_stream.assert_called()
            stop_inf.assert_called()
            plc_sync.assert_not_called()
            start_stream.assert_not_called()

        assert page._shutdown_requested
        assert page._stream_manager._shutting_down
        assert page._cip_client._exiting
        page._stream_manager.clear_shutdown_guard()
        page._cip_client._exiting = False

    def test_prepare_shutdown_blocks_stream_start_and_recovery(self):
        from unittest.mock import patch

        from streaming.stream_health import HealthStatus, StreamHealthInfo
        from streaming.stream_manager import StreamManager

        mgr = StreamManager()
        mgr.clear_shutdown_guard()
        mgr._is_running = True
        mgr._settings.reliability.stream_auto_restart = True
        mgr._settings.streaming.unhealthy_restart_after_s = 0.01
        mgr.prepare_shutdown()

        info = StreamHealthInfo(
            status=HealthStatus.UNHEALTHY,
            fps=0.0,
            expected_fps=30.0,
            frame_drops=99,
            last_frame_time=None,
            latency_ms=0.0,
            buffer_usage=0.0,
            message="unhealthy",
        )
        with patch.object(mgr, "stop") as stop_mock, patch.object(mgr, "start") as start_mock:
            mgr._unhealthy_since = __import__("time").time() - 1.0
            mgr._on_health_changed(info)
            stop_mock.assert_not_called()
            start_mock.assert_not_called()

        assert mgr.start() is False
        mgr.clear_shutdown_guard()
        mgr._is_running = False

    def test_power_guard_release_idempotent(self):
        from core.power_guard import PowerGuard

        guard = PowerGuard()
        guard.release()
        guard.release()
        assert guard.is_active is False

    def test_cip_shutdown_for_exit_blocks_reconnect(self):
        from communication.cip_client import CIPClient

        cip = CIPClient()
        cip.shutdown_for_exit()
        assert cip._exiting is True
        cip._reconnect_timer = None
        cip._schedule_reconnect()
        assert cip._reconnect_timer is None
        cip._exiting = False

