# -*- coding: utf-8 -*-
"""Testes da matriz de recovery PLC → FSM."""

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control.plc_recovery import PlcSnapshot, resolve_safe_state


def _snap(**kwargs) -> PlcSnapshot:
    return PlcSnapshot(**kwargs)


class TestPlcRecovery:
    def test_emergency_stop_blocks(self):
        s = _snap(plc_emergency_stop=True)
        assert resolve_safe_state(s) == "SAFETY_BLOCKED"

    def test_safety_emergency_blocks(self):
        s = _snap(safety_emergency_stop=True)
        assert resolve_safe_state(s) == "SAFETY_BLOCKED"

    def test_production_safety_incomplete(self):
        s = _snap(safety_gate_closed=False, safety_area_clear=True, safety_light_curtain_ok=True)
        assert resolve_safe_state(s, production_mode=True) == "SAFETY_BLOCKED"

    def test_robot_error(self):
        s = _snap(robot_error=True)
        assert resolve_safe_state(s) == "ERROR"

    def test_robot_ack_mid_handshake_is_error(self):
        s = _snap(robot_ack=True, robot_busy=False)
        assert resolve_safe_state(s) == "ERROR"

    def test_waiting_place(self):
        s = _snap(robot_pick_complete=True, robot_place_complete=False)
        assert resolve_safe_state(s) == "WAITING_PLACE"

    def test_waiting_pick(self):
        s = _snap(robot_busy=True, robot_pick_complete=False)
        assert resolve_safe_state(s) == "WAITING_PICK"

    def test_waiting_cycle_start(self):
        s = _snap(robot_place_complete=True, robot_busy=False)
        assert resolve_safe_state(s) == "WAITING_CYCLE_START"

    def test_ready_for_next(self):
        s = _snap(plc_cycle_complete=True)
        assert resolve_safe_state(s) == "READY_FOR_NEXT"

    def test_waiting_authorization(self):
        s = _snap(plc_authorize_detection=True, robot_busy=False)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_read_failed_production_fail_closed(self):
        s = _snap(
            read_failed=True,
            safety_gate_closed=True,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
        )
        assert resolve_safe_state(s, production_mode=True) == "ERROR"

    def test_read_failed_dev_permissive(self):
        s = _snap(
            read_failed=True,
            safety_gate_closed=True,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
        )
        assert resolve_safe_state(s, production_mode=False) == "WAITING_AUTHORIZATION"

    def test_ambiguous_production_error(self):
        s = _snap(
            safety_gate_closed=True,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
        )
        assert resolve_safe_state(s, production_mode=True) == "ERROR"
