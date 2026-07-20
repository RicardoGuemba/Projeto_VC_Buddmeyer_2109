#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Validação rápida: pytest handshake + smoke vídeo opcional."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    tests = [
        "tests/test_fsm_handshake.py",
        "tests/test_production_mode.py",
        "tests/test_safety_gate.py",
        "tests/test_pick_stabilizer.py",
        "tests/test_coordinate_transform.py",
        "tests/test_audit_store.py",
        "tests/test_stream_recovery.py",
    ]
    cmd = [sys.executable, "-m", "pytest", *tests, "-q"]
    print("[validate] running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=ROOT)
    if result.returncode != 0:
        return result.returncode

    video = ROOT / "videos" / "Colcha.mp4"
    if video.exists() or (ROOT.parent / "videos" / "Colcha.mp4").exists():
        smoke_cmd = [
            sys.executable,
            "-m",
            "scripts.smoke_test_segmentation",
            "--source",
            "video",
            "--video",
            "videos/Colcha.mp4",
            "--frames",
            "5",
        ]
        print("[validate] smoke:", " ".join(smoke_cmd))
        smoke = subprocess.run(smoke_cmd, cwd=ROOT)
        return smoke.returncode

    print("[validate] smoke skipped (video not found)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
