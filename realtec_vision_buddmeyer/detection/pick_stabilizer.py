# -*- coding: utf-8 -*-
"""Estabilização multi-frame do alvo de pick antes de emitir à FSM."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from detection.events import Detection


@dataclass
class PickStabilizer:
    """Exige N frames consecutivos com o mesmo alvo (centroide dentro de epsilon)."""

    stable_frames: int = 3
    centroid_epsilon_px: float = 15.0

    _streak: int = 0
    _anchor: Optional[Tuple[float, float]] = None
    _last_detection: Optional[Detection] = None

    def reset(self) -> None:
        self._streak = 0
        self._anchor = None
        self._last_detection = None

    def update(self, detection: Optional[Detection]) -> Optional[Detection]:
        """
        Actualiza estabilizador com a detecção pick do frame.

        Returns:
            Detection estável quando streak >= stable_frames; None caso contrário.
        """
        if detection is None:
            self.reset()
            return None

        cx, cy = detection.pick_xy
        if self._anchor is None:
            self._anchor = (float(cx), float(cy))
            self._streak = 1
            self._last_detection = detection
            return None

        ax, ay = self._anchor
        dist = ((float(cx) - ax) ** 2 + (float(cy) - ay) ** 2) ** 0.5
        if dist <= self.centroid_epsilon_px:
            self._streak += 1
            self._last_detection = detection
        else:
            self._anchor = (float(cx), float(cy))
            self._streak = 1
            self._last_detection = detection
            return None

        if self._streak >= self.stable_frames:
            return self._last_detection
        return None
