# -*- coding: utf-8 -*-
"""Cores e rótulos do overlay de detecção multi-objeto."""

# BGR (OpenCV / operation_page stream)
PICK_MASK_COLOR_BGR = (0, 255, 128)       # verde-água — objeto selecionado
OTHER_MASK_COLOR_BGR = (255, 210, 140)    # azul claro visível — demais objetos

# Qt QColor (video_widget): R, G, B
PICK_MASK_COLOR_QT = (0, 255, 128)
OTHER_MASK_COLOR_QT = (140, 210, 255)

# Opacidade do preenchimento da máscara (0.0–1.0 OpenCV; 0–255 Qt)
PICK_MASK_FILL_ALPHA = 0.40
OTHER_MASK_FILL_ALPHA = 0.45
PICK_MASK_FILL_ALPHA_QT = 150
OTHER_MASK_FILL_ALPHA_QT = 120

PICK_COORD_SUFFIX = " (pick)"

# Rótulos no vídeo (BGR) — contraste alto sobre máscaras e fundo variável
PICK_LABEL_COLOR_BGR = (220, 255, 255)    # branco esverdeado (pick)
OTHER_LABEL_COLOR_BGR = (255, 248, 235)   # branco quente (demais objetos)
LABEL_OUTLINE_COLOR_BGR = (0, 0, 0)

LABEL_FONT_SCALE = 0.68
LABEL_FONT_THICKNESS = 2
LABEL_OUTLINE_THICKNESS = 4


def is_pick_detection(detection, pick) -> bool:
    """Identifica o alvo de pick pela mesma instância na lista de detecções."""
    if pick is None or detection is None:
        return False
    return detection is pick


def format_centroid_metrics_summary(
    cx_px: float,
    cy_px: float,
    area_px: float,
    angle_deg,
    mm_per_px: float = 1.0,
    *,
    is_pick: bool = False,
) -> str:
    """Resumo compacto X, Y, área e ângulo junto ao centroide."""
    mm = float(mm_per_px) or 1.0
    cx_mm = float(cx_px) * mm
    cy_mm = float(cy_px) * mm
    area_cm2 = float(area_px) * (mm ** 2) / 100.0
    parts = [
        f"X:{cx_mm:.0f}",
        f"Y:{cy_mm:.0f}",
        f"A:{area_cm2:.1f}cm²",
    ]
    if angle_deg is not None:
        parts.append(f"∠{float(angle_deg):.0f}°")
    text = " ".join(parts)
    if is_pick:
        text += PICK_COORD_SUFFIX
    return text
