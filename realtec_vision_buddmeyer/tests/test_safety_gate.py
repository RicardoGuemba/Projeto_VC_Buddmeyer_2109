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

        RobotController._reset_instance_for_tests()
        CIPClient._reset_instance_for_tests()

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            cip._simulated_plc._tags["RobotCtrl_EmergencyStop"] = True

            rc = RobotController()
            assert await rc._check_safety() is False
            assert "PlcEmergencyStop" in rc.last_safety_block_reason

        asyncio.run(_run())

    def test_optional_field_tags_do_not_block_open_gate(self):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController

        RobotController._reset_instance_for_tests()
        CIPClient._reset_instance_for_tests()

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            cip._simulated_plc._tags["Safety_GateClosed"] = False
            cip._simulated_plc._tags["Safety_AreaClear"] = False
            cip._simulated_plc._tags["Safety_LightCurtainOK"] = False

            rc = RobotController()
            rc._settings.reliability.require_field_safety_tags = False
            assert await rc._check_safety() is True
            assert rc.last_safety_block_reason == ""

        asyncio.run(_run())

    def test_required_field_tags_block_open_gate(self):
        from communication.cip_client import CIPClient
        from control.robot_controller import RobotController

        RobotController._reset_instance_for_tests()
        CIPClient._reset_instance_for_tests()

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            cip._simulated_plc._tags["Safety_GateClosed"] = False

            rc = RobotController()
            rc._settings.reliability.require_field_safety_tags = True
            assert await rc._check_safety() is False
            assert "SafetyGateClosed" in rc.last_safety_block_reason

        asyncio.run(_run())

    def test_robot_ack_recursion_is_fail_closed(self):
        from communication.cip_client import CIPClient
        from communication.exceptions import CIPTagError

        CIPClient._reset_instance_for_tests()

        async def _run():
            cip = CIPClient()
            await cip._connect_simulated()
            original = cip._simulated_plc.read_variable

            def boom(name):
                if name == "ROBOT_ACK":
                    raise RecursionError("aphyt")
                return original(name)

            cip._simulated_plc.read_variable = boom
            with pytest.raises(CIPTagError, match="fail-closed"):
                await cip.read_tag("RobotAck")

        asyncio.run(_run())
