# -*- coding: utf-8 -*-
"""Testes do PickStabilizer."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _det(cx: float, cy: float):
    from detection.events import BoundingBox, Detection

    return Detection(
        bbox=BoundingBox(0, 0, 50, 50),
        confidence=0.9,
        class_id=0,
        class_name="Embalagem",
        mask=np.ones((50, 50), dtype=bool),
        centroid_override=(cx, cy),
        area_px=1000.0,
    )


class TestPickStabilizer:
    def test_requires_stable_frames(self):
        from detection.pick_stabilizer import PickStabilizer

        stab = PickStabilizer(stable_frames=3, centroid_epsilon_px=15.0)
        det = _det(100.0, 100.0)

        assert stab.update(det) is None
        assert stab.update(det) is None
        assert stab.update(det) is not None

    def test_resets_on_large_movement(self):
        from detection.pick_stabilizer import PickStabilizer

        stab = PickStabilizer(stable_frames=2, centroid_epsilon_px=10.0)
        assert stab.update(_det(10.0, 10.0)) is None
        assert stab.update(_det(100.0, 100.0)) is None

    def test_tracks_vcpn_not_mask_centroid(self):
        from detection.pick_stabilizer import PickStabilizer

        a = _det(100.0, 100.0)
        a.vcp_n = (100.0, 45.0)
        b = _det(100.0, 100.0)
        b.vcp_n = (100.0, 155.0)
        stab = PickStabilizer(stable_frames=2, centroid_epsilon_px=15.0)
        assert stab.update(a) is None
        assert stab.update(b) is None
