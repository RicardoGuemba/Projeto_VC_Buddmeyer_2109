# -*- coding: utf-8 -*-
"""
Módulo de detecção do sistema Buddmeyer Vision v2.0

Pipeline atual: instance segmentation (Mask2Former) com fallback para
object detection clássico (DETR/RT-DETR) via o mesmo `InferenceEngine`.
"""

from .inference_engine import InferenceEngine
from .model_loader import (
    ModelLoader,
    TASK_INSTANCE_SEGMENTATION,
    TASK_OBJECT_DETECTION,
)
from .postprocess import PostProcessor
from .segmentation_postprocess import SegmentationPostProcessor
from .mask_geometry import (
    MaskGeometry,
    VcpPick,
    compute_mask_geometry,
    compute_vcp_pick,
    major_axis_endpoints,
)
from .pick_selection import (
    PickSelectionMethod,
    select_pick_target,
    scale_detection_metrics,
)
from .events import BoundingBox, Detection, DetectionResult, DetectionEvent

__all__ = [
    "InferenceEngine",
    "ModelLoader",
    "PostProcessor",
    "SegmentationPostProcessor",
    "MaskGeometry",
    "VcpPick",
    "compute_mask_geometry",
    "compute_vcp_pick",
    "major_axis_endpoints",
    "BoundingBox",
    "Detection",
    "DetectionResult",
    "DetectionEvent",
    "PickSelectionMethod",
    "select_pick_target",
    "scale_detection_metrics",
    "TASK_INSTANCE_SEGMENTATION",
    "TASK_OBJECT_DETECTION",
]
