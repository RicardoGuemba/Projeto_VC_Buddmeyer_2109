#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Verificações pré-arranque para box PC (systemd ExecStartPre)."""

from __future__ import annotations

import socket
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config import get_settings


def _fail(msg: str) -> int:
    print(f"PREFLIGHT FAIL: {msg}", file=sys.stderr)
    return 1


def _ok(msg: str) -> None:
    print(f"PREFLIGHT OK: {msg}")


def check_model(settings) -> int:
    model_path = settings.get_models_path() / "model.safetensors"
    if not model_path.exists():
        return _fail(f"Modelo ausente: {model_path}")
    size = model_path.stat().st_size
    if size < 100_000_000:
        return _fail(f"model.safetensors suspeito ({size} bytes) — correr git lfs pull")
    _ok(f"modelo {model_path.name} ({size // 1_000_000} MB)")
    return 0


def check_logs_writable(settings) -> int:
    log_dir = settings.get_log_file_path().parent
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        probe = log_dir / ".preflight_write"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink(missing_ok=True)
    except OSError as e:
        return _fail(f"Sem escrita em {log_dir}: {e}")
    _ok(f"logs graváveis em {log_dir}")
    return 0


def check_plc_reachable(settings) -> int:
    if not settings.reliability.production_mode:
        _ok("production_mode=false — skip PLC reachability")
        return 0
    if settings.cip.simulated:
        _ok("cip.simulated=true — skip PLC reachability")
        return 0
    ip = settings.cip.ip
    port = settings.cip.port
    try:
        with socket.create_connection((ip, port), timeout=3.0):
            pass
    except OSError as e:
        return _fail(f"CLP inacessível em {ip}:{port} — {e}")
    _ok(f"CLP alcançável {ip}:{port}")
    return 0


def check_camera_hint(settings) -> int:
    source = settings.streaming.source_type
    if source == "gentl":
        cti = (settings.streaming.gentl_cti_path or "").strip()
        if not cti:
            return _fail("gentl_cti_path vazio — configure CTI GenTL")
        if not Path(cti).exists():
            return _fail(f"CTI GenTL não encontrado: {cti}")
        _ok(f"GenTL CTI {cti}")
        return 0
    if source == "usb":
        _ok("fonte USB — verificação de dispositivo em runtime")
        return 0
    _ok(f"fonte {source} — verificação específica em runtime")
    return 0


def main() -> int:
    config_path = ROOT / "config" / "config.yaml"
    settings = get_settings(config_path, reload=True)
    checks = (
        check_model,
        check_logs_writable,
        check_plc_reachable,
        check_camera_hint,
    )
    for fn in checks:
        code = fn(settings)
        if code != 0:
            return code
    print("PREFLIGHT: todas as verificações passaram")
    return 0


if __name__ == "__main__":
    sys.exit(main())
