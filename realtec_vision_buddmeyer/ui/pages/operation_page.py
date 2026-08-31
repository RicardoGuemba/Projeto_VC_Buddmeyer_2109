# -*- coding: utf-8 -*-
"""
Página de Operação - Aba principal para operação do sistema.
"""

import asyncio
import time
from pathlib import Path
from typing import List, Optional

import numpy as np

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QComboBox, QLabel, QFileDialog, QSpinBox,
    QSplitter, QGroupBox, QCheckBox, QMessageBox,
)
from PySide6.QtCore import Qt, Slot, QTimer, Signal
from PySide6.QtGui import QFont, QKeySequence, QShortcut

from config import get_settings
from coordinate.transform import get_coordinate_transform
from core.logger import get_logger
from core.metrics import MetricsCollector
from core.power_guard import get_power_guard
from streaming import StreamManager
from streaming.mjpeg_server import MjpegServer, normalize_http_path
from detection import InferenceEngine
from detection.pick_selection import area_for_plc, select_pick_target
from communication import CIPClient
from control import RobotController

from ui.detection_overlay import draw_detection_masks_on_frame
from ui.widgets.video_widget import VideoWidget
from ui.widgets.status_panel import StatusPanel
from ui.widgets.event_console import EventConsole
from ui.widgets.gentl_camera_settings_dialog import GenTLCameraSettingsDialog


class OperationPage(QWidget):
    """
    Página de Operação.
    
    Contém:
    - Widget de vídeo com detecções
    - Painel de status lateral
    - Console de eventos
    - Controles de operação
    """
    
    model_preload_finished = Signal(bool)  # True = modelo carregado em segundo plano
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._logger = get_logger("ui.operation")
        self._settings = get_settings()
        self._stream_manager = StreamManager()
        self._inference_engine = InferenceEngine()
        self._cip_client = CIPClient()
        self._robot_controller = RobotController()
        
        self._is_running = False
        self._mjpeg_server: Optional[MjpegServer] = None
        
        self._last_best_detection = None
        self._last_base_frame: Optional[np.ndarray] = None
        self._last_overlay_result = None
        self._detection_count = 0  # Contador total de detecções
        self._error_count = 0  # Contador total de erros
        
        # Carregamento do modelo na GUI thread (PyTorch/MPS não é estável em QThread)
        self._model_loading = False
        self._shutdown_requested = False
        self._pending_start_source_label: Optional[str] = None
        self._roi_persist_timer = QTimer(self)
        self._roi_persist_timer.setSingleShot(True)
        self._roi_persist_timer.timeout.connect(self._persist_roi_to_config)
        
        self._setup_ui()
        self._sync_combo_to_settings()
        self._connect_signals()
        self._setup_shortcuts()
    
    def _setup_ui(self) -> None:
        """Configura a interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Splitter principal (horizontal)
        main_splitter = QSplitter(Qt.Horizontal)
        
        # Área central (vídeo + console)
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.setContentsMargins(0, 0, 0, 0)
        central_layout.setSpacing(8)
        
        # Widget de vídeo
        self._video_widget = VideoWidget()
        self._video_widget.set_show_overlay(False)
        self._video_widget.double_clicked.connect(self._toggle_fullscreen)
        central_layout.addWidget(self._video_widget, stretch=3)
        
        # Legenda da fonte atual (abaixo do vídeo)
        self._source_caption = QLabel()
        self._source_caption.setStyleSheet("color: #c5c9ce; font-size: 11px; padding: 2px 0;")
        self._source_caption.setAlignment(Qt.AlignCenter)
        central_layout.addWidget(self._source_caption)
        
        # Console de eventos
        console_group = QGroupBox("Eventos")
        console_group.setStyleSheet("""
            QGroupBox {
                color: #e5e7eb;
                border: 1px solid #1b3a69;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
            }
        """)
        console_layout = QVBoxLayout(console_group)
        self._event_console = EventConsole()
        self._event_console.setMinimumHeight(140)
        console_layout.addWidget(self._event_console)
        central_layout.addWidget(console_group, stretch=1)
        
        main_splitter.addWidget(central_widget)
        
        # Painel de status (direita)
        self._status_panel = StatusPanel()
        main_splitter.addWidget(self._status_panel)
        
        # Proporções do splitter
        main_splitter.setSizes([800, 280])
        
        layout.addWidget(main_splitter, stretch=1)
        
        # Barra de status da etapa atual (pick-and-place)
        status_bar = QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #14284c;
                border: 1px solid #1b3a69;
                border-radius: 4px;
            }
        """)
        status_bar.setMinimumHeight(44)
        status_bar_layout = QHBoxLayout(status_bar)
        status_bar_layout.setContentsMargins(12, 8, 12, 8)
        status_label = QLabel("Status atual:")
        status_label.setStyleSheet("color: #c5c9ce; font-size: 11px; font-weight: bold;")
        status_bar_layout.addWidget(status_label)
        self._status_step_label = QLabel("—")
        self._status_step_label.setStyleSheet("color: #26477e; font-weight: bold; font-size: 11px;")
        self._status_step_label.setWordWrap(True)
        status_bar_layout.addWidget(self._status_step_label, stretch=1)
        layout.addWidget(status_bar)
        
        # Barra de controles (inferior)
        controls_frame = QFrame()
        controls_frame.setStyleSheet("""
            QFrame {
                background-color: #14284c;
                border: 1px solid #1b3a69;
                border-radius: 4px;
            }
        """)
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(12)
        
        # Seletor de fonte
        controls_layout.addWidget(QLabel("Fonte:"))
        
        self._source_combo = QComboBox()
        self._source_combo.setMinimumWidth(180)
        self._source_combo.addItems([
            "Câmera USB",
            "Câmera GenTL (Omron Sentech)",
        ])
        self._source_combo.currentIndexChanged.connect(self._on_source_changed)
        controls_layout.addWidget(self._source_combo)
        
        self._usb_index_spin = QSpinBox()
        self._usb_index_spin.setRange(0, 10)
        self._usb_index_spin.setToolTip("Índice da câmera USB (0 = primeira)")
        self._usb_index_spin.valueChanged.connect(self._on_usb_index_changed)
        self._usb_index_label = QLabel("Índice:")
        controls_layout.addWidget(self._usb_index_label)
        controls_layout.addWidget(self._usb_index_spin)
        
        self._gentl_cti_btn = QPushButton("Selecionar CTI...")
        self._gentl_cti_btn.setToolTip("Selecionar arquivo CTI GenTL (ex.: Omron Sentech)")
        self._gentl_cti_btn.clicked.connect(self._select_gentl_cti_file)
        self._gentl_cti_btn.setVisible(False)
        controls_layout.addWidget(self._gentl_cti_btn)

        self._gentl_settings_btn = QPushButton("Ajustes da câmera...")
        self._gentl_settings_btn.setToolTip("Abrir tela de ajustes da câmera GenTL (gain, exposição). Requer stream ativo.")
        self._gentl_settings_btn.clicked.connect(self._open_gentl_camera_settings)
        self._gentl_settings_btn.setVisible(False)
        controls_layout.addWidget(self._gentl_settings_btn)
        
        controls_layout.addStretch()
        
        # Botões de controle
        self._play_btn = QPushButton("▶ Iniciar")
        self._play_btn.setMinimumWidth(100)
        self._play_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._play_btn.clicked.connect(self._start_system)
        controls_layout.addWidget(self._play_btn)
        
        self._pause_btn = QPushButton("⏸ Pausar")
        self._pause_btn.setMinimumWidth(100)
        self._pause_btn.setEnabled(False)
        self._pause_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: black;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
            QPushButton:disabled {
                background-color: #6c757d;
                color: white;
            }
        """)
        self._pause_btn.clicked.connect(self._toggle_pause)
        controls_layout.addWidget(self._pause_btn)
        
        self._stop_btn = QPushButton("⏹ Parar")
        self._stop_btn.setMinimumWidth(100)
        self._stop_btn.setEnabled(False)
        self._stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._stop_btn.clicked.connect(self._stop_system)
        controls_layout.addWidget(self._stop_btn)
        
        # Separador visual
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("background-color: #1b3a69;")
        controls_layout.addWidget(sep)
        
        # Autorizar envio ao CLP (modo manual, apos deteccao)
        self._authorize_send_btn = QPushButton("Autorizar envio ao CLP")
        self._authorize_send_btn.setMinimumWidth(140)
        self._authorize_send_btn.setEnabled(False)
        self._authorize_send_btn.setVisible(False)
        self._authorize_send_btn.setStyleSheet("""
            QPushButton {
                background-color: #26477e;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b3a69;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._authorize_send_btn.setToolTip("Objeto detectado. Clique para enviar coordenadas ao CLP e iniciar o ciclo.")
        self._authorize_send_btn.clicked.connect(self._authorize_send_to_plc)
        controls_layout.addWidget(self._authorize_send_btn)
        
        # Controles de ciclo pick-and-place
        self._continuous_cb = QCheckBox("Modo Continuo")
        self._continuous_cb.setChecked(False)
        self._continuous_cb.setToolTip(
            "Marcado: ciclos de pick-and-place executam automaticamente.\n"
            "Desmarcado: aguarda 'Novo Ciclo' ao final de cada ciclo."
        )
        self._continuous_cb.stateChanged.connect(self._on_cycle_mode_changed)
        controls_layout.addWidget(self._continuous_cb)
        
        self._new_cycle_btn = QPushButton("Novo Ciclo")
        self._new_cycle_btn.setMinimumWidth(100)
        self._new_cycle_btn.setEnabled(False)
        self._new_cycle_btn.setStyleSheet("""
            QPushButton {
                background-color: #26477e;
                color: white;
                font-weight: bold;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1b3a69;
            }
            QPushButton:disabled {
                background-color: #6c757d;
            }
        """)
        self._new_cycle_btn.setToolTip("Autoriza o proximo ciclo de pick-and-place (modo manual)")
        self._new_cycle_btn.clicked.connect(self._authorize_new_cycle)
        controls_layout.addWidget(self._new_cycle_btn)
        
        controls_layout.addStretch()
        
        self._exit_btn = QPushButton("Sair")
        self._exit_btn.setToolTip("Encerra o sistema (Cmd+Q no macOS)")
        self._exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self._exit_btn.clicked.connect(self._on_exit_clicked)
        controls_layout.addWidget(self._exit_btn)
        
        layout.addWidget(controls_frame)
    
    def _load_roi_from_settings(self) -> None:
        """Carrega ROI das configurações para o painel."""
        from config.settings import DEFAULT_ROI_QUARTER_AREA

        s = self._settings.preprocess
        enabled = bool(getattr(s, "roi_enabled", True))
        if s.roi and len(s.roi) == 4:
            self._status_panel.set_roi(enabled, s.roi[0], s.roi[1], s.roi[2], s.roi[3])
        else:
            x, y, w, h = DEFAULT_ROI_QUARTER_AREA
            self._status_panel.set_roi(True, x, y, w, h)
            s.roi = list(DEFAULT_ROI_QUARTER_AREA)
            s.roi_enabled = True
        self._refresh_centroid_display()

    def _persist_roi_to_config(self) -> None:
        """Grava dimensões ROI e estado de confinamento em config.yaml."""
        config_path = self._settings.get_base_path() / "config" / "config.yaml"
        self._settings.to_yaml(config_path)
        self._logger.info(
            "roi_persisted",
            roi=self._settings.preprocess.roi,
            roi_enabled=self._settings.preprocess.roi_enabled,
        )
    
    def _refresh_centroid_display(self) -> None:
        """Atualiza exibição do centroide no painel (usa calibração atual)."""
        if self._last_best_detection is not None:
            self._status_panel.update_detection(self._last_best_detection)
    
    def _on_roi_changed(self) -> None:
        """Atualiza settings e persiste ROI como default quando dimensões mudam."""
        enabled, coords = self._status_panel.get_roi()
        self._settings.preprocess.roi = list(coords)
        self._settings.preprocess.roi_enabled = enabled
        self._refresh_centroid_display()
        self._roi_persist_timer.start(500)
    
    def _sync_combo_to_settings(self) -> None:
        """Sincroniza o combo de fonte com o source_type do settings."""
        source_type_map = {"usb": 0, "gentl": 1}
        current_source = self._settings.streaming.source_type
        if current_source not in source_type_map:
            current_source = "usb"
            self._settings.streaming.source_type = "usb"
        combo_index = source_type_map[current_source]
        self._source_combo.setCurrentIndex(combo_index)
        self._usb_index_spin.setValue(self._settings.streaming.usb_camera_index)
        self._on_source_changed(combo_index)
    
    def _on_usb_index_changed(self, value: int) -> None:
        """Actualiza índice USB em memória e legenda."""
        self._settings.streaming.usb_camera_index = value
        if self._source_combo.currentIndex() == 0:
            self._update_source_caption()
    
    def _update_source_caption(self) -> None:
        """Atualiza a legenda da fonte atual (abaixo do vídeo)."""
        idx = self._source_combo.currentIndex()
        if idx == 0:
            cam = self._settings.streaming.usb_camera_index
            self._source_caption.setText(f"Fonte: Câmera USB (índice {cam})")
        else:
            cti = (self._settings.streaming.gentl_cti_path or "").strip()
            if cti:
                self._source_caption.setText(f"Fonte: Câmera GenTL — {Path(cti).name}")
            else:
                self._source_caption.setText(
                    "Fonte: Câmera GenTL (Omron Sentech) — use 'Selecionar CTI...'"
                )
    
    def _connect_signals(self) -> None:
        """Conecta os sinais."""
        # Stream (ROI aplicado em _on_frame_available antes de exibir e inferir)
        self._stream_manager.frame_info_available.connect(self._on_frame_available)
        self._stream_manager.stream_started.connect(self._on_stream_started)
        self._stream_manager.stream_stopped.connect(self._on_stream_stopped)
        self._stream_manager.stream_error.connect(self._on_stream_error)
        
        # Inferência
        self._inference_engine.detection_result.connect(self._on_detection_result)
        self._inference_engine.detection_event.connect(self._on_detection)
        
        # CIP
        self._cip_client.state_changed.connect(self._status_panel.set_connection_state)
        self._cip_client.connection_error.connect(self._on_cip_error)
        
        # Robô
        self._robot_controller.state_changed.connect(self._status_panel.set_robot_state)
        self._robot_controller.state_changed.connect(self._on_robot_state_changed)
        self._robot_controller.cycle_completed.connect(self._on_cycle_completed)
        self._robot_controller.error_occurred.connect(self._on_robot_error)
        self._robot_controller.cycle_step.connect(self._on_cycle_step)
        self._robot_controller.cycle_summary.connect(self._on_cycle_summary)
        
        # ROI (persiste em settings; Salvar Config na aba Configuração persiste no arquivo)
        self._status_panel.roi_changed.connect(self._on_roi_changed)
        self._load_roi_from_settings()
        
        # Timer para atualizar FPS
        self._fps_timer = QTimer(self)
        self._fps_timer.timeout.connect(self._update_fps)
        self._fps_timer.start(500)
    
    def _setup_shortcuts(self) -> None:
        """Configura atalhos de teclado."""
        # F5 - Iniciar
        start_shortcut = QShortcut(QKeySequence("F5"), self)
        start_shortcut.activated.connect(self._start_system)
        
        # F6 - Parar
        stop_shortcut = QShortcut(QKeySequence("F6"), self)
        stop_shortcut.activated.connect(self._stop_system)
        
        # F11 - Fullscreen
        fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
        fullscreen_shortcut.activated.connect(self._toggle_fullscreen)
    
    @Slot()
    def _start_system(self) -> None:
        """Inicia o sistema."""
        if self._is_running:
            return
        
        # Determina fonte selecionada na UI (câmera USB ou GenTL)
        source_types = ["usb", "gentl"]
        source_labels = ["Câmera USB", "Câmera GenTL (Omron Sentech)"]
        source_index = self._source_combo.currentIndex()
        source_type = source_types[source_index]
        
        self._event_console.add_info(
            f"Iniciando sistema com fonte: {source_labels[source_index]}..."
        )
        self._logger.info("start_system_requested", source_type=source_type)
        
        # Atualiza fonte em memória
        self._settings.streaming.source_type = source_type
        if source_type == "usb":
            self._settings.streaming.usb_camera_index = self._usb_index_spin.value()
        
        self._stream_manager.clear_shutdown_guard()
        
        # Validação prévia para GenTL (arquivo CTI)
        if source_type == "gentl":
            cti_path_str = (self._settings.streaming.gentl_cti_path or "").strip()
            if not cti_path_str:
                self._event_console.add_error(
                    "Arquivo CTI GenTL não configurado. Use o botão 'Selecionar CTI...' para escolher "
                    "o arquivo .cti (ex.: Omron Sentech) ou configure na aba Configuração."
                )
                self._logger.error("gentl_cti_empty_on_start")
                return
            cti_path = Path(cti_path_str)
            if not cti_path.exists():
                self._event_console.add_error(
                    f"Arquivo CTI não encontrado:\n{cti_path}\n\n"
                    "Use 'Selecionar CTI...' para escolher o arquivo correto."
                )
                self._logger.error("gentl_cti_not_found_on_start", path=str(cti_path))
                return
        
        # Atualiza configuração do StreamManager com os parâmetros da fonte
        if source_type == "usb":
            self._stream_manager.change_source(
                source_type=source_type,
                camera_index=self._settings.streaming.usb_camera_index,
            )
        else:
            self._stream_manager.change_source(
                source_type=source_type,
                gentl_cti_path=self._settings.streaming.gentl_cti_path,
                gentl_device_index=self._settings.streaming.gentl_device_index,
            )
        
        # Inicia stream (usa configurações em memória, NÃO recarrega do YAML)
        if not self._stream_manager.start():
            self._event_console.add_error(
                f"Falha ao iniciar stream ({source_labels[source_index]})"
            )
            return
        
        self._event_console.add_info(
            f"Stream iniciado: {source_labels[source_index]}"
        )
        
        source_label = source_labels[source_index]
        
        # Carrega modelo na GUI thread (agendado; evita crash MPS/CUDA em QThread)
        if not self._inference_engine.is_model_loaded:
            if self._model_loading:
                self._pending_start_source_label = source_label
                self._play_btn.setText("Carregando modelo...")
                self._play_btn.setEnabled(False)
                return
            self._event_console.add_info(
                "Carregando modelo de detecção... (pode levar 1–2 min na primeira vez)"
            )
            self._play_btn.setText("Carregando modelo...")
            self._play_btn.setEnabled(False)
            self._schedule_model_load(pending_start_label=source_label)
            return
        
        self._finish_start_system_after_model(source_label)
    
    def _finish_start_system_after_model(self, source_label: str) -> None:
        """Conclui a inicialização após o modelo estar carregado (inicia inferência, CLP, atualiza UI)."""
        if not self._inference_engine.start():
            self._event_console.add_error("Falha ao iniciar inferência")
            self._stream_manager.stop()
            return
        self._event_console.add_info("Inferência iniciada - detecção ativa")
        cycle_mode = "continuous" if self._continuous_cb.isChecked() else "manual"
        self._robot_controller.set_cycle_mode(cycle_mode)
        asyncio.create_task(self._connect_plc_and_start_robot())
        self._is_running = True

        self.apply_output_stream_settings(from_system_start=True)

        if getattr(self._settings.reliability, "inhibit_power_management", True):
            if get_power_guard().acquire():
                self._event_console.add_info("Protecção sleep/screensaver activa")

        self._update_ui_state()
        self._event_console.add_success(f"Sistema iniciado [{source_label}]")
        self._status_panel.set_system_status("RUNNING")

    def apply_output_stream_settings(self, from_system_start: bool = False) -> None:
        """
        Aplica output.rtsp_enabled / http_port / http_path ao servidor MJPEG.

        O stream pode correr sem Operação ▶ Iniciar (placeholder até haver câmera).
        """
        enabled = bool(self._settings.output.rtsp_enabled)
        port = int(self._settings.output.http_port)
        path = normalize_http_path(self._settings.output.http_path)

        if not enabled:
            if self._mjpeg_server is not None:
                self._stop_mjpeg_server()
                self._event_console.add_info("Stream HTTP desligado")
            return

        needs_restart = (
            self._mjpeg_server is None
            or self._mjpeg_server.port != port
            or self._mjpeg_server.path != path
        )
        if not needs_restart:
            return

        self._stop_mjpeg_server()
        self._start_mjpeg_server(port=port, path=path)

    def restore_output_stream_if_configured(self) -> None:
        """Re-liga o stream HTTP ao abrir o app se já estava activo (Copiar URL anterior)."""
        if self._settings.output.rtsp_enabled:
            self.apply_output_stream_settings()

    def _start_mjpeg_server(self, port: int, path: str) -> None:
        """Inicia MjpegServer e reporta URL no console."""
        self._mjpeg_server = MjpegServer(
            host="0.0.0.0",
            port=port,
            path=path,
        )
        self._mjpeg_server.set_health_provider(self._build_health_payload)
        if self._mjpeg_server.start():
            deadline = time.monotonic() + 0.5
            while time.monotonic() < deadline:
                if self._mjpeg_server.verify_listening(timeout=0.05):
                    break
                time.sleep(0.05)
            local_url, net_url = self._mjpeg_server.get_stream_urls()
            self._event_console.add_success(f"Stream HTTP: {net_url}")
            self._event_console.add_info(
                f"Mesmo PC: {local_url} | Outros dispositivos: {net_url}"
            )
            self._event_console.add_info(
                "ERR_CONNECTION_REFUSED? Permita o app no firewall "
                f"(porta {port})"
            )
        else:
            self._mjpeg_server = None
            self._event_console.add_error(
                f"Porta {port} em uso. "
                "Feche outro app ou mude em Configuração → Saída."
            )

    def _stop_mjpeg_server(self) -> None:
        """Para e limpa o servidor MJPEG se existir."""
        if self._mjpeg_server is None:
            return
        try:
            self._mjpeg_server.stop()
        except Exception as e:
            self._logger.warning("mjpeg_stop_error", error=str(e))
        self._mjpeg_server = None
    
    @Slot(bool)
    def _on_model_load_finished(self, success: bool) -> None:
        """Chamado quando o carregamento do modelo termina."""
        if self._shutdown_requested:
            return
        label = self._pending_start_source_label
        self._pending_start_source_label = None
        self._play_btn.setText("▶ Iniciar")
        self._play_btn.setEnabled(True)
        if label is not None:
            if not success:
                self._event_console.add_error("Falha ao carregar modelo")
                self._stream_manager.stop()
                return
            self._event_console.add_info("Modelo carregado.")
            self._finish_start_system_after_model(label)
        else:
            self.model_preload_finished.emit(success)

    def _schedule_model_load(self, pending_start_label: Optional[str] = None) -> None:
        """
        Agenda carregamento do modelo na GUI thread.

        PyTorch (especialmente MPS no macOS) não é seguro quando o modelo é
        instanciado/movido para device numa QThread secundária.
        """
        if self._inference_engine.is_model_loaded:
            if pending_start_label is not None:
                self._finish_start_system_after_model(pending_start_label)
            else:
                self.model_preload_finished.emit(True)
            return
        if self._model_loading:
            if pending_start_label is not None:
                self._pending_start_source_label = pending_start_label
            return
        self._model_loading = True
        if pending_start_label is not None:
            self._pending_start_source_label = pending_start_label
        QTimer.singleShot(0, self._run_model_load_on_main_thread)

    def _run_model_load_on_main_thread(self) -> None:
        """Executa load_model na thread principal do Qt."""
        if not self._model_loading or self._shutdown_requested:
            self._model_loading = False
            return
        try:
            success = self._inference_engine.load_model()
        except Exception as e:
            self._logger.error("model_load_on_main_thread_failed", error=str(e))
            success = False
        self._model_loading = False
        self._on_model_load_finished(success)

    def _build_health_payload(self) -> dict:
        """Payload JSON para GET /health."""
        stream_status = self._stream_manager.get_status()
        cip_status = self._cip_client.get_status()
        return {
            "process": "running" if self._is_running else "stopped",
            "stream": stream_status.get("health", {}).get("status", "unknown"),
            "cip": cip_status.get("status", "unknown"),
            "fsm_state": self._robot_controller.state.value,
            "uptime_s": round(self._mjpeg_server.uptime_s, 1) if self._mjpeg_server else 0.0,
        }

    def auto_start_if_configured(self) -> None:
        """Inicia Operação automaticamente quando auto_start_operation está activo."""
        if not getattr(self._settings.reliability, "auto_start_operation", False):
            return
        if self._is_running:
            return
        self._logger.info("auto_start_operation_triggered")
        self._event_console.add_info("Auto-start: iniciando Operação...")
        self._start_system()

    def start_model_preload(self) -> None:
        """Pré-carrega o modelo após abrir o app (na GUI thread)."""
        if self._inference_engine.is_model_loaded or self._model_loading:
            return
        self._schedule_model_load(pending_start_label=None)

    def shutdown(self) -> None:
        """Libera recursos ao fechar a aplicação."""
        self._shutdown_requested = True
        self._model_loading = False
        self._pending_start_source_label = None
        if hasattr(self, "_fps_timer"):
            self._fps_timer.stop()
        self._stream_manager.prepare_shutdown()
        self._cip_client._exiting = True
        if self._mjpeg_server is not None:
            self._mjpeg_server.set_health_provider(None)
        if self._is_running:
            self._stop_system(for_exit=True)
        else:
            self._robot_controller.stop()
        get_power_guard().release()
        self._stop_mjpeg_server()
        self._cip_client.shutdown_for_exit()

    async def _connect_plc_and_start_robot(self) -> None:
        """Conecta ao CLP. Em production_mode falha se CLP real indisponível."""
        production = getattr(self._settings.reliability, "production_mode", False)
        try:
            await self._cip_client.connect()

            if self._cip_client.is_simulated:
                if production:
                    self._event_console.add_error(
                        "CLP real indisponível em production_mode. FSM não iniciada."
                    )
                    self._logger.error("plc_unavailable_production_mode")
                    return
                self._event_console.add_warning(
                    "CLP real nao alcancavel - operando em modo SIMULADO.\n"
                    "Robo virtual ativo: pick-and-place simulado com delays."
                )
                self._logger.warning("plc_fallback_to_simulated")
            else:
                self._event_console.add_success(
                    f"Conectado ao CLP real ({self._settings.cip.ip}:{self._settings.cip.port})"
                )

            try:
                await self._cip_client.set_vision_ready(True)
                self._event_console.add_info("VisionReady = True enviado ao CLP")
            except Exception as e:
                self._logger.warning("failed_to_set_vision_ready", error=str(e))

            initial_state = await self._robot_controller.prepare_plc_recovery_state()
            self._robot_controller.start(initial_state=initial_state)
            if initial_state is not None:
                self._event_console.add_info(
                    f"Recovery CLP: FSM sincronizada → {initial_state.value}"
                )
            mode_label = "continuo" if self._continuous_cb.isChecked() else "manual"
            self._event_console.add_info(
                f"Controlador de robo iniciado (modo {mode_label})"
            )

        except Exception as e:
            if production:
                self._event_console.add_error(
                    f"Falha ao conectar CLP (production_mode): {e}"
                )
                self._logger.error("plc_connect_exception_production", error=str(e))
                return
            self._event_console.add_warning(
                f"Erro ao conectar CLP: {e}\n"
                f"Sistema operando em modo simulado."
            )
            self._logger.error("plc_connect_exception", error=str(e))
            if not self._cip_client.is_connected:
                await self._cip_client._connect_simulated()
            initial_state = await self._robot_controller.prepare_plc_recovery_state()
            self._robot_controller.start(initial_state=initial_state)

    async def _connect_plc(self) -> None:
        """Conecta ao CLP."""
        try:
            await self._cip_client.connect()
            self._event_console.add_success("Conectado ao CLP")
        except Exception as e:
            self._event_console.add_warning(f"CLP em modo simulado: {e}")
    
    async def _shutdown_plc_connection(self) -> None:
        """Seta VisionReady = False e desconecta do CLP."""
        try:
            if self._cip_client._state.is_connected:
                await self._cip_client.set_vision_ready(False)
                self._logger.info("vision_ready_false_sent")
        except Exception as e:
            self._logger.warning("failed_to_set_vision_ready_false", error=str(e))
        finally:
            await self._cip_client.disconnect()
    
    @Slot()
    def _stop_system(self, for_exit: bool = False) -> None:
        """Para o sistema de forma ordenada e estável."""
        if not self._is_running:
            return

        self._is_running = False
        self._last_best_detection = None
        self._last_base_frame = None
        self._last_overlay_result = None

        self._event_console.add_info("Parando sistema...")

        # Mantém stream HTTP se foi activado (Copiar URL) — browser continua a funcionar
        if not for_exit and not self._settings.output.rtsp_enabled:
            self._stop_mjpeg_server()

        worker_timeout = 400 if for_exit else 5000
        self._robot_controller.stop()
        self._inference_engine.stop(timeout_ms=worker_timeout)
        self._stream_manager.stop(timeout_ms=worker_timeout)
        get_power_guard().release()

        if not for_exit:
            try:
                self._run_shutdown_plc_sync()
            except Exception as e:
                self._logger.warning("shutdown_plc_error", error=str(e))

        self._update_ui_state()
        self._pause_btn.setText("⏸ Pausar")
        self._video_widget.clear()

        self._event_console.add_info("Sistema parado")
        self._status_panel.set_system_status("STOPPED")

    def _run_shutdown_plc_sync(self) -> None:
        """Executa desconexão do CLP sem bloquear (evita deadlock ao sair)."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                return
            # Fire-and-forget: agenda desconexão sem esperar (evita nested.exec() que
            # causava travamento ao clicar em Sair)
            asyncio.ensure_future(self._shutdown_plc_connection())
        except RuntimeError:
            pass
        except Exception as e:
            self._logger.warning("shutdown_plc_sync_error", error=str(e))
    
    @Slot()
    def _toggle_pause(self) -> None:
        """Alterna pause/resume do stream e da inferência."""
        if not self._is_running:
            return
        
        if self._stream_manager._worker and self._stream_manager._worker._paused:
            # Resumir
            self._stream_manager.resume()
            self._inference_engine.start()
            self._pause_btn.setText("⏸ Pausar")
            self._event_console.add_info("Sistema retomado")
            self._status_panel.set_system_status("RUNNING")
            self._logger.info("system_resumed")
        else:
            # Pausar
            self._stream_manager.pause()
            self._inference_engine.stop()
            self._pause_btn.setText("▶ Retomar")
            self._event_console.add_info("Sistema pausado")
            self._status_panel.set_system_status("PAUSED")
            self._logger.info("system_paused")
    
    def _update_ui_state(self) -> None:
        """Atualiza estado da UI."""
        self._play_btn.setEnabled(not self._is_running)
        self._pause_btn.setEnabled(self._is_running)
        self._stop_btn.setEnabled(self._is_running)
        self._source_combo.setEnabled(not self._is_running)
        self._usb_index_spin.setEnabled(not self._is_running)
        self._gentl_cti_btn.setEnabled(not self._is_running)
        
        # Controles de ciclo
        is_manual = not self._continuous_cb.isChecked()
        self._new_cycle_btn.setEnabled(
            self._is_running and is_manual
            and self._robot_controller.state.value == "READY_FOR_NEXT"
        )
        
        if not self._is_running:
            self._status_step_label.setText("—")
            self._authorize_send_btn.setVisible(False)
            self._authorize_send_btn.setEnabled(False)
        
        self._status_panel.set_stream_running(self._is_running)
        self._status_panel.set_inference_running(self._is_running)
    
    def _on_source_changed(self, index: int) -> None:
        """Handler para mudança de fonte (USB vs GenTL)."""
        is_usb = index == 0
        self._usb_index_label.setVisible(is_usb)
        self._usb_index_spin.setVisible(is_usb)
        self._gentl_cti_btn.setVisible(not is_usb)
        self._gentl_settings_btn.setVisible(not is_usb)
        self._update_source_caption()
    
    def _select_gentl_cti_file(self) -> None:
        """Abre diálogo para selecionar arquivo CTI GenTL (ex.: Omron Sentech)."""
        initial_dir = None
        current_path = (self._settings.streaming.gentl_cti_path or "").strip()
        if current_path:
            current_path_obj = Path(current_path)
            if current_path_obj.exists():
                initial_dir = str(current_path_obj.parent)
            elif current_path_obj.parent.exists():
                initial_dir = str(current_path_obj.parent)
        if not initial_dir:
            initial_dir = ""  # deixa o sistema escolher (ex.: Program Files)
        
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo CTI GenTL",
            initial_dir,
            "Arquivos CTI (*.cti);;Todos os Arquivos (*)",
        )
        if file_path:
            path_obj = Path(file_path)
            if not path_obj.exists() or not path_obj.is_file():
                self._event_console.add_error(f"Arquivo não encontrado ou inválido: {file_path}")
                return
            abs_path_str = str(path_obj.resolve())
            self._settings.streaming.gentl_cti_path = abs_path_str
            self._update_source_caption()
            self._event_console.add_info(f"CTI GenTL selecionado: {path_obj.name}")
            self._logger.info("gentl_cti_selected", path=abs_path_str)

    def _open_gentl_camera_settings(self) -> None:
        """Abre a tela de ajustes da câmera GenTL (gain, exposição). Requer stream ativo."""
        adapter = self._stream_manager.get_gentl_adapter()
        if adapter is None:
            QMessageBox.information(
                self,
                "Ajustes da câmera",
                "Inicie o stream com a câmera GenTL (Omron Sentech) para poder ajustar gain, exposição e outros parâmetros.",
            )
            return
        dlg = GenTLCameraSettingsDialog(adapter, self)
        dlg.exec()
    
    def _toggle_fullscreen(self) -> None:
        """Alterna fullscreen do vídeo."""
        main_window = self.window()
        if main_window is None:
            return
        
        if main_window.isFullScreen():
            main_window.showNormal()
            self._event_console.add_info("Saiu do modo tela cheia")
        else:
            main_window.showFullScreen()
            self._event_console.add_info("Modo tela cheia (F11 para sair)")
    
    def _update_fps(self) -> None:
        """Atualiza FPS no widget de vídeo e latência CIP no painel (RF-06)."""
        if self._stream_manager.is_running:
            fps = self._stream_manager.get_fps()
            self._video_widget.set_fps(fps)
        latency_ms = MetricsCollector().get_last_value("cip_response_time")
        self._status_panel.set_latency_ms(latency_ms)
    
    @Slot()
    def _on_stream_started(self) -> None:
        """Handler para stream iniciado."""
        self._event_console.add_info("Stream iniciado", "Stream")
    
    @Slot()
    def _on_stream_stopped(self) -> None:
        """Handler para stream parado (inclusive por falha em change_source)."""
        self._event_console.add_info("Stream parado", "Stream")
        
        # Se a UI ainda pensa que está rodando mas o stream parou,
        # precisamos sincronizar o estado para evitar inconsistência.
        if self._is_running and not self._stream_manager.is_running:
            self._logger.warning("stream_stopped_unexpectedly_resetting_state")
            self._stop_system()
    
    @Slot(str)
    def _on_stream_error(self, error: str) -> None:
        """Handler para erro de stream."""
        self._event_console.add_error(f"Erro de stream: {error}", "Stream")
    
    def _draw_roi_overlay_if_enabled(self, frame):
        """Desenha retângulo verde de marcação ROI (não corta o frame)."""
        import cv2

        enabled, coords = self._status_panel.get_roi()
        if not enabled or not coords or len(coords) != 4:
            return frame
        x, y, w, h = [int(v) for v in coords]
        h_img, w_img = frame.shape[:2]
        x1 = max(0, min(x, w_img - 1))
        y1 = max(0, min(y, h_img - 1))
        x2 = max(x1 + 1, min(x + w, w_img))
        y2 = max(y1 + 1, min(y + h, h_img))
        out = frame.copy()
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)  # BGR verde, 2px
        return out

    def _draw_detections_on_frame(self, frame, result) -> np.ndarray:
        """Desenha todas as detecções no frame; destaca o alvo de pick (BGR)."""
        if result is None or not result.has_detections:
            return frame

        det_cfg = self._settings.detection
        mm_per_px = get_coordinate_transform().mm_per_px
        pick = select_pick_target(
            result.detections,
            method=det_cfg.pick_selection_method,
            confidence_weight=det_cfg.pick_confidence_weight,
            area_weight=det_cfg.pick_area_weight,
        )
        roi_enabled, roi_coords = self._status_panel.get_roi()
        return draw_detection_masks_on_frame(
            frame,
            result.detections,
            pick,
            mm_per_px=mm_per_px,
            roi_enabled=roi_enabled,
            roi=roi_coords if roi_enabled else None,
        )

    def _refresh_video_with_detections(self) -> None:
        """Recompõe o frame exibido com todas as detecções do último resultado."""
        if self._last_base_frame is None:
            return

        frame = self._draw_roi_overlay_if_enabled(self._last_base_frame)
        result = self._last_overlay_result
        if result is None:
            result = self._inference_engine.last_result

        if result is not None and result.has_detections:
            self._logger.debug(
                "overlay_refresh",
                detection_count=result.count,
                masks_with_data=sum(
                    1 for d in result.detections if getattr(d, "mask", None) is not None
                ),
            )
            frame = self._draw_detections_on_frame(frame, result)

        self._video_widget.update_frame(frame)
        if self._mjpeg_server is not None:
            self._mjpeg_server.push_frame(frame)

    @Slot(object)
    def _on_detection_result(self, result) -> None:
        """Atualiza overlay assim que a inferência devolve todas as detecções."""
        self._last_overlay_result = result
        self._refresh_video_with_detections()

    @Slot(object)
    def _on_frame_available(self, frame_info) -> None:
        """Handler para frame - desenha ROI (overlay), exibe e envia para inferência."""
        if not self._is_running:
            return
        frame = frame_info.frame
        self._last_base_frame = frame.copy()
        self._refresh_video_with_detections()

        if self._is_running and self._inference_engine.is_running:
            self._inference_engine.process_frame(frame, frame_info.frame_id)
    
    @Slot(object)
    def _on_detection(self, event) -> None:
        """Handler para detecção."""
        if not self._is_running:
            return
        if event.detected:
            self._last_best_detection = event
            self._detection_count += 1

            self._event_console.add_success(
                f"Detectado: {event.class_name} ({event.confidence:.0%})",
                "Detecção"
            )
            self._status_panel.update_detection(event)

            if self._robot_controller.accepting_detections:
                self._robot_controller.process_detection(event)
    
    @Slot(int)
    def _on_cycle_completed(self, cycle_number: int) -> None:
        """Handler para ciclo completado."""
        self._event_console.add_success(f"Ciclo {cycle_number} completado", "Robô")
    
    def _on_cycle_mode_changed(self, state: int) -> None:
        """Handler para mudança de modo de ciclo (manual/contínuo)."""
        mode = "continuous" if self._continuous_cb.isChecked() else "manual"
        self._robot_controller.set_cycle_mode(mode)
        self._new_cycle_btn.setEnabled(not self._continuous_cb.isChecked() and self._is_running)
        label = "Contínuo" if mode == "continuous" else "Manual"
        self._event_console.add_info(f"Modo de ciclo: {label}")
    
    def _authorize_new_cycle(self) -> None:
        """Autoriza o próximo ciclo de pick-and-place (modo manual)."""
        self._robot_controller.authorize_next_cycle()
        self._new_cycle_btn.setEnabled(False)
        self._event_console.add_info("Novo ciclo autorizado pelo operador")
    
    def _on_exit_clicked(self) -> None:
        """Fecha o sistema (mesmo fluxo do menu Arquivo → Sair)."""
        mw = self.window()
        if mw and hasattr(mw, "_confirm_and_exit"):
            mw._confirm_and_exit()
        elif mw:
            mw.close()
    
    def _authorize_send_to_plc(self) -> None:
        """Autoriza envio das coordenadas ao CLP apos deteccao (modo manual)."""
        self._robot_controller.authorize_send_to_plc()
        self._authorize_send_btn.setEnabled(False)
        self._event_console.add_info("Envio ao CLP autorizado pelo operador")
    
    def _status_message_for_state(self, state_value: str) -> str:
        """Mensagem amigavel para a barra de status conforme estado do robo."""
        from control.robot_controller import RobotControlState
        messages = {
            RobotControlState.INITIALIZING.value: "Inicializando conexao com CLP...",
            RobotControlState.WAITING_AUTHORIZATION.value: "Aguardando autorizacao do CLP para deteccao...",
            RobotControlState.DETECTING.value: "Aguardando deteccao de embalagem...",
            RobotControlState.WAITING_SEND_AUTHORIZATION.value: "Objeto detectado. Aguardando autorizacao para envio ao CLP.",
            RobotControlState.SENDING_DATA.value: "Enviando coordenadas ao CLP...",
            RobotControlState.WAITING_ACK.value: "Aguardando ACK do robo...",
            RobotControlState.ACK_CONFIRMED.value: "ACK recebido. Aguardando PICK...",
            RobotControlState.WAITING_PICK.value: "Aguardando PICK (coleta)...",
            RobotControlState.WAITING_PLACE.value: "Aguardando PLACE (posicionamento)...",
            RobotControlState.WAITING_CYCLE_START.value: "Aguardando sinal de ciclo completo...",
            RobotControlState.READY_FOR_NEXT.value: "Ciclo finalizado. Aguardando 'Novo Ciclo' (modo manual).",
            RobotControlState.ERROR.value: "Erro no ciclo.",
            RobotControlState.TIMEOUT.value: "Timeout. Aguardando novo ciclo.",
            RobotControlState.SAFETY_BLOCKED.value: "Seguranca ativa. Aguardando liberacao.",
            RobotControlState.STOPPED.value: "Parado.",
        }
        return messages.get(state_value, state_value)
    
    @Slot(str)
    def _on_robot_state_changed(self, state_value: str) -> None:
        """Handler para mudanca de estado do robo: botoes e barra de status."""
        from control.robot_controller import RobotControlState
        
        # Barra de status
        self._status_step_label.setText(self._status_message_for_state(state_value))
        
        # Botao Novo Ciclo
        if (
            state_value == RobotControlState.READY_FOR_NEXT.value
            and self._robot_controller.cycle_mode == "manual"
            and self._is_running
        ):
            self._new_cycle_btn.setEnabled(True)
        else:
            self._new_cycle_btn.setEnabled(False)
        
        # Botao Autorizar envio ao CLP (modo manual, apos deteccao)
        if (
            state_value == RobotControlState.WAITING_SEND_AUTHORIZATION.value
            and self._robot_controller.cycle_mode == "manual"
            and self._is_running
        ):
            self._authorize_send_btn.setVisible(True)
            self._authorize_send_btn.setEnabled(True)
        else:
            self._authorize_send_btn.setVisible(False)
            self._authorize_send_btn.setEnabled(False)

        stream_health = self._stream_manager.get_status().get("health", {}).get("status", "")
        plc_status = self._cip_client.state.status.value if self._cip_client.state else ""
        self._status_panel.update_system_health(
            stream_health=stream_health,
            plc_status=plc_status,
            fsm_state=state_value,
            simulated=self._cip_client.is_simulated,
            production_mode=getattr(self._settings.reliability, "production_mode", False),
        )
    
    @Slot(str)
    def _on_cycle_step(self, step: str) -> None:
        """Handler para etapa do ciclo — exibe no console e na barra de status."""
        if not self._is_running:
            return
        self._event_console.add_info(f"[Ciclo] {step}", "Robo")
        self._status_step_label.setText(step)
    
    @Slot(list)
    def _on_cycle_summary(self, steps: list) -> None:
        """Handler para resumo do ciclo completo — exibe sumário formatado."""
        if not self._is_running or not steps:
            return
        
        cycle_num = self._robot_controller.cycle_count
        
        # Calcula duração total
        if len(steps) >= 2:
            t0 = steps[0]["timestamp"]
            t1 = steps[-1]["timestamp"]
            duration = (t1 - t0).total_seconds()
        else:
            duration = 0.0
        
        self._event_console.add_success(
            f"===== CICLO #{cycle_num} COMPLETO ({duration:.1f}s) =====",
            "Ciclo"
        )
        for i, s in enumerate(steps, 1):
            ts = s["timestamp"].strftime("%H:%M:%S")
            self._event_console.add_info(
                f"  {i}. [{ts}] {s['step']}",
                "Ciclo"
            )
        self._event_console.add_success(
            f"{'=' * 45}",
            "Ciclo"
        )
        
        # Em modo manual, informa que aguarda autorização
        if self._robot_controller.cycle_mode == "manual":
            self._event_console.add_warning(
                "Aguardando operador clicar 'Novo Ciclo' para continuar.",
                "Ciclo"
            )
    
    @Slot(str)
    def _on_cip_error(self, error: str) -> None:
        """Handler para erro CIP (RF-06: último erro na UI)."""
        self._error_count += 1
        self._event_console.add_error(f"Erro CIP: {error}", "CLP")
        self._status_panel.set_last_error(error)
    
    @Slot(str)
    def _on_robot_error(self, error: str) -> None:
        """Handler para erro do robô (RF-06: último erro na UI)."""
        self._error_count += 1
        self._event_console.add_error(f"Erro do robô: {error}", "Robô")
        self._status_panel.set_last_error(error)
