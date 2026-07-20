# -*- coding: utf-8 -*-
"""Testes stream auto-recovery."""

import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestStreamRecovery:
    def test_unhealthy_triggers_recovery(self):
        from streaming.stream_health import HealthStatus, StreamHealthInfo
        from streaming.stream_manager import StreamManager

        StreamManager._instance = None
        mgr = StreamManager()
        mgr._is_running = True
        mgr._settings.reliability.stream_auto_restart = True
        mgr._settings.streaming.unhealthy_restart_after_s = 0.01
        mgr._poll_timer = None

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
            mgr._on_health_changed(info)
            mgr._unhealthy_since = __import__("time").time() - 1.0
            mgr._on_health_changed(info)
            stop_mock.assert_called()
            start_mock.assert_called()

        StreamManager._instance = None
