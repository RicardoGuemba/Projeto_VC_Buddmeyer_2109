# -*- coding: utf-8 -*-
"""Testes das flags de resiliência."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from config.settings import ReliabilitySettings, Settings


class TestAutoStartConfig:
    def test_reliability_defaults(self):
        r = ReliabilitySettings()
        assert r.auto_start_operation is False
        assert r.plc_sync_on_startup is True
        assert r.inhibit_power_management is True
        assert r.kiosk_fullscreen is False
        assert r.require_field_safety_tags is False

    def test_settings_loads_config_version(self):
        yaml = ROOT / "config" / "config.yaml"
        s = Settings.from_yaml(yaml)
        assert s.config_version >= 1
        assert s.reliability.plc_sync_on_startup is True

    def test_production_example_exists(self):
        example = ROOT / "config" / "config.production.yaml.example"
        assert example.exists()
        s = Settings.from_yaml(example)
        assert s.reliability.production_mode is True
        assert s.reliability.auto_start_operation is True
        assert s.reliability.require_field_safety_tags is True
        assert s.cip.max_retries == 0
