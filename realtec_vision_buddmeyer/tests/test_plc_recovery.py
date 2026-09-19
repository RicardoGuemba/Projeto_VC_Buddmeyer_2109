# -*- coding: utf-8 -*-
"""Testes da matriz de recovery PLC → FSM."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from control.plc_recovery import PlcSnapshot, resolve_safe_state, safety_block_reason


def _snap(**kwargs) -> PlcSnapshot:
    return PlcSnapshot(**kwargs)


class TestSafetyBlockReason:
    def test_estop_always_blocks(self):
        assert safety_block_reason(plc_emergency_stop=True) is not None
        assert "PlcEmergencyStop" in safety_block_reason(plc_emergency_stop=True)

    def test_gate_ignored_when_optional(self):
        assert (
            safety_block_reason(
                plc_emergency_stop=False,
                safety_gate_closed=False,
                require_field_safety_tags=False,
            )
            is None
        )

    def test_gate_blocks_when_required(self):
        reason = safety_block_reason(
            plc_emergency_stop=False,
            safety_emergency_stop=True,
            safety_gate_closed=False,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
            require_field_safety_tags=True,
        )
        assert reason is not None
        assert "SafetyGateClosed" in reason


class TestPlcRecovery:
    def test_emergency_stop_blocks(self):
        s = _snap(plc_emergency_stop=True)
        assert resolve_safe_state(s) == "SAFETY_BLOCKED"

    def test_safety_emergency_true_is_ok(self):
        """SafetyEmergencyStop True = emergência não ativa (contrato)."""
        s = _snap(safety_emergency_stop=True, plc_authorize_detection=True)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_safety_emergency_false_blocks_when_required(self):
        s = _snap(
            safety_emergency_stop=False,
            safety_gate_closed=True,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
        )
        assert resolve_safe_state(s, require_field_safety_tags=True) == "SAFETY_BLOCKED"

    def test_field_safety_incomplete_when_required(self):
        s = _snap(
            safety_emergency_stop=True,
            safety_gate_closed=False,
            safety_area_clear=True,
            safety_light_curtain_ok=True,
        )
        assert resolve_safe_state(s, require_field_safety_tags=True) == "SAFETY_BLOCKED"

    def test_field_safety_incomplete_optional_does_not_block(self):
        s = _snap(
            plc_authorize_detection=True,
            safety_gate_closed=False,
            safety_area_clear=False,
            safety_light_curtain_ok=False,
        )
        assert resolve_safe_state(s, require_field_safety_tags=False) == "WAITING_AUTHORIZATION"

    def test_robot_error(self):
        s = _snap(robot_error=True)
        assert resolve_safe_state(s) == "ERROR"

    def test_robot_ack_mid_handshake_is_error(self):
        s = _snap(robot_ack=True, robot_busy=False)
        assert resolve_safe_state(s) == "ERROR"

    def test_mid_cycle_pick_is_idle_in_lab(self):
        s = _snap(robot_pick_complete=True, robot_place_complete=False)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_mid_cycle_pick_is_error_in_production(self):
        s = _snap(robot_busy=True, robot_pick_complete=False)
        assert resolve_safe_state(s, production_mode=True) == "ERROR"

    def test_place_complete_not_busy_is_idle_in_lab(self):
        s = _snap(robot_place_complete=True, robot_busy=False)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_cycle_complete_is_idle(self):
        s = _snap(plc_cycle_complete=True, robot_busy=False)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_waiting_authorization(self):
        s = _snap(plc_authorize_detection=True, robot_busy=False)
        assert resolve_safe_state(s) == "WAITING_AUTHORIZATION"

    def test_authorize_true_gate_false_optional_stays_waiting_auth(self):
        """POC: Authorize True não é mascarado por Safety_* a False."""
        s = _snap(
            plc_authorize_detection=True,
            plc_emergency_stop=False,
            robot_ack=False,
            safety_gate_closed=False,
        )
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
