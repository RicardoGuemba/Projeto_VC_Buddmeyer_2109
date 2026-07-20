# -*- coding: utf-8 -*-
"""Testes CoordinateTransform."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestCoordinateTransform:
    def test_scale_conversion(self):
        from coordinate.transform import CoordinateTransform

        t = CoordinateTransform(mm_per_px=10.0)
        pose = t.vision_to_robot(12.0, 8.0, angle_deg=30.0, confidence=0.8)
        assert pose.x_mm == 120.0
        assert pose.y_mm == 80.0
        assert pose.angle_deg == 30.0
