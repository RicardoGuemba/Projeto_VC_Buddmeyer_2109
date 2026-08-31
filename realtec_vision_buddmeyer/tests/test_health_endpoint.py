# -*- coding: utf-8 -*-
"""Testes do endpoint GET /health no servidor MJPEG."""

import http.client
import json
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streaming.mjpeg_server import MjpegServer


def _pick_port() -> int:
    import socket

    for p in range(19000, 19100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", p))
                return p
        except OSError:
            continue
    raise RuntimeError("no free port")


@pytest.fixture
def health_server():
    port = _pick_port()
    srv = MjpegServer(host="127.0.0.1", port=port, path="/stream")
    srv.set_health_provider(lambda: {
        "process": "running",
        "stream": "healthy",
        "cip": "connected",
        "fsm_state": "WAITING_AUTHORIZATION",
        "uptime_s": 1.0,
    })
    assert srv.start()
    time.sleep(0.15)
    yield srv, port
    srv.stop()


class TestHealthEndpoint:
    def test_health_returns_json(self, health_server):
        _srv, port = health_server
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
        conn.request("GET", "/health")
        resp = conn.getresponse()
        assert resp.status == 200
        body = json.loads(resp.read().decode("utf-8"))
        assert body["process"] == "running"
        assert body["fsm_state"] == "WAITING_AUTHORIZATION"
        conn.close()
