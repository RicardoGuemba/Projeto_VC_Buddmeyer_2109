# -*- coding: utf-8 -*-
"""
Testes funcionais do stream HTTP MJPEG (cliente HTTP real).

Valida multipart/x-mixed-replace, JPEG, path custom / 404, HTML raiz e threading.
"""

import http.client
import socket
import sys
import threading
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from streaming.mjpeg_server import MjpegServer, normalize_http_path


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _wait_listening(server: MjpegServer, timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if server.verify_listening():
            return
        time.sleep(0.05)
    raise AssertionError("server not listening")


def _read_some(conn: http.client.HTTPConnection, n: int = 4096):
    """Lê até n bytes do body (stream contínuo — não espera EOF)."""
    resp = conn.getresponse()
    status = resp.status
    content_type = resp.getheader("Content-Type", "")
    chunks = []
    remaining = n
    deadline = time.monotonic() + 2.0
    while remaining > 0 and time.monotonic() < deadline:
        chunk = resp.read(min(1024, remaining))
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
        if b"\xff\xd8" in b"".join(chunks):
            break
    return status, content_type, b"".join(chunks)


class TestMjpegHttpStreamFunctional:
    """Funcional: GET multipart + JPEG magic bytes."""

    def test_get_stream_returns_multipart_jpeg(self):
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/stream")
        assert server.start() is True
        try:
            _wait_listening(server)
            frame = np.zeros((64, 64, 3), dtype=np.uint8)
            frame[:, :] = (0, 128, 255)
            server.push_frame(frame)

            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
            conn.request("GET", "/stream")
            status, content_type, data = _read_some(conn)
            conn.close()

            assert status == 200
            assert "multipart/x-mixed-replace" in content_type
            assert "boundary=" in content_type
            assert b"\xff\xd8" in data
        finally:
            server.stop()

    def test_stream_sends_placeholder_without_camera_frame(self):
        """Sem push_frame, browser ainda recebe JPEG (placeholder)."""
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/stream")
        assert server.start() is True
        try:
            _wait_listening(server)
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
            conn.request("GET", "/stream")
            status, content_type, data = _read_some(conn)
            conn.close()
            assert status == 200
            assert "multipart" in content_type
            assert b"\xff\xd8" in data
        finally:
            server.stop()

    def test_root_returns_html_viewer(self):
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/stream")
        assert server.start() is True
        try:
            _wait_listening(server)
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2.0)
            conn.request("GET", "/")
            resp = conn.getresponse()
            body = resp.read()
            status = resp.status
            conn.close()
            assert status == 200
            assert b"<img" in body
            assert b"/stream" in body
        finally:
            server.stop()

    def test_wrong_path_returns_404(self):
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/stream")
        assert server.start() is True
        try:
            _wait_listening(server)
            conn = http.client.HTTPConnection("127.0.0.1", port, timeout=2.0)
            conn.request("GET", "/nope")
            resp = conn.getresponse()
            status = resp.status
            resp.read()
            conn.close()
            assert status == 404
        finally:
            server.stop()

    def test_custom_path_cam_only(self):
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/cam")
        assert server.start() is True
        try:
            _wait_listening(server)
            frame = np.zeros((32, 32, 3), dtype=np.uint8)
            server.push_frame(frame)

            conn_ok = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
            conn_ok.request("GET", "/cam")
            status_ok, content_type, data = _read_some(conn_ok)
            conn_ok.close()
            assert status_ok == 200
            assert "multipart" in content_type
            assert b"\xff\xd8" in data

            conn_bad = http.client.HTTPConnection("127.0.0.1", port, timeout=2.0)
            conn_bad.request("GET", "/stream")
            resp = conn_bad.getresponse()
            status_bad = resp.status
            resp.read()
            conn_bad.close()
            assert status_bad == 404
        finally:
            server.stop()

    def test_concurrent_favicon_does_not_block_stream(self):
        """ThreadingHTTPServer: favicon em paralelo não impede o stream."""
        port = _free_port()
        server = MjpegServer(host="127.0.0.1", port=port, path="/stream")
        assert server.start() is True
        try:
            _wait_listening(server)
            server.push_frame(np.zeros((16, 16, 3), dtype=np.uint8))

            results = {}

            def hold_stream():
                conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5.0)
                conn.request("GET", "/stream")
                status, ctype, data = _read_some(conn)
                results["stream"] = (status, ctype, data)
                conn.close()

            t = threading.Thread(target=hold_stream)
            t.start()
            time.sleep(0.15)

            conn_fav = http.client.HTTPConnection("127.0.0.1", port, timeout=2.0)
            conn_fav.request("GET", "/favicon.ico")
            resp = conn_fav.getresponse()
            fav_status = resp.status
            resp.read()
            conn_fav.close()
            t.join(timeout=5.0)

            assert fav_status == 204
            assert "stream" in results
            assert results["stream"][0] == 200
            assert b"\xff\xd8" in results["stream"][2]
        finally:
            server.stop()

    def test_normalize_http_path(self):
        assert normalize_http_path(None) == "/stream"
        assert normalize_http_path("") == "/stream"
        assert normalize_http_path("cam") == "/cam"
        assert normalize_http_path("/video") == "/video"
