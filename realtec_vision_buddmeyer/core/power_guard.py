# -*- coding: utf-8 -*-
"""Inibição de sleep/screensaver durante operação industrial (Linux)."""

from __future__ import annotations

import platform
import subprocess
from typing import Optional

from core.logger import get_logger

logger = get_logger("core.power_guard")


class PowerGuard:
    """Mantém o sistema acordado enquanto Operação está activa."""

    def __init__(self) -> None:
        self._inhibit_proc: Optional[subprocess.Popen] = None
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def acquire(self) -> bool:
        """Bloqueia idle/sleep. Retorna True se algum mecanismo foi activado."""
        if self._active:
            return True
        if platform.system() != "Linux":
            logger.debug("power_guard_skipped_non_linux")
            return False

        try:
            self._inhibit_proc = subprocess.Popen(
                [
                    "systemd-inhibit",
                    "--what=idle:sleep:handle-lid-switch",
                    "--who=Realtec Vision Buddmeyer",
                    "--why=Industrial pick-and-place operation",
                    "--mode=block",
                    "sleep",
                    "infinity",
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._active = True
            logger.info("power_guard_acquired", mechanism="systemd-inhibit")
            self._try_x11_screensaver_off()
            return True
        except FileNotFoundError:
            logger.warning("power_guard_systemd_inhibit_missing")
            return self._try_x11_screensaver_off()
        except Exception as e:
            logger.warning("power_guard_acquire_failed", error=str(e))
            return False

    def release(self) -> None:
        """Liberta inibição de power management."""
        if self._inhibit_proc is not None:
            try:
                self._inhibit_proc.terminate()
                self._inhibit_proc.wait(timeout=2.0)
            except Exception as e:
                logger.warning("power_guard_release_failed", error=str(e))
                try:
                    self._inhibit_proc.kill()
                except Exception:
                    pass
            self._inhibit_proc = None
        self._active = False
        logger.info("power_guard_released")

    def _try_x11_screensaver_off(self) -> bool:
        """Fallback X11: desactiva screensaver e DPMS."""
        try:
            subprocess.run(
                ["xset", "s", "off", "-dpms"],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2.0,
            )
            logger.info("power_guard_x11_dpms_off")
            return True
        except Exception:
            return False


_power_guard_instance: Optional[PowerGuard] = None


def get_power_guard() -> PowerGuard:
    global _power_guard_instance
    if _power_guard_instance is None:
        _power_guard_instance = PowerGuard()
    return _power_guard_instance
