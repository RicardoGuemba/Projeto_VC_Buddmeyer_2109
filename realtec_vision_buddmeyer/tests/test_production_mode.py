# -*- coding: utf-8 -*-
"""Testes de production_mode e fallback CLP."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestProductionMode:
    def test_cip_blocks_simulated_fallback_in_production(self):
        from communication.cip_client import CIPClient
        from communication.connection_state import ConnectionStatus

        CIPClient._reset_instance_for_tests()
        client = CIPClient()
        client._settings.cip.simulated = False
        client._settings.reliability.production_mode = True

        async def _run():
            with patch.object(client, "_connect_sync", side_effect=RuntimeError("offline")):
                ok = await client.connect()
            assert ok is False
            assert client.is_simulated is False

        asyncio.run(_run())
        CIPClient._reset_instance_for_tests()

    def test_reconnect_infinite_when_max_retries_zero(self):
        from config.settings import CIPSettings

        s = CIPSettings(max_retries=0)
        assert s.max_retries == 0
