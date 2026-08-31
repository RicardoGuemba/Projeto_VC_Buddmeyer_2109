# -*- coding: utf-8 -*-
"""Testes das constantes e helpers do overlay."""

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _det(conf=0.8, area=100.0, cx=25.0, cy=25.0):
    return SimpleNamespace(
        class_name="Embalagem",
        confidence=conf,
        centroid=(cx, cy),
        effective_area_px=area,
    )


class TestOverlayConstants:
    def test_is_pick_by_reference(self):
        from ui.overlay_constants import is_pick_detection

        d = _det()
        assert is_pick_detection(d, d) is True

    def test_not_pick_different_instance(self):
        from ui.overlay_constants import is_pick_detection

        a = _det(area=500.0)
        b = _det(area=500.0)
        assert is_pick_detection(a, b) is False

    def test_other_mask_color_bgr_is_blue_dominant(self):
        from ui.overlay_constants import OTHER_MASK_COLOR_BGR

        b, g, r = OTHER_MASK_COLOR_BGR
        assert b > r and b > g

    def test_opencv_safe_label_strips_unicode(self):
        from ui.overlay_constants import opencv_safe_label

        text = opencv_safe_label("A:207.3cm² ∠62° (pick)")
        assert "?" not in text
        assert text.isascii()
        assert "cm2" in text
        assert "ang:62deg" in text
        assert "(pick)" in text
