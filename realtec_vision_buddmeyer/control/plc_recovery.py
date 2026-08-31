# -*- coding: utf-8 -*-
"""Recuperação segura da FSM sincronizada com tags do CLP após reboot."""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional


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


def _safety_ok(snapshot: PlcSnapshot, *, production_mode: bool) -> bool:
    if not production_mode:
        return True
    checks = (
        snapshot.safety_gate_closed,
        snapshot.safety_area_clear,
        snapshot.safety_light_curtain_ok,
    )
    if any(v is None for v in checks):
        return False
    return bool(snapshot.safety_gate_closed and snapshot.safety_area_clear and snapshot.safety_light_curtain_ok)


def resolve_safe_state(
    snapshot: PlcSnapshot,
    *,
    production_mode: bool = False,
) -> str:
    """
    Mapeia tags CLP para estado FSM seguro (valor string do enum).

    Nunca retoma handshake a meio (ex.: WAITING_ACK); estados ambíguos → ERROR em production.
    """
    if snapshot.plc_emergency_stop or snapshot.safety_emergency_stop:
        return "SAFETY_BLOCKED"

    if production_mode and not _safety_ok(snapshot, production_mode=True):
        return "SAFETY_BLOCKED"

    if snapshot.robot_error:
        return "ERROR"

    if snapshot.robot_ack:
        return "ERROR"

    if snapshot.robot_place_complete and not snapshot.robot_busy:
        return "WAITING_CYCLE_START"

    if snapshot.robot_pick_complete and not snapshot.robot_place_complete:
        return "WAITING_PLACE"

    if snapshot.robot_busy and not snapshot.robot_pick_complete:
        return "WAITING_PICK"

    if snapshot.plc_cycle_complete:
        return "READY_FOR_NEXT"

    if snapshot.plc_authorize_detection and not snapshot.robot_busy:
        return "WAITING_AUTHORIZATION"

    if snapshot.read_failed:
        return "ERROR" if production_mode else "WAITING_AUTHORIZATION"

    return "ERROR" if production_mode else "WAITING_AUTHORIZATION"
