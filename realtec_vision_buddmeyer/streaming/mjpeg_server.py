# -*- coding: utf-8 -*-
"""
Servidor HTTP MJPEG para streaming de vídeo via navegador.
URL simples para copiar e colar na barra de endereços (ex.: http://127.0.0.1:8080/stream).
Compatível com Windows, macOS e Linux.
"""

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional

import cv2
import numpy as np

from core.logger import get_logger

logger = get_logger("streaming.mjpeg")


def get_local_ip() -> str:
    """
    Obtém IP local da interface de rede (para exibir na URL).
    Usa múltiplos métodos para compatibilidade com Windows, macOS e Linux.
    """
    # Método 1: socket UDP para gateway (funciona em muitas redes)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(0.2)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        if ip and ip != "0.0.0.0":
            return ip
    except Exception:
        pass

    # Método 2: hostname (macOS, Linux)
    try:
        ip = socket.gethostbyname(socket.gethostname())
        if ip and ip != "127.0.0.1" and not ip.startswith("127."):
            return ip
    except Exception:
        pass

    # Método 3: localhost para acesso no mesmo PC
    return "127.0.0.1"


def is_port_available(host: str, port: int) -> bool:
    """Verifica se a porta está disponível para bind."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            s.bind((host, port))
            return True
    except OSError:
        return False


def normalize_http_path(path: Optional[str]) -> str:
    """Normaliza path HTTP do stream (sempre com leading slash)."""
    raw = (path or "").strip() or "/stream"
    return raw if raw.startswith("/") else f"/{raw}"


def _placeholder_jpeg(width: int = 640, height: int = 480) -> bytes:
    """JPEG estático enquanto a câmera ainda não enviou frames."""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    img[:] = (32, 32, 32)
    cv2.putText(
        img,
        "Aguardando camera...",
        (40, height // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        1.0,
        (200, 200, 200),
        2,
        cv2.LINE_AA,
    )
    ok, buf = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
    if not ok or buf is None:
        return b""
    return buf.tobytes()


BOUNDARY = "frame"
_PLACEHOLDER_JPEG = _placeholder_jpeg()


class MjpegHandler(BaseHTTPRequestHandler):
    """Handler HTTP que serve stream MJPEG (multipart/x-mixed-replace)."""

    # HTTP/1.0: stream sem Content-Length funciona melhor em browsers + http.client
    protocol_version = "HTTP/1.0"

    def log_message(self, format, *args):
        """Reduz logs de acesso (evita poluir console)."""
        logger.debug(
            "http_request",
            method=self.command,
            path=self.path,
            client=self.client_address[0],
        )

    @property
    def mjpeg(self) -> Optional["MjpegServer"]:
        return getattr(self.server, "mjpeg", None)

    def do_HEAD(self):
        """HEAD rápido (alguns browsers fazem prefetch)."""
        self._serve_path(body=False)

    def do_GET(self):
        """Responde GET com HTML viewer, stream MJPEG ou 404."""
        self._serve_path(body=True)

    def _serve_path(self, body: bool) -> None:
        mjpeg = self.mjpeg
        if mjpeg is None:
            self.send_error(500, "Server not configured")
            return

        path = self.path.split("?")[0].rstrip("/") or "/"
        stream_path = mjpeg.path.rstrip("/") or "/"

        # Favicon / assets: responde rápido para não bloquear o browser
        if path in ("/favicon.ico", "/robots.txt"):
            self.send_response(204)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            return

        # Página HTML com <img> — útil se o utilizador abrir a raiz
        if path == "/":
            html = (
                "<!DOCTYPE html><html><head><meta charset='utf-8'>"
                f"<title>Realtec Stream</title></head><body style='margin:0;background:#111;color:#eee;"
                "font-family:sans-serif;text-align:center'>"
                "<p style='padding:12px'>Stream MJPEG — "
                f"<a style='color:#8cf' href='{stream_path}'>{stream_path}</a></p>"
                f"<img src='{stream_path}' alt='stream' "
                "style='max-width:100%;height:auto;background:#000'/>"
                "</body></html>"
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "close")
            self.end_headers()
            if body:
                self.wfile.write(html)
            return

        if path != stream_path:
            self.send_error(404, f"Not Found: {self.path}")
            return

        if not body:
            self.send_response(200)
            self.send_header(
                "Content-Type",
                f'multipart/x-mixed-replace; boundary="{BOUNDARY}"',
            )
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            return

        self._stream_mjpeg(mjpeg)

    def _stream_mjpeg(self, mjpeg: "MjpegServer") -> None:
        """Loop multipart — envia placeholder até haver frames reais; ritmo contínuo."""
        self.send_response(200)
        self.send_header(
            "Content-Type",
            f'multipart/x-mixed-replace; boundary="{BOUNDARY}"',
        )
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        try:
            while mjpeg.is_running:
                frame = mjpeg.get_latest_frame()
                if frame is None:
                    data = _PLACEHOLDER_JPEG
                else:
                    ok, jpeg = cv2.imencode(
                        ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80]
                    )
                    if not ok or jpeg is None:
                        time.sleep(0.033)
                        continue
                    data = jpeg.tobytes()

                self.wfile.write(f"--{BOUNDARY}\r\n".encode())
                self.wfile.write(b"Content-Type: image/jpeg\r\n")
                self.wfile.write(f"Content-Length: {len(data)}\r\n\r\n".encode())
                self.wfile.write(data)
                self.wfile.write(b"\r\n")
                try:
                    self.wfile.flush()
                except Exception:
                    break
                time.sleep(0.066)  # ~15 fps
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception as e:
            logger.warning("mjpeg_stream_error", error=str(e))


class MjpegServer:
    """
    Servidor HTTP que serve stream MJPEG.
    Permite copiar URL e colar no navegador para visualizar o vídeo.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8080, path: str = "/stream"):
        self._host = host
        self._port = port
        self._path = normalize_http_path(path)
        self._server: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None
        self._latest_frame: Optional[np.ndarray] = None
        self._frame_seq: int = 0
        self._lock = threading.Lock()
        self._running = False

    @property
    def path(self) -> str:
        return self._path

    @property
    def port(self) -> int:
        return self._port

    @property
    def is_running(self) -> bool:
        return self._running

    def push_frame(self, frame: np.ndarray) -> None:
        """Atualiza o frame mais recente (thread-safe)."""
        with self._lock:
            self._latest_frame = frame.copy() if frame is not None else None
            self._frame_seq += 1

    def get_latest_frame(self) -> Optional[np.ndarray]:
        """Retorna o frame mais recente (thread-safe)."""
        with self._lock:
            if self._latest_frame is not None:
                return self._latest_frame.copy()
        return None

    def get_frame_seq(self) -> int:
        """Número de sequência do último push (para pacing do stream)."""
        with self._lock:
            return self._frame_seq
    def start(self) -> bool:
        """Inicia o servidor em thread separada (ThreadingHTTPServer)."""
        if self._running:
            return True
        if not is_port_available(self._host, self._port):
            logger.error(
                "mjpeg_port_in_use",
                port=self._port,
                hint="Porta em uso. Feche outro app ou mude a porta em Configuração → Saída.",
            )
            return False
        try:
            self._server = ThreadingHTTPServer((self._host, self._port), MjpegHandler)
            self._server.mjpeg = self  # type: ignore[attr-defined]
            self._server.daemon_threads = True
            self._thread = threading.Thread(target=self._serve, daemon=True)
            self._thread.start()
            self._running = True
            url = f"http://{get_local_ip()}:{self._port}{self._path}"
            logger.info("mjpeg_server_started", url=url, port=self._port)
            return True
        except OSError as e:
            logger.error("mjpeg_server_start_failed", error=str(e), port=self._port)
            return False

    def get_stream_url(self) -> str:
        """Retorna a URL completa do stream (para exibir ao usuário)."""
        return f"http://{get_local_ip()}:{self._port}{self._path}"

    def get_stream_urls(self) -> tuple[str, str]:
        """Retorna (url_localhost, url_rede) para exibição."""
        local = f"http://127.0.0.1:{self._port}{self._path}"
        net = f"http://{get_local_ip()}:{self._port}{self._path}"
        return (local, net)

    def verify_listening(self, timeout: float = 0.5) -> bool:
        """Verifica se o servidor está aceitando conexões em localhost."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                s.connect(("127.0.0.1", self._port))
                return True
        except OSError:
            return False

    def _serve(self) -> None:
        """Loop do servidor HTTP."""
        if self._server:
            self._server.serve_forever()

    def stop(self) -> None:
        """Para o servidor e limpa o frame."""
        if not self._running and self._server is None:
            with self._lock:
                self._latest_frame = None
            return
        self._running = False
        if self._server:
            try:
                self._server.shutdown()
            except Exception:
                pass
            try:
                self._server.server_close()
            except Exception:
                pass
            self._server = None
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        with self._lock:
            self._latest_frame = None
        logger.info("mjpeg_server_stopped", port=self._port)
