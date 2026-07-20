# -*- coding: utf-8 -*-
"""Testes de seleção pick-and-place e conversão de unidades."""

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _make_detection(confidence: float, area_px: float):
    from detection.events import BoundingBox, Detection

    return Detection(
        bbox=BoundingBox(0, 0, 50, 50),
        confidence=confidence,
        class_id=0,
        class_name="Embalagem",
        mask=np.ones((50, 50), dtype=bool),
        centroid_override=(25.0, 25.0),
        angle_deg=30.0,
        area_px=area_px,
    )


class TestSelectPickTarget:
    def test_area_then_conf_prefers_larger_area(self):
        from detection.pick_selection import select_pick_target

        low_conf_big = _make_detection(confidence=0.6, area_px=10000.0)
        high_conf_small = _make_detection(confidence=0.95, area_px=200.0)
        pick = select_pick_target(
            [low_conf_big, high_conf_small], method="area_then_conf"
        )
        assert pick is low_conf_big

    def test_area_then_conf_tiebreaks_by_confidence(self):
        from detection.pick_selection import select_pick_target

        a = _make_detection(confidence=0.7, area_px=5000.0)
        b = _make_detection(confidence=0.9, area_px=5000.0)
        pick = select_pick_target([a, b], method="area_then_conf")
        assert pick is b

    def test_area_only_ignores_confidence(self):
        from detection.pick_selection import select_pick_target

        low_conf_big = _make_detection(confidence=0.6, area_px=10000.0)
        high_conf_small = _make_detection(confidence=0.95, area_px=200.0)
        pick = select_pick_target(
            [low_conf_big, high_conf_small], method="area_only"
        )
        assert pick is low_conf_big

    def test_confidence_only(self):
        from detection.pick_selection import select_pick_target

        low_conf_big = _make_detection(confidence=0.6, area_px=10000.0)
        high_conf_small = _make_detection(confidence=0.95, area_px=200.0)
        pick = select_pick_target(
            [low_conf_big, high_conf_small], method="confidence_only"
        )
        assert pick is high_conf_small

    def test_weighted_score_matches_legacy(self):
        from detection.events import DetectionResult
        from detection.pick_selection import select_pick_target

        low_conf_big = _make_detection(confidence=0.6, area_px=10000.0)
        high_conf_small = _make_detection(confidence=0.95, area_px=200.0)
        result = DetectionResult(detections=[low_conf_big, high_conf_small])
        legacy = result.best_by_priority(confidence_weight=1.0, area_weight=1.0)
        pick = select_pick_target(
            result.detections,
            method="weighted_score",
            confidence_weight=1.0,
            area_weight=1.0,
        )
        assert pick is legacy

    def test_empty_returns_none(self):
        from detection.pick_selection import select_pick_target

        assert select_pick_target([], method="area_then_conf") is None


class TestScaleDetectionMetrics:
    def test_centroid_mm_and_area_cm2(self):
        from detection.pick_selection import scale_detection_metrics

        det = _make_detection(confidence=0.8, area_px=100.0)
        metrics = scale_detection_metrics(det, mm_per_px=10.0, plc_area_unit="cm2")
        assert metrics["centroid_mm"] == (250.0, 250.0)
        assert metrics["area_cm2"] == 100.0  # 100 px² * 100 mm²/px² / 100
        assert metrics["area_plc"] == 100.0

    def test_area_for_plc_units(self):
        from detection.pick_selection import area_for_plc

        assert area_for_plc(100.0, 10.0, "px2") == 100.0
        assert area_for_plc(100.0, 10.0, "mm2") == 10000.0
        assert area_for_plc(100.0, 10.0, "cm2") == 100.0


class TestDetectionSettingsMigration:
    def test_prioritize_area_true_migrates_to_weighted_score(self):
        from config.settings import DetectionSettings

        cfg = DetectionSettings.model_validate({"prioritize_area": True})
        assert cfg.pick_selection_method == "weighted_score"

    def test_prioritize_area_false_migrates_to_confidence_only(self):
        from config.settings import DetectionSettings

        cfg = DetectionSettings.model_validate({"prioritize_area": False})
        assert cfg.pick_selection_method == "confidence_only"

    def test_default_is_area_then_conf(self):
        from config.settings import DetectionSettings

        cfg = DetectionSettings()
        assert cfg.pick_selection_method == "area_then_conf"
        assert cfg.plc_area_unit == "cm2"
