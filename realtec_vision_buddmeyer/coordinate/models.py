# -*- coding: utf-8 -*-
"""Modelos de pose para integração robótica."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional


@dataclass
class VisionPose:
    x_px: float
    y_px: float
    angle_deg: float = 0.0


@dataclass
class RobotPose:
    x_mm: float
    y_mm: float
    z_mm: float = 0.0
    angle_deg: float = 0.0
    frame_id: str = "robot_base"
    confidence: float = 0.0
    timestamp: Optional[datetime] = None

    def to_dict(self) -> dict:
        ts = self.timestamp or datetime.now(timezone.utc)
        return {
            "x_mm": self.x_mm,
            "y_mm": self.y_mm,
            "z_mm": self.z_mm,
            "angle_deg": self.angle_deg,
            "frame_id": self.frame_id,
            "confidence": self.confidence,
            "timestamp": ts.isoformat(),
        }
