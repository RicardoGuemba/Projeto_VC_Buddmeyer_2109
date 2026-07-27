# -*- coding: utf-8 -*-
"""Testes unitários do servidor MJPEG HTTP."""

import sys
from pathlib import Path
import numpy as np
import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streaming.mjpeg_server import (
    MjpegServer,
    get_local_ip,
    is_port_available,
)


class TestMjpegServer:
    """Testes do MjpegServer."""

    def test_push_and_get_frame(self):
        """push_frame e get_latest_frame preservam o frame."""
        server = MjpegServer(host="127.0.0.1", port=0)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        frame[100:200, 100:200] = 255
        server.push_frame(frame)
        out = server.get_latest_frame()
        assert out is not None
        assert out.shape == frame.shape
        np.testing.assert_array_equal(out, frame)

    def test_get_latest_frame_none_when_empty(self):
        """get_latest_frame retorna None quando nenhum frame foi enviado."""
        server = MjpegServer(host="127.0.0.1", port=0)
        assert server.get_latest_frame() is None

    def test_stop_clears_frame(self):
        """stop() limpa o frame interno."""
        server = MjpegServer(host="127.0.0.1", port=0)
        server.push_frame(np.zeros((10, 10, 3), dtype=np.uint8))
        assert server.get_latest_frame() is not None
        server.stop()
        assert server.get_latest_frame() is None

    def test_start_stop(self):
        """start() e stop() funcionam sem erro."""
        server = MjpegServer(host="127.0.0.1", port=19998)
        assert server.start() is True
        server.stop()
        assert server._running is False

    def test_path_property(self):
        """path retorna o path configurado."""
        server = MjpegServer(host="0.0.0.0", port=8080, path="/video")
        assert server.path == "/video"
        server2 = MjpegServer(host="0.0.0.0", port=8080, path="stream")
        assert server2.path == "/stream"

    def test_get_local_ip_returns_string(self):
        """get_local_ip retorna string válida."""
        ip = get_local_ip()
        assert isinstance(ip, str)
        assert ip in ("127.0.0.1",) or ip.count(".") == 3

    def test_is_port_available_free(self):
        """Porta livre retorna True."""
        assert is_port_available("127.0.0.1", 0) is True  # 0 = qualquer porta livre

    def test_port_in_use_blocks_start(self):
        """Servidor não inicia se porta já estiver em uso."""
        import socket

        # Ocupa porta 19997
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 19997))
        try:
            server = MjpegServer(host="127.0.0.1", port=19997)
            assert server.start() is False
        finally:
            sock.close()

    def test_get_stream_url_after_start(self):
        """get_stream_url retorna URL http válida após start."""
        server = MjpegServer(host="127.0.0.1", port=19996)
        assert server.start() is True
        try:
            url = server.get_stream_url()
            assert url.startswith("http://")
            assert "19996" in url
            assert "/stream" in url
        finally:
            server.stop()

    def test_get_stream_urls_returns_both(self):
        """get_stream_urls retorna (localhost, rede)."""
        server = MjpegServer(host="127.0.0.1", port=19995)
        assert server.start() is True
        try:
            local, net = server.get_stream_urls()
            assert "127.0.0.1" in local
            assert "19995" in local
            assert net != local or get_local_ip() == "127.0.0.1"
        finally:
            server.stop()

    def test_verify_listening_after_start(self):
        """verify_listening retorna True quando servidor está ativo."""
        import time

        server = MjpegServer(host="127.0.0.1", port=19994)
        assert server.start() is True
        try:
            time.sleep(0.2)
            assert server.verify_listening() is True
        finally:
            server.stop()

    def test_get_stream_url_custom_path(self):
        """get_stream_url inclui path custom."""
        server = MjpegServer(host="127.0.0.1", port=19993, path="/cam")
        assert server.start() is True
        try:
            url = server.get_stream_url()
            assert "19993" in url
            assert url.endswith("/cam")
        finally:
            server.stop()

    def test_normalize_http_path_helper(self):
        from streaming.mjpeg_server import normalize_http_path

        assert normalize_http_path("x") == "/x"
        assert normalize_http_path("/y") == "/y"
