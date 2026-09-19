# -*- coding: utf-8 -*-
"""Recuperação segura da FSM sincronizada com tags do CLP após reboot."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional, Tuple


@dataclass
class PlcSnapshot:
    """Instantâneo de tags CLP relevantes para recovery."""

    robot_error: Optional[bool] = None
    robot_busy: Optional[bool] = None
    robot_ack: Optional[bool] = None
    robot_pick_complete: Optional[bool] = None
    robot_place_complete: Optional[bool] = None
    plc_authorize_detection: Optional[bool] = None
    plc_cycle_complete: Optional[bool] = None
    plc_emergency_stop: Optional[bool] = None
    safety_gate_closed: Optional[bool] = None
    safety_area_clear: Optional[bool] = None
    safety_light_curtain_ok: Optional[bool] = None
    safety_emergency_stop: Optional[bool] = None
    read_failed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


RECOVERY_READ_TAGS = (
    "RobotError",
    "RobotBusy",
    "RobotAck",
    "RobotPickComplete",
    "RobotPlaceComplete",
    "PlcAuthorizeDetection",
    "PlcCycleComplete",
    "PlcEmergencyStop",
    "SafetyGateClosed",
    "SafetyAreaClear",
    "SafetyLightCurtainOK",
    "SafetyEmergencyStop",
)

# (logical_name, human-readable PLC tag = False reason)
_FIELD_SAFETY_CHECKS: Tuple[Tuple[str, str, str], ...] = (
    ("safety_gate_closed", "SafetyGateClosed", "Safety_GateClosed=False"),
    ("safety_area_clear", "SafetyAreaClear", "Safety_AreaClear=False"),
    ("safety_light_curtain_ok", "SafetyLightCurtainOK", "Safety_LightCurtainOK=False"),
)


async def read_plc_snapshot(cip_client) -> PlcSnapshot:
    """Lê tags do CLP para decisão de recovery."""
    snapshot = PlcSnapshot()
    failures = 0
    for tag in RECOVERY_READ_TAGS:
        try:
            value = await cip_client.read_tag(tag)
            setattr(snapshot, _tag_to_field(tag), bool(value))
        except Exception:
            failures += 1
            setattr(snapshot, _tag_to_field(tag), None)
    snapshot.read_failed = failures > 0
    return snapshot


def _tag_to_field(tag: str) -> str:
    mapping = {
        "RobotError": "robot_error",
        "RobotBusy": "robot_busy",
        "RobotAck": "robot_ack",
        "RobotPickComplete": "robot_pick_complete",
        "RobotPlaceComplete": "robot_place_complete",
        "PlcAuthorizeDetection": "plc_authorize_detection",
        "PlcCycleComplete": "plc_cycle_complete",
        "PlcEmergencyStop": "plc_emergency_stop",
        "SafetyGateClosed": "safety_gate_closed",
        "SafetyAreaClear": "safety_area_clear",
        "SafetyLightCurtainOK": "safety_light_curtain_ok",
        "SafetyEmergencyStop": "safety_emergency_stop",
    }
    return mapping[tag]


def safety_block_reason(
    *,
    plc_emergency_stop: Optional[bool],
    safety_emergency_stop: Optional[bool] = None,
    safety_gate_closed: Optional[bool] = None,
    safety_area_clear: Optional[bool] = None,
    safety_light_curtain_ok: Optional[bool] = None,
    require_field_safety_tags: bool = False,
) -> Optional[str]:
    """
    Mesma regra usada no poll da FSM e no recovery.

    PlcEmergencyStop True = paragem (bloqueia sempre).
    SafetyEmergencyStop True = emergência NÃO ativa (OK); False = bloqueio
    só quando require_field_safety_tags.
    Gate/área/cortina só quando require_field_safety_tags.
    """
    if plc_emergency_stop:
        return "PlcEmergencyStop RobotCtrl_EmergencyStop=True"

    if not require_field_safety_tags:
        return None

    if safety_emergency_stop is not True:
        return "SafetyEmergencyStop Safety_EmergencyStop is not True"

    field_values = {
        "safety_gate_closed": safety_gate_closed,
        "safety_area_clear": safety_area_clear,
        "safety_light_curtain_ok": safety_light_curtain_ok,
    }
    for attr, logical, message in _FIELD_SAFETY_CHECKS:
        if field_values[attr] is not True:
            return f"{logical} {message}"
    return None


def resolve_safe_state(
    snapshot: PlcSnapshot,
    *,
    production_mode: bool = False,
    require_field_safety_tags: bool = False,
) -> str:
    """
    Mapeia tags CLP para estado FSM seguro (valor string do enum).

    Nunca retoma handshake a meio (ex.: WAITING_ACK); estados ambíguos → ERROR em production.
    Safety usa a mesma regra que o poll (safety_block_reason).
    """
    blocked = safety_block_reason(
        plc_emergency_stop=snapshot.plc_emergency_stop,
        safety_emergency_stop=snapshot.safety_emergency_stop,
        safety_gate_closed=snapshot.safety_gate_closed,
        safety_area_clear=snapshot.safety_area_clear,
        safety_light_curtain_ok=snapshot.safety_light_curtain_ok,
        require_field_safety_tags=require_field_safety_tags,
    )
    if blocked:
        return "SAFETY_BLOCKED"

    if snapshot.robot_error:
        return "ERROR"

    if snapshot.robot_ack:
        return "ERROR"

    # Ciclo já fechado no CLP → Idle (não retomar pick/place).
    if snapshot.plc_cycle_complete and not snapshot.robot_busy:
        return "WAITING_AUTHORIZATION"

    # FSM mínima: nunca retomar Pick/Place a meio (sem pose nesta sessão).
    mid_cycle = bool(
        snapshot.robot_busy
        or snapshot.robot_pick_complete
        or snapshot.robot_place_complete
    )
    if mid_cycle:
        return "ERROR" if production_mode else "WAITING_AUTHORIZATION"

    if snapshot.plc_authorize_detection and not snapshot.robot_busy:
        return "WAITING_AUTHORIZATION"

    if snapshot.read_failed:
        return "ERROR" if production_mode else "WAITING_AUTHORIZATION"

    return "ERROR" if production_mode else "WAITING_AUTHORIZATION"
