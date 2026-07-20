# -*- coding: utf-8 -*-
"""Lógica compartilhada de overlay multi-detecção (OpenCV)."""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

import numpy as np

from ui.overlay_constants import (
    LABEL_FONT_SCALE,
    LABEL_FONT_THICKNESS,
    LABEL_OUTLINE_COLOR_BGR,
    LABEL_OUTLINE_THICKNESS,
    OTHER_LABEL_COLOR_BGR,
    OTHER_MASK_COLOR_BGR,
    OTHER_MASK_FILL_ALPHA,
    PICK_LABEL_COLOR_BGR,
    PICK_MASK_COLOR_BGR,
    PICK_MASK_FILL_ALPHA,
    format_centroid_metrics_summary,
    is_pick_detection,
)
from preprocessing.roi_manager import clamp_centroid_to_roi


def ordered_detections_for_overlay(
    detections: Sequence[Any],
    pick: Optional[Any],
) -> List[Any]:
    """Retorna todas as detecções: demais primeiro, pick por último."""
    if not detections:
        return []
    others = [d for d in detections if not is_pick_detection(d, pick)]
    if pick is None:
        return list(others)
    return list(others) + [pick]


def binarize_mask(mask: np.ndarray) -> np.ndarray:
    """Converte máscara bool/float/uint8 para uint8 0/255 para findContours."""
    if mask is None:
        return np.zeros((1, 1), dtype=np.uint8)
    arr = np.asarray(mask)
    if arr.dtype == bool:
        return (arr.astype(np.uint8)) * 255
    if np.issubdtype(arr.dtype, np.floating):
        return (arr > 0.5).astype(np.uint8) * 255
    return (arr > 0).astype(np.uint8) * 255


def draw_overlay_label(
    frame: np.ndarray,
    text: str,
    origin: Tuple[int, int],
    is_pick: bool,
) -> None:
    """Desenha rótulo legível com contorno escuro."""
    import cv2

    color = PICK_LABEL_COLOR_BGR if is_pick else OTHER_LABEL_COLOR_BGR
    x, y = origin
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(
        frame, text, (x, y), font, LABEL_FONT_SCALE,
        LABEL_OUTLINE_COLOR_BGR, LABEL_OUTLINE_THICKNESS, lineType=cv2.LINE_AA,
    )
    cv2.putText(
        frame, text, (x, y), font, LABEL_FONT_SCALE,
        color, LABEL_FONT_THICKNESS, lineType=cv2.LINE_AA,
    )


def mask_style_for_detection(detection: Any, pick: Optional[Any]) -> Tuple[Tuple[int, int, int], int, float]:
    """Cor BGR, espessura do contorno e alpha do preenchimento."""
    if is_pick_detection(detection, pick):
        return PICK_MASK_COLOR_BGR, 3, PICK_MASK_FILL_ALPHA
    return OTHER_MASK_COLOR_BGR, 2, OTHER_MASK_FILL_ALPHA


def prepare_mask_canvas(
    mask: np.ndarray,
    frame_h: int,
    frame_w: int,
    bbox: Any,
) -> np.ndarray:
    """
    Garante máscara no referencial do frame (H x W).

    Aceita máscara full-frame ou local ao bbox.
    """
    import cv2

    local = binarize_mask(mask)
    lh, lw = local.shape[:2]
    if lh == frame_h and lw == frame_w:
        return local

    x1 = max(0, int(bbox.x1))
    y1 = max(0, int(bbox.y1))
    x2 = min(frame_w, int(bbox.x2))
    y2 = min(frame_h, int(bbox.y2))
    bw = max(1, x2 - x1)
    bh = max(1, y2 - y1)

    if lh != bh or lw != bw:
        local = cv2.resize(local, (bw, bh), interpolation=cv2.INTER_NEAREST)

    canvas = np.zeros((frame_h, frame_w), dtype=np.uint8)
    h_put = min(bh, local.shape[0], frame_h - y1)
    w_put = min(bw, local.shape[1], frame_w - x1)
    if h_put > 0 and w_put > 0:
        canvas[y1:y1 + h_put, x1:x1 + w_put] = local[:h_put, :w_put]
    return canvas


def centroid_label_origin(
    cx: int,
    cy: int,
    frame_h: int,
    frame_w: int,
    *,
    offset_x: int = 12,
    offset_y: int = 10,
) -> Tuple[int, int]:
    """Posição do rótulo junto ao centroide, dentro do frame."""
    x = max(4, min(frame_w - 4, cx + offset_x))
    y = max(20, min(frame_h - 4, cy + offset_y))
    return x, y


def draw_detection_masks_on_frame(
    frame: np.ndarray,
    detections: Sequence[Any],
    pick: Optional[Any],
    mm_per_px: float = 1.0,
    *,
    roi_enabled: bool = False,
    roi: Optional[List[int]] = None,
) -> np.ndarray:
    """
    Desenha máscara de TODAS as detecções no frame BGR; destaca o pick.

    Retorna cópia do frame com overlay aplicado.
    """
    import cv2
    import math

    if frame is None or not detections:
        return frame

    out = frame.copy()
    frame_h, frame_w = out.shape[:2]

    for det in ordered_detections_for_overlay(detections, pick):
        is_pick = is_pick_detection(det, pick)
        color, thickness, fill_alpha = mask_style_for_detection(det, pick)

        bbox = det.bbox
        x1, y1 = int(bbox.x1), int(bbox.y1)
        x2, y2 = int(bbox.x2), int(bbox.y2)

        drew_mask = False
        if getattr(det, "mask", None) is not None:
            try:
                bin_mask = prepare_mask_canvas(det.mask, frame_h, frame_w, det.bbox)
                contours, _ = cv2.findContours(
                    bin_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE,
                )
                if contours:
                    overlay = out.copy()
                    cv2.drawContours(
                        overlay, contours, -1, color, thickness=cv2.FILLED,
                    )
                    cv2.addWeighted(
                        overlay, fill_alpha, out, 1.0 - fill_alpha, 0, out,
                    )
                    cv2.drawContours(
                        out, contours, -1, color, thickness=thickness,
                    )
                    drew_mask = True
            except Exception:
                drew_mask = False

        if not drew_mask:
            cv2.rectangle(out, (x1, y1), (x2, y2), color, thickness)

        cx_f, cy_f = det.centroid
        if roi_enabled and roi and len(roi) == 4:
            cx_f, cy_f = clamp_centroid_to_roi(cx_f, cy_f, tuple(roi))
        cx, cy = int(cx_f), int(cy_f)
        cv2.circle(out, (cx, cy), 8 if is_pick else 6, color, 2)

        if is_pick and getattr(det, "has_orientation", False) and getattr(det, "angle_deg", None) is not None:
            angle = float(det.angle_deg or 0.0)
            half = (
                0.5 * float(det.major_axis_length)
                if getattr(det, "major_axis_length", None)
                else 0.5 * max(bbox.width, bbox.height)
            )
            dx = math.cos(math.radians(angle)) * half
            dy = math.sin(math.radians(angle)) * half
            p1 = (int(cx_f - dx), int(cy_f - dy))
            p2 = (int(cx_f + dx), int(cy_f + dy))
            cv2.line(out, p1, p2, (255, 0, 255), 3)

        angle = getattr(det, "angle_deg", None) if getattr(det, "has_orientation", False) else None
        metrics_text = format_centroid_metrics_summary(
            cx_f,
            cy_f,
            det.effective_area_px,
            angle,
            mm_per_px,
            is_pick=is_pick,
        )
        class_label = f"{det.class_name} {det.confidence:.0%}"
        if is_pick:
            class_label += " [PICK]"

        draw_overlay_label(out, class_label, (x1, max(22, y1 - 8)), is_pick)

        mx, my = centroid_label_origin(cx, cy, frame_h, frame_w)
        draw_overlay_label(out, metrics_text, (mx, my), is_pick)

    return out
