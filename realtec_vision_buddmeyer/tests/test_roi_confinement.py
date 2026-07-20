# -*- coding: utf-8 -*-
"""Testes de confinamento ROI e persistência de dimensões."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_detection(cx: float, cy: float, confidence: float = 0.9, area_px: float = 1000.0):
    from detection.events import BoundingBox, Detection

    return Detection(
        bbox=BoundingBox(cx - 10, cy - 10, cx + 10, cy + 10),
        confidence=confidence,
        class_id=0,
        class_name="Embalagem",
        mask=np.ones((20, 20), dtype=bool),
        centroid_override=(cx, cy),
        angle_deg=30.0,
        area_px=area_px,
    )


class TestRoiConfinementHelpers:
    def test_is_roi_confinement_active_requires_enabled_and_roi(self):
        from config.settings import PreprocessSettings
        from preprocessing.roi_manager import is_roi_confinement_active

        active = PreprocessSettings(roi=[0, 0, 100, 100], roi_enabled=True)
        inactive = PreprocessSettings(roi=[0, 0, 100, 100], roi_enabled=False)
        assert is_roi_confinement_active(active) is True
        assert is_roi_confinement_active(inactive) is False

    def test_confine_centroid_projects_outside_point(self):
        from config.settings import PreprocessSettings
        from preprocessing.roi_manager import confine_centroid_for_pick

        pre = PreprocessSettings(roi=[100, 100, 50, 50], roi_enabled=True)
        cx, cy = confine_centroid_for_pick(10.0, 10.0, pre)
        assert cx == 100.0
        assert cy == 100.0

    def test_confine_centroid_noop_when_disabled(self):
        from config.settings import PreprocessSettings
        from preprocessing.roi_manager import confine_centroid_for_pick

        pre = PreprocessSettings(roi=[100, 100, 50, 50], roi_enabled=False)
        cx, cy = confine_centroid_for_pick(10.0, 20.0, pre)
        assert cx == 10.0
        assert cy == 20.0


class TestDetectionEventRoiConfinement:
    def test_from_result_confines_pick_centroid(self):
        from detection.events import DetectionEvent, DetectionResult

        det = _make_detection(10.0, 10.0)
        result = DetectionResult(detections=[det])
        roi = [100, 100, 80, 80]
        ev = DetectionEvent.from_result(
            result,
            roi_enabled=True,
            roi=roi,
        )
        assert ev.detected is True
        assert ev.centroid == (100.0, 100.0)
        assert ev.all_detections_scaled[0]["centroid_px"] == (100.0, 100.0)

    def test_from_result_keeps_centroid_when_confinement_off(self):
        from detection.events import DetectionEvent, DetectionResult

        det = _make_detection(10.0, 10.0)
        result = DetectionResult(detections=[det])
        ev = DetectionEvent.from_result(
            result,
            roi_enabled=False,
            roi=[100, 100, 80, 80],
        )
        assert ev.centroid == (10.0, 10.0)


class TestStatusPanelRoi:
    def test_get_roi_returns_spinbox_values_when_disabled(self, qtbot):
        from ui.widgets.status_panel import StatusPanel

        panel = StatusPanel()
        qtbot.addWidget(panel)
        panel.set_roi(False, 50, 60, 120, 130)
        enabled, coords = panel.get_roi()
        assert enabled is False
        assert coords == [50, 60, 120, 130]
