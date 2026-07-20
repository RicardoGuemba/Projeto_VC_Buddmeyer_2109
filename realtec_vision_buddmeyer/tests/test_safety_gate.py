# -*- coding: utf-8 -*-
"""Testes fail-closed de safety."""

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestSafetyGate:
    def test_safety_fail_closed_on_read_error_in_production(self):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController

        RobotController._reset_instance_for_tests()
        CIPClient._reset_instance_for_tests()

        async def _run():
            cip = CIPClient()
            cip._settings.reliability.production_mode = True
            await cip._connect_simulated()

            rc = RobotController()
            rc._settings.reliability.production_mode = True

            async def fail_read(_name):
                raise RuntimeError("read fail")

            cip.read_tag = fail_read  # type: ignore
            assert await rc._check_safety() is False

        asyncio.run(_run())

    def test_emergency_stop_blocks_safety(self):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            cip._simulated_plc._tags["RobotCtrl_EmergencyStop"] = True

            rc = RobotController()
            assert await rc._check_safety() is False

        asyncio.run(_run())
