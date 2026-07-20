# -*- coding: utf-8 -*-
"""Testes E2E do handshake FSM com SimulatedPLC."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _patch_fast_delays(sim):
    sim._ack_delay = 0.05
    sim._pick_delay = 0.05
    sim._place_delay = 0.05
    sim._cycle_end_delay = 0.05


@pytest.fixture
def reset_singletons():
    from communication.cip_client import CIPClient
    from control.robot_controller import RobotController

    RobotController._reset_instance_for_tests()
    CIPClient._reset_instance_for_tests()
    yield
    RobotController._reset_instance_for_tests()
    CIPClient._reset_instance_for_tests()


class TestFsmHandshake:
    def test_accepting_detections_only_in_detecting(self, reset_singletons):
        from control.robot_controller import RobotController, RobotControlState

        rc = RobotController()
        rc._state = RobotControlState.WAITING_AUTHORIZATION
        assert rc.accepting_detections is False
        rc._state = RobotControlState.DETECTING
        assert rc.accepting_detections is True

    def test_process_detection_ignored_outside_detecting(self, reset_singletons):
        from control.robot_controller import RobotController, RobotControlState
        from detection.events import DetectionEvent

        rc = RobotController()
        rc._state = RobotControlState.WAITING_ACK
        event = DetectionEvent(
            detected=True,
            centroid=(10.0, 20.0),
            confidence=0.9,
            detection_count=1,
            inference_time_ms=5.0,
        )
        rc.process_detection(event)
        assert rc._current_detection is None

    def test_continuous_handshake_simulated_plc(self, reset_singletons):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController, RobotControlState
        from detection.events import DetectionEvent

        async def _run():
            cip = CIPClient()
            cip._settings.cip.simulated = True
            await cip.connect()
            _patch_fast_delays(cip._simulated_plc)

            rc = RobotController()
            rc._settings.robot_control.bypass_authorization = True
            rc.set_cycle_mode("continuous")
            rc.start()

            for _ in range(30):
                await rc._process_current_state()
                await asyncio.sleep(0.02)
                if rc.state == RobotControlState.DETECTING:
                    break

            assert rc.state == RobotControlState.DETECTING

            event = DetectionEvent(
                detected=True,
                centroid=(120.0, 80.0),
                confidence=0.92,
                detection_count=1,
                inference_time_ms=12.0,
                angle_deg=45.0,
                area_px=5000.0,
            )
            rc.process_detection(event)

            for _ in range(150):
                await rc._process_current_state()
                await asyncio.sleep(0.05)
                if rc.cycle_count >= 1:
                    break

            rc.stop()
            assert rc.cycle_count >= 1

        asyncio.run(_run())

    def test_robot_error_sets_fault(self, reset_singletons):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController, RobotControlState

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            rc = RobotController()
            rc._is_running = True
            rc._state = RobotControlState.WAITING_PICK
            cip._simulated_plc._tags["ROBOT_ERROR"] = True

            triggered = await rc._check_robot_error()
            assert triggered is True
            assert rc.state == RobotControlState.ERROR

        asyncio.run(_run())
