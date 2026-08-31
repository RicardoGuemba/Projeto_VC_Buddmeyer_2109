# -*- coding: utf-8 -*-
"""Testes do overlay OpenCV multi-detecção."""

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _bbox(x1, y1, x2, y2):
    return SimpleNamespace(x1=x1, y1=y1, x2=x2, y2=y2, width=x2 - x1, height=y2 - y1)


def _det(cx, cy, size, area, conf=0.8):
    mask = np.zeros((200, 200), dtype=bool)
    half = size // 2
    x, y = int(cx), int(cy)
    mask[y - half:y + half, x - half:x + half] = True
    return SimpleNamespace(
        class_name="Embalagem",
        confidence=conf,
        centroid=(float(cx), float(cy)),
        effective_area_px=float(area),
        bbox=_bbox(x - half, y - half, x + half, y + half),
        mask=mask,
        angle_deg=10.0,
        major_axis_length=float(size),
        has_orientation=True,
    )


class TestDetectionOverlay:
    def test_format_centroid_metrics_summary(self):
        from ui.overlay_constants import format_centroid_metrics_summary

        text = format_centroid_metrics_summary(100.0, 50.0, 10000.0, 45.0, mm_per_px=10.0)
        assert "X:1000" in text
        assert "Y:500" in text
        assert "A:10000.0cm²" in text
        assert "∠45°" in text

        ascii_text = format_centroid_metrics_summary(
            100.0, 50.0, 10000.0, 45.0, mm_per_px=10.0, ascii_safe=True,
        )
        assert "A:10000.0cm2" in ascii_text
        assert "ang:45deg" in ascii_text
        assert "?" not in ascii_text
        assert ascii_text.isascii()

        pick = format_centroid_metrics_summary(
            10.0, 20.0, 500.0, None, mm_per_px=1.0, is_pick=True,
        )
        assert "(pick)" in pick
        assert "∠" not in pick

    def test_ordered_puts_pick_last(self):
        from ui.detection_overlay import ordered_detections_for_overlay

        a = _det(50, 50, 30, 900)
        b = _det(150, 80, 40, 1600)
        pick = b
        ordered = ordered_detections_for_overlay([a, b], pick)
        assert ordered == [a, b]
        assert ordered[-1] is pick

    def test_binarize_bool_mask(self):
        from ui.detection_overlay import binarize_mask

        mask = np.zeros((10, 10), dtype=bool)
        mask[2:5, 2:5] = True
        out = binarize_mask(mask)
        assert out.dtype == np.uint8
        assert out[3, 3] == 255
        assert out[0, 0] == 0

    def test_draw_all_masks_changes_pixels_for_each_object(self):
        from ui.detection_overlay import draw_detection_masks_on_frame

        frame = np.zeros((200, 200, 3), dtype=np.uint8)
        frame[:] = (40, 40, 40)
        small = _det(50, 50, 30, 900, conf=0.7)
        big = _det(150, 80, 40, 1600, conf=0.9)
        pick = big

        out = draw_detection_masks_on_frame(frame, [small, big], pick, mm_per_px=1.0)

        assert not np.array_equal(out[50, 50], frame[50, 50])
        assert not np.array_equal(out[80, 150], frame[80, 150])
        assert not np.array_equal(out[50, 50], out[80, 150])

    def test_prepare_mask_canvas_embeds_bbox_local_mask(self):
        from ui.detection_overlay import prepare_mask_canvas

        mask = np.zeros((20, 30), dtype=bool)
        mask[2:18, 2:28] = True
        bbox = SimpleNamespace(x1=50, y1=40, x2=80, y2=60)
        canvas = prepare_mask_canvas(mask, frame_h=200, frame_w=200, bbox=bbox)
        assert canvas.shape == (200, 200)
        assert canvas[50, 70] == 255
        assert canvas[0, 0] == 0

    def test_draw_three_objects_all_regions_touched(self):
        from ui.detection_overlay import draw_detection_masks_on_frame

        frame = np.full((220, 220, 3), 30, dtype=np.uint8)
        d1 = _det(40, 40, 24, 576)
        d2 = _det(110, 60, 28, 784)
        d3 = _det(170, 140, 32, 1024)
        pick = d2
        out = draw_detection_masks_on_frame(frame, [d1, d2, d3], pick, mm_per_px=1.0)

        changed = 0
        for det in (d1, d2, d3):
            x1, y1 = int(det.bbox.x1), int(det.bbox.y1)
            x2, y2 = int(det.bbox.x2), int(det.bbox.y2)
            region_out = out[y1:y2, x1:x2]
            region_in = frame[y1:y2, x1:x2]
            if not np.array_equal(region_out, region_in):
                changed += 1
        assert changed == 3

    def test_pick_axis_anchored_at_mask_centroid_when_roi_clamps_pick(self):
        from ui.detection_overlay import draw_detection_masks_on_frame

        frame = np.zeros((300, 350, 3), dtype=np.uint8)
        pick = _det(50.0, 175.0, 40, 1600, conf=0.95)
        pick.angle_deg = 0.0
        roi = [100, 100, 200, 150]
        out = draw_detection_masks_on_frame(
            frame,
            [pick],
            pick,
            mm_per_px=1.0,
            roi_enabled=True,
            roi=roi,
        )
        axis_x, axis_y = int(pick.centroid[0]), int(pick.centroid[1])
        pick_x, pick_y = 100, 175
        assert out[pick_y, pick_x].any() != 0
        assert out[axis_y, axis_x].any() != 0
