# -*- coding: utf-8 -*-
"""
Seleção do alvo de pick-and-place e conversão de métricas para unidades físicas.

Métodos disponíveis (configurável em detection.pick_selection_method):
- area_then_conf: maior área aparente (paralaxe/proximidade), desempate por confiança
- weighted_score: score ponderado confiança + área normalizada
- area_only: apenas maior área aparente
- confidence_only: apenas maior confiança
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from detection.events import Detection

from preprocessing.roi_manager import clamp_centroid_for_pick

PickSelectionMethod = Literal[
    "area_then_conf",
    "weighted_score",
    "area_only",
    "confidence_only",
]

PlcAreaUnit = Literal["cm2", "mm2", "px2"]

PICK_SELECTION_METHODS: tuple[str, ...] = (
    "area_then_conf",
    "weighted_score",
    "area_only",
    "confidence_only",
)

PLC_AREA_UNITS: tuple[str, ...] = ("cm2", "mm2", "px2")


def select_pick_target(
    detections: List["Detection"],
    method: PickSelectionMethod = "area_then_conf",
    confidence_weight: float = 1.0,
    area_weight: float = 1.0,
) -> Optional["Detection"]:
    """
    Seleciona a detecção alvo para pick-and-place.

    Returns:
        Detecção escolhida ou None se a lista estiver vazia.
    """
    if not detections:
        return None

    if method == "confidence_only":
        return max(detections, key=lambda d: float(d.confidence))

    if method == "area_only":
        return max(detections, key=lambda d: d.effective_area_px)

    if method == "area_then_conf":
        return max(
            detections,
            key=lambda d: (d.effective_area_px, float(d.confidence)),
        )

    # weighted_score (default legado de prioritize_area=True)
    max_area = max(d.effective_area_px for d in detections) or 1.0

    def _score(d: "Detection") -> float:
        return (
            confidence_weight * float(d.confidence)
            + area_weight * (d.effective_area_px / max_area)
        )

    return max(detections, key=_score)


def area_px_to_mm2(area_px: float, mm_per_px: float) -> float:
    """Converte área em px² para mm²."""
    return float(area_px) * (float(mm_per_px) ** 2)


def area_px_to_cm2(area_px: float, mm_per_px: float) -> float:
    """Converte área em px² para cm²."""
    return area_px_to_mm2(area_px, mm_per_px) / 100.0


def area_for_plc(
    area_px: float,
    mm_per_px: float,
    unit: PlcAreaUnit = "cm2",
) -> float:
    """Converte área em px² para a unidade configurada no CLP."""
    if unit == "px2":
        return float(area_px)
    if unit == "mm2":
        return area_px_to_mm2(area_px, mm_per_px)
    return area_px_to_cm2(area_px, mm_per_px)


def scale_detection_metrics(
    detection: "Detection",
    mm_per_px: float = 1.0,
    plc_area_unit: PlcAreaUnit = "cm2",
    roi_enabled: bool = False,
    roi: Optional[List[int]] = None,
) -> Dict[str, Any]:
    """
    Escala métricas de uma detecção para unidades físicas.

    Returns:
        Dict com centroid_mm, area_cm2, area_mm2, area_px, area_plc, confidence, etc.
    """
    mm_per_px = float(mm_per_px) or 1.0
    cx_px, cy_px = detection.centroid
    if roi_enabled and roi and len(roi) == 4:
        cx_px, cy_px = clamp_centroid_for_pick(
            cx_px,
            cy_px,
            tuple(roi),
            angle_deg=detection.angle_deg,
        )
    area_px = float(detection.effective_area_px)
    area_mm2 = area_px_to_mm2(area_px, mm_per_px)
    area_cm2 = area_mm2 / 100.0

    return {
        "class_name": detection.class_name,
        "confidence": float(detection.confidence),
        "centroid_px": (float(cx_px), float(cy_px)),
        "centroid_mm": (float(cx_px) * mm_per_px, float(cy_px) * mm_per_px),
        "angle_deg": float(detection.angle_deg) if detection.angle_deg is not None else None,
        "area_px": area_px,
        "area_mm2": area_mm2,
        "area_cm2": area_cm2,
        "area_plc": area_for_plc(area_px, mm_per_px, plc_area_unit),
        "plc_area_unit": plc_area_unit,
    }


def scale_all_detections(
    detections: List["Detection"],
    mm_per_px: float = 1.0,
    plc_area_unit: PlcAreaUnit = "cm2",
    roi_enabled: bool = False,
    roi: Optional[List[int]] = None,
) -> List[Dict[str, Any]]:
    """Escala métricas de todas as detecções."""
    return [
        scale_detection_metrics(
            d,
            mm_per_px=mm_per_px,
            plc_area_unit=plc_area_unit,
            roi_enabled=roi_enabled,
            roi=roi,
        )
        for d in detections
    ]


def migrate_prioritize_area(prioritize_area: bool) -> PickSelectionMethod:
    """Migra config legada prioritize_area para pick_selection_method."""
    return "weighted_score" if prioritize_area else "confidence_only"
