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
    VCP_MARKER_COLOR_BGR,
    VCPN_COLOR_BGR,
    VCP_REF_COLOR_BGR,
    format_centroid_metrics_lines,
    is_pick_detection,
    opencv_safe_label,
)
from preprocessing.roi_manager import clamp_centroid_for_pick


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
    text = opencv_safe_label(text)
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


def vcp_vector_endpoints(
    origin: Tuple[float, float],
    vcp_n: Tuple[float, float],
    *,
    length_frac: float = 0.55,
) -> Tuple[Tuple[float, float], Tuple[float, float]]:
    """Vetor no tamanho atual, a partir da origem (centroide) rumo ao VCPn."""
    t = min(1.0, max(0.0, float(length_frac)))
    ox, oy = float(origin[0]), float(origin[1])
    dx = float(vcp_n[0]) - ox
    dy = float(vcp_n[1]) - oy
    return (ox, oy), (ox + t * dx, oy + t * dy)


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

    if frame is None or not detections:
        return frame

    out = frame.copy()
    frame_h, frame_w = out.shape[:2]
    hud_lines = None

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

        axis_cx, axis_cy = det.centroid
        vcp_n = getattr(det, "vcp_n", None)
        pick_cx, pick_cy = (vcp_n if vcp_n is not None else (axis_cx, axis_cy))
        axis_for_clamp = getattr(det, "angle_deg", None)
        if roi_enabled and roi and len(roi) == 4:
            pick_cx, pick_cy = clamp_centroid_for_pick(
                pick_cx,
                pick_cy,
                tuple(roi),
                angle_deg=axis_for_clamp if is_pick else None,
            )
        cx, cy = int(pick_cx), int(pick_cy)
        if is_pick:
            (vx0, vy0), (vx1, vy1) = vcp_vector_endpoints(
                (axis_cx, axis_cy), (pick_cx, pick_cy),
            )
            cv2.arrowedLine(
                out,
                (int(vx0), int(vy0)),
                (int(vx1), int(vy1)),
                VCP_MARKER_COLOR_BGR,
                3,
                tipLength=0.35,
            )
            cv2.circle(out, (cx, cy), 8, VCPN_COLOR_BGR, -1)

        overlay_angle = getattr(det, "heading_deg", None)
        if overlay_angle is None:
            overlay_angle = getattr(det, "angle_deg", None) if getattr(det, "has_orientation", False) else None
        if is_pick:
            hud_lines = format_centroid_metrics_lines(
                pick_cx,
                pick_cy,
                det.effective_area_px,
                overlay_angle,
                mm_per_px,
                ascii_safe=True,
                confidence=float(det.confidence),
                class_name=str(det.class_name),
            )

    if hud_lines:
        line_h = 18
        for i, line in enumerate(hud_lines):
            draw_overlay_label(out, line, (8, 22 + i * line_h), is_pick=True)

    return out


def draw_vcp_reference_on_frame(
    frame: np.ndarray,
    roi: Optional[Sequence[float]] = None,
    *,
    vcp_reference: str = "roi_top_mid",
) -> np.ndarray:
    """
    Marca no frame o ponto REF e a rosa local: N (norte, -Y) e L (leste, +X).

    Norte = topo da imagem (-Y). REF = mediana do lado superior do ROI,
    ou FOV (W/2, 0) se a referência for fov_top_mid / ROI ausente.
    """
    import cv2

    from detection.mask_geometry import resolve_vcp_reference

    if frame is None:
        return frame

    out = frame.copy()
    frame_h, frame_w = out.shape[:2]
    ref_xy = resolve_vcp_reference(
        vcp_reference,
        roi=roi,
        frame_wh=(float(frame_w), float(frame_h)),
    )
    rx = int(round(ref_xy[0]))
    ry = int(round(ref_xy[1]))
    rx = max(0, min(frame_w - 1, rx))
    ry = max(0, min(frame_h - 1, ry))

    color = VCP_REF_COLOR_BGR
    arrow_len = 36
    y_north = max(0, ry - arrow_len)
    x_east = min(frame_w - 1, rx + arrow_len)
    cv2.arrowedLine(out, (rx, ry + 8), (rx, y_north), color, 2, tipLength=0.35)
    cv2.arrowedLine(out, (rx + 8, ry), (x_east, ry), color, 2, tipLength=0.35)
    cv2.drawMarker(
        out, (rx, ry), color, markerType=cv2.MARKER_CROSS, markerSize=16, thickness=2,
    )
    cv2.circle(out, (rx, ry), 6, color, 2)

    n_origin = centroid_label_origin(rx, y_north, frame_h, frame_w, offset_x=8, offset_y=-4)
    draw_overlay_label(out, "N", n_origin, is_pick=False)
    l_origin = centroid_label_origin(x_east, ry, frame_h, frame_w, offset_x=8, offset_y=4)
    draw_overlay_label(out, "L", l_origin, is_pick=False)
    return out
