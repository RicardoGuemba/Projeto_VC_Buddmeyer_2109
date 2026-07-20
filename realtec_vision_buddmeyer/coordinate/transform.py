# -*- coding: utf-8 -*-
"""Transformação de coordenadas (modo scale v1)."""

from __future__ import annotations

from datetime import datetime, timezone
from functools import lru_cache
from typing import Optional

from config import get_settings

from .models import RobotPose, VisionPose


class CoordinateTransform:
    """Converte pixels de visão para mm no referencial configurado."""

    def __init__(self, mm_per_px: float = 1.0, z_mm: float = 0.0, frame_id: str = "robot_base"):
        self.mm_per_px = float(mm_per_px) or 1.0
        self.z_mm = float(z_mm)
        self.frame_id = frame_id

    @classmethod
    def from_settings(cls) -> "CoordinateTransform":
        s = get_settings()
        mm_per_px = getattr(s.preprocess, "roi_calibration_mm_per_px", 1.0) or 1.0
        return cls(mm_per_px=mm_per_px)

    def vision_to_robot(
        self,
        cx_px: float,
        cy_px: float,
        angle_deg: float = 0.0,
        confidence: float = 0.0,
    ) -> RobotPose:
        scale = self.mm_per_px
        return RobotPose(
            x_mm=float(cx_px) * scale,
            y_mm=float(cy_px) * scale,
            z_mm=self.z_mm,
            angle_deg=float(angle_deg),
            frame_id=self.frame_id,
            confidence=float(confidence),
            timestamp=datetime.now(timezone.utc),
        )

    def from_vision_pose(self, pose: VisionPose, confidence: float = 0.0) -> RobotPose:
        return self.vision_to_robot(
            pose.x_px, pose.y_px, pose.angle_deg, confidence=confidence
        )


@lru_cache(maxsize=1)
def get_coordinate_transform() -> CoordinateTransform:
    """Singleton leve alinhado às settings actuais."""
    return CoordinateTransform.from_settings()


def invalidate_coordinate_transform_cache() -> None:
    get_coordinate_transform.cache_clear()
