# -*- coding: utf-8 -*-
"""
Página de Configuração - Configurações do sistema.
Interface reformulada: agrupamento por função, layout estado da arte (ISA-101).
"""

from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QFormLayout, QLineEdit, QSpinBox,
    QDoubleSpinBox, QComboBox, QCheckBox, QPushButton,
    QLabel, QFileDialog, QSlider, QFrame, QMessageBox,
    QScrollArea, QGridLayout, QApplication
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QFont

from config import get_settings
from core.logger import get_logger
from streaming.mjpeg_server import get_local_ip, normalize_http_path

logger = get_logger("config")


# Estilos ISA-101 / HMI industrial (pick-and-place)
CONFIG_GROUP_STYLE = """
    QGroupBox {
        font-weight: bold;
        color: #e5e7eb;
        border: 1px solid #1b3a69;
        border-radius: 6px;
        margin-top: 14px;
        padding: 12px 12px 12px 12px;
        background-color: #14284c;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #26477e;
    }
"""


class ConfigurationPage(QWidget):
    """
    Página de Configuração.
    
    Sub-abas:
    - Fonte de Vídeo
    - Modelo RT-DETR
    - Pré-processamento
    - Controle (CLP)
    - Output
    """

    settings_saved = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self._settings = get_settings()
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self) -> None:
        """Configura a interface (ISA-101: ações primárias no topo)."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        # Barra de ações (ISA-101: ações no topo para visibilidade imediata)
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        self._reset_btn = QPushButton("Restaurar Padrões")
        self._reset_btn.setToolTip("Restaura valores padrão (não persiste até Salvar)")
        self._reset_btn.clicked.connect(self._reset_settings)
        buttons_layout.addWidget(self._reset_btn)
        self._save_btn = QPushButton("Salvar Configurações")
        self._save_btn.setToolTip("Persiste configurações no arquivo config.yaml")
        self._save_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        self._save_btn.clicked.connect(self._save_settings)
        buttons_layout.addWidget(self._save_btn)
        self._exit_btn = QPushButton("Sair")
        self._exit_btn.setToolTip("Encerra o sistema (Cmd+Q no macOS)")
        self._exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                padding: 10px 20px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        self._exit_btn.clicked.connect(self._on_exit_clicked)
        buttons_layout.addWidget(self._exit_btn)
        layout.addLayout(buttons_layout)
        
        # Tabs de configuração
        self._tabs = QTabWidget()
        self._tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #1b3a69;
                border-radius: 4px;
                background-color: #14284c;
            }
            QTabBar::tab {
                background-color: #1b3a69;
                color: #e0e0e0;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
            }
            QTabBar::tab:selected {
                background-color: #14284c;
                color: #26477e;
            }
        """)
        
        # Abas agrupadas por função (estado da arte)
        self._tabs.addTab(self._create_camera_tab(), "Câmera")
        self._tabs.addTab(self._create_deteccao_tab(), "Detecção")
        self._tabs.addTab(self._create_imagem_tab(), "Imagem")
        self._tabs.addTab(self._create_plc_tab(), "CLP")
        self._tabs.addTab(self._create_output_tab(), "Saída")
        
        layout.addWidget(self._tabs)
    
    def showEvent(self, event) -> None:
        """Actualiza visibilidade dos grupos de câmera ao abrir a página."""
        super().showEvent(event)
        self._update_camera_groups_visibility()
    
    def _on_exit_clicked(self) -> None:
        """Fecha o sistema (mesmo fluxo do menu Arquivo → Sair)."""
        mw = self.window()
        if mw and hasattr(mw, "_confirm_and_exit"):
            mw._confirm_and_exit()
        else:
            mw.close() if mw else None
    
    def _create_camera_tab(self) -> QWidget:
        """Aba Câmera: parâmetros USB e GenTL (tipo escolhido na aba Operação)."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        info = QLabel(
            "O tipo de câmera (USB ou GenTL) é escolhido na aba Operação. "
            "Esta secção guarda apenas os parâmetros técnicos da fonte activa."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #8b9dc3; font-size: 11px; padding: 4px 0;")
        layout.addWidget(info)
        
        self._usb_group = QGroupBox("Câmera USB")
        self._usb_group.setStyleSheet(CONFIG_GROUP_STYLE)
        usb_layout = QFormLayout(self._usb_group)
        
        self._usb_index = QSpinBox()
        self._usb_index.setRange(0, 10)
        self._usb_index.setToolTip("Índice OpenCV da câmera USB (0 = primeira)")
        usb_layout.addRow("Índice:", self._usb_index)
        
        layout.addWidget(self._usb_group)
        
        self._gentl_group = QGroupBox("Câmera GenTL (Omron Sentech)")
        self._gentl_group.setStyleSheet(CONFIG_GROUP_STYLE)
        gentl_layout = QFormLayout(self._gentl_group)
        
        cti_layout = QHBoxLayout()
        self._gentl_cti_path = QLineEdit()
        self._gentl_cti_path.setPlaceholderText(r"C:\...\StGenTL_MD_VC141_v1_5_x64.cti")
        self._gentl_cti_path.setReadOnly(True)
        cti_layout.addWidget(self._gentl_cti_path)
        
        gentl_browse_btn = QPushButton("Procurar...")
        gentl_browse_btn.clicked.connect(self._browse_gentl_cti)
        cti_layout.addWidget(gentl_browse_btn)
        gentl_layout.addRow("Arquivo CTI:", cti_layout)
        
        self._gentl_device_index = QSpinBox()
        self._gentl_device_index.setRange(0, 10)
        self._gentl_device_index.setToolTip("Índice da câmera na lista GenTL (0 = primeira)")
        gentl_layout.addRow("Índice da câmera:", self._gentl_device_index)
        
        self._gentl_max_dimension = QSpinBox()
        self._gentl_max_dimension.setRange(0, 4096)
        self._gentl_max_dimension.setValue(1920)
        self._gentl_max_dimension.setSpecialValueText("Sem limite")
        self._gentl_max_dimension.setToolTip(
            "Máximo do lado maior em pixels (0 = não redimensionar). "
            "Reduz carga em câmeras 20MP+."
        )
        gentl_layout.addRow("Dimensão máx. (px):", self._gentl_max_dimension)
        
        self._gentl_target_fps = QDoubleSpinBox()
        self._gentl_target_fps.setRange(1.0, 60.0)
        self._gentl_target_fps.setValue(15.0)
        self._gentl_target_fps.setDecimals(1)
        self._gentl_target_fps.setToolTip(
            "FPS alvo do stream (valores menores reduzem carga em alta resolução)"
        )
        gentl_layout.addRow("FPS alvo:", self._gentl_target_fps)
        
        layout.addWidget(self._gentl_group)
        
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _update_camera_groups_visibility(self) -> None:
        """Mostra só o grupo relevante para a fonte activa (USB ou GenTL)."""
        source = getattr(self._settings.streaming, "source_type", "usb")
        is_gentl = source == "gentl"
        self._usb_group.setVisible(not is_gentl)
        self._gentl_group.setVisible(is_gentl)
    
    def _create_deteccao_tab(self) -> QWidget:
        """Aba Detecção: modelo e parâmetros de inferência activos em runtime."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        info = QLabel(
            "Parâmetros usados pelo motor de inferência. "
            "Alterações em confiança, device ou FPS exigem parar e reiniciar o sistema."
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #8b9dc3; font-size: 11px; padding: 4px 0;")
        layout.addWidget(info)
        
        model_group = QGroupBox("Modelo")
        model_group.setStyleSheet(CONFIG_GROUP_STYLE)
        model_layout = QFormLayout(model_group)
        path_layout = QHBoxLayout()
        self._model_path = QLineEdit()
        self._model_path.setPlaceholderText("model_best (pasta local Mask2Former)")
        path_layout.addWidget(self._model_path)
        browse_model_btn = QPushButton("Procurar...")
        browse_model_btn.clicked.connect(self._browse_model)
        path_layout.addWidget(browse_model_btn)
        model_layout.addRow("Caminho local:", path_layout)
        layout.addWidget(model_group)
        
        params_group = QGroupBox("Inferência")
        params_group.setStyleSheet(CONFIG_GROUP_STYLE)
        params_layout = QFormLayout(params_group)
        self._device_combo = QComboBox()
        self._device_combo.addItems(["auto", "cuda", "mps", "cpu"])
        params_layout.addRow("Device:", self._device_combo)
        conf_layout = QHBoxLayout()
        self._confidence_slider = QSlider(Qt.Horizontal)
        self._confidence_slider.setRange(0, 100)
        self._confidence_slider.valueChanged.connect(self._on_confidence_changed)
        conf_layout.addWidget(self._confidence_slider)
        self._confidence_label = QLabel("50%")
        self._confidence_label.setMinimumWidth(40)
        conf_layout.addWidget(self._confidence_label)
        params_layout.addRow("Confiança mín.:", conf_layout)
        self._max_detections = QSpinBox()
        self._max_detections.setRange(1, 100)
        params_layout.addRow("Máx. detecções:", self._max_detections)
        self._inference_fps = QSpinBox()
        self._inference_fps.setRange(1, 60)
        params_layout.addRow("FPS inferência:", self._inference_fps)
        self._stable_frames = QSpinBox()
        self._stable_frames.setRange(1, 30)
        self._stable_frames.setToolTip(
            "Frames consecutivos com o mesmo alvo antes de emitir evento à FSM"
        )
        params_layout.addRow("Frames estáveis:", self._stable_frames)
        self._centroid_epsilon = QDoubleSpinBox()
        self._centroid_epsilon.setRange(1.0, 200.0)
        self._centroid_epsilon.setDecimals(1)
        self._centroid_epsilon.setSuffix(" px")
        self._centroid_epsilon.setToolTip(
            "Tolerância de movimento do centroide entre frames estáveis"
        )
        params_layout.addRow("Epsilon centroide:", self._centroid_epsilon)
        layout.addWidget(params_group)

        pick_group = QGroupBox("Seleção pick-and-place")
        pick_group.setStyleSheet(CONFIG_GROUP_STYLE)
        pick_layout = QFormLayout(pick_group)
        self._pick_method_combo = QComboBox()
        self._pick_method_combo.addItem(
            "Área + confiança (paralaxe) — default",
            "area_then_conf",
        )
        self._pick_method_combo.addItem("Score ponderado (conf + área)", "weighted_score")
        self._pick_method_combo.addItem("Apenas maior área", "area_only")
        self._pick_method_combo.addItem("Apenas maior confiança", "confidence_only")
        self._pick_method_combo.setToolTip(
            "Paralaxe: embalagens mais próximas da câmera aparecem maiores. "
            "O método 'Área + confiança' prioriza maior área aparente e "
            "usa confiança como desempate."
        )
        pick_layout.addRow("Método:", self._pick_method_combo)
        self._pick_conf_weight = QDoubleSpinBox()
        self._pick_conf_weight.setRange(0.0, 10.0)
        self._pick_conf_weight.setSingleStep(0.1)
        self._pick_conf_weight.setValue(1.0)
        pick_layout.addRow("Peso confiança:", self._pick_conf_weight)
        self._pick_area_weight = QDoubleSpinBox()
        self._pick_area_weight.setRange(0.0, 10.0)
        self._pick_area_weight.setSingleStep(0.1)
        self._pick_area_weight.setValue(1.0)
        pick_layout.addRow("Peso área:", self._pick_area_weight)
        self._plc_area_unit_combo = QComboBox()
        self._plc_area_unit_combo.addItem("cm²", "cm2")
        self._plc_area_unit_combo.addItem("mm²", "mm2")
        self._plc_area_unit_combo.addItem("px²", "px2")
        self._plc_area_unit_combo.setToolTip("Unidade enviada na tag OBJECT_AREA ao CLP")
        pick_layout.addRow("Área no CLP:", self._plc_area_unit_combo)
        self._pick_method_combo.currentIndexChanged.connect(self._on_pick_method_changed)
        self._on_pick_method_changed()
        layout.addWidget(pick_group)
        layout.addStretch()
        scroll.setWidget(widget)
        return scroll
    
    def _create_imagem_tab(self) -> QWidget:
        """Aba Imagem: ROI e perfil de pré-processamento."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        roi_group = QGroupBox("ROI (Região de Interesse)")
        roi_group.setStyleSheet(CONFIG_GROUP_STYLE)
        roi_group.setToolTip("Define a região da imagem usada na detecção. Sempre em pixels.")
        roi_layout = QFormLayout(roi_group)

        roi_coords = QHBoxLayout()
        self._roi_x = QDoubleSpinBox()
        self._roi_x.setRange(0, 9999)
        self._roi_x.setDecimals(1)
        self._roi_x.setToolTip("Coordenada X do canto superior esquerdo")
        self._roi_y = QDoubleSpinBox()
        self._roi_y.setRange(0, 9999)
        self._roi_y.setDecimals(1)
        self._roi_y.setToolTip("Coordenada Y do canto superior esquerdo")
        self._roi_w = QDoubleSpinBox()
        self._roi_w.setRange(0.1, 9999)
        self._roi_w.setDecimals(1)
        self._roi_w.setToolTip("Largura da região")
        self._roi_h = QDoubleSpinBox()
        self._roi_h.setRange(0.1, 9999)
        self._roi_h.setDecimals(1)
        self._roi_h.setToolTip("Altura da região")
        roi_coords.addWidget(QLabel("X:"))
        roi_coords.addWidget(self._roi_x)
        roi_coords.addWidget(QLabel("Y:"))
        roi_coords.addWidget(self._roi_y)
        roi_coords.addWidget(QLabel("W:"))
        roi_coords.addWidget(self._roi_w)
        roi_coords.addWidget(QLabel("H:"))
        roi_coords.addWidget(self._roi_h)
        roi_layout.addRow("Coordenadas (x, y, largura, altura) [px]:", roi_coords)

        self._roi_enabled = QCheckBox("Ativar confinamento ROI")
        self._roi_enabled.setToolTip(
            "Limita o centroide enviado ao CLP e exibido no overlay à região definida"
        )
        roi_layout.addRow("", self._roi_enabled)

        roi_default_btn = QPushButton("Padrão (25% área central)")
        roi_default_btn.setToolTip("Define ROI como 25% da área centralizada (ex.: 640x480)")
        roi_default_btn.clicked.connect(self._set_default_roi)
        roi_layout.addRow("", roi_default_btn)

        self._centroid_mm_per_px = QDoubleSpinBox()
        self._centroid_mm_per_px.setRange(0.0001, 10000.0)
        self._centroid_mm_per_px.setValue(1.0)
        self._centroid_mm_per_px.setSuffix(" mm/px")
        self._centroid_mm_per_px.setToolTip(
            "Relação mm/px aplicada ao centroide (X,Y) da detecção. Default 1. Ex.: 100 → coord_mm = px * 100"
        )
        roi_layout.addRow("Centroide (mm/px):", self._centroid_mm_per_px)

        layout.addWidget(roi_group)
        layout.addStretch()
        return widget
    
    def _set_default_roi(self) -> None:
        """Aplica ROI padrão (25% da área centralizada) em pixels."""
        from config.settings import DEFAULT_ROI_QUARTER_AREA
        x, y, w, h = DEFAULT_ROI_QUARTER_AREA
        self._roi_x.setValue(x)
        self._roi_y.setValue(y)
        self._roi_w.setValue(w)
        self._roi_h.setValue(h)
    
    def _create_plc_tab(self) -> QWidget:
        """Cria aba de configuração do CLP."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        conn_group = QGroupBox("Conexão CIP/EtherNet-IP")
        conn_group.setStyleSheet(CONFIG_GROUP_STYLE)
        conn_layout = QFormLayout(conn_group)
        
        self._plc_ip = QLineEdit()
        self._plc_ip.setPlaceholderText("187.99.125.5")
        conn_layout.addRow("IP do CLP:", self._plc_ip)
        
        self._plc_port = QSpinBox()
        self._plc_port.setRange(1, 65535)
        self._plc_port.setValue(44818)
        conn_layout.addRow("Porta CIP:", self._plc_port)
        
        self._conn_timeout = QDoubleSpinBox()
        self._conn_timeout.setRange(1.0, 60.0)
        self._conn_timeout.setSingleStep(0.5)
        self._conn_timeout.setSuffix(" s")
        conn_layout.addRow("Timeout:", self._conn_timeout)
        
        self._simulated = QCheckBox("Modo simulado")
        conn_layout.addRow("", self._simulated)
        
        test_btn = QPushButton("Testar Conexão")
        test_btn.clicked.connect(self._test_plc_connection)
        conn_layout.addRow("", test_btn)
        
        layout.addWidget(conn_group)
        
        retry_group = QGroupBox("Reconexão Automática")
        retry_group.setStyleSheet(CONFIG_GROUP_STYLE)
        retry_layout = QFormLayout(retry_group)
        
        self._retry_interval = QDoubleSpinBox()
        self._retry_interval.setRange(0.5, 30.0)
        self._retry_interval.setSingleStep(0.5)
        self._retry_interval.setSuffix(" s")
        retry_layout.addRow("Intervalo:", self._retry_interval)
        
        self._max_retries = QSpinBox()
        self._max_retries.setRange(0, 100)
        retry_layout.addRow("Máx. tentativas:", self._max_retries)
        
        layout.addWidget(retry_group)
        
        hb_group = QGroupBox("Heartbeat")
        hb_group.setStyleSheet(CONFIG_GROUP_STYLE)
        hb_layout = QFormLayout(hb_group)
        
        self._heartbeat_interval = QDoubleSpinBox()
        self._heartbeat_interval.setRange(0.1, 10.0)
        self._heartbeat_interval.setSingleStep(0.1)
        self._heartbeat_interval.setSuffix(" s")
        hb_layout.addRow("Intervalo:", self._heartbeat_interval)
        
        layout.addWidget(hb_group)
        
        layout.addStretch()
        
        return widget
    
    def _create_output_tab(self) -> QWidget:
        """Aba Saída: um clique copia a URL e liga o stream HTTP MJPEG."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(16)
        
        stream_group = QGroupBox("Stream HTTP (MJPEG)")
        stream_group.setStyleSheet(CONFIG_GROUP_STYLE)
        stream_layout = QFormLayout(stream_group)
        
        # Legado YAML; não exposto na UI — activado ao clicar Copiar URL
        self._rtsp_enabled = QCheckBox()
        self._rtsp_enabled.setVisible(False)
        
        self._http_port = QSpinBox()
        self._http_port.setRange(1, 65535)
        self._http_port.setValue(8080)
        stream_layout.addRow("Porta:", self._http_port)

        self._http_path = QLineEdit("/stream")
        self._http_path.setPlaceholderText("/stream")
        self._http_path.setToolTip("Path HTTP do stream (ex.: /stream)")
        stream_layout.addRow("Path:", self._http_path)
        
        copy_btn = QPushButton("Copiar URL do stream")
        copy_btn.setToolTip(
            "Liga o stream, copia a URL e cole no Chrome/Firefox/Edge."
        )
        copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #2563eb;
                color: white;
                font-weight: bold;
                padding: 10px 16px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        copy_btn.clicked.connect(self._copy_stream_url)
        stream_layout.addRow("", copy_btn)
        
        url_help = QLabel(
            "Clique no botão acima → cole a URL no navegador. "
            "Com Operação ▶ Iniciado, o vídeo ao vivo aparece; "
            "caso contrário, verá aguardando câmera."
        )
        url_help.setStyleSheet("color: #8b9dc3; font-size: 11px;")
        url_help.setWordWrap(True)
        stream_layout.addRow("", url_help)
        
        layout.addWidget(stream_group)
        layout.addStretch()
        
        return widget
    
    def _sync_output_settings(self, *, enable_stream: bool = False) -> None:
        """Sincroniza widgets Saída → settings (memória)."""
        s = self._settings
        if enable_stream:
            self._rtsp_enabled.setChecked(True)
        s.output.rtsp_enabled = self._rtsp_enabled.isChecked() or enable_stream
        s.output.http_port = self._http_port.value()
        s.output.http_path = normalize_http_path(self._http_path.text())
        self._http_path.setText(s.output.http_path)

    def _persist_output_yaml(self) -> None:
        """Grava config.yaml (silencioso ao copiar URL)."""
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        self._settings.to_yaml(config_path)

    def _get_stream_url(self, localhost: bool = False) -> str:
        """Retorna URL do stream (localhost = mesmo PC)."""
        port = self._http_port.value()
        path = normalize_http_path(self._http_path.text())
        host = "127.0.0.1" if localhost else get_local_ip()
        return f"http://{host}:{port}{path}"

    def _copy_stream_url(self) -> None:
        """Liga stream, persiste, aplica no servidor e copia URL (127.0.0.1)."""
        self._sync_output_settings(enable_stream=True)
        self._persist_output_yaml()
        self.settings_saved.emit()

        url = self._get_stream_url(localhost=True)
        QApplication.clipboard().setText(url)
        logger.info(
            "stream_url_copied",
            url=url,
            port=self._settings.output.http_port,
            path=self._settings.output.http_path,
        )
        QMessageBox.information(
            self,
            "Stream pronto",
            f"URL copiada:\n{url}\n\n"
            "Cole na barra de endereços do navegador.",
        )
    
    def _load_settings(self) -> None:
        """Carrega configurações atuais."""
        s = self._settings
        
        # Câmera (tipo definido na aba Operação)
        self._usb_index.setValue(s.streaming.usb_camera_index)
        self._gentl_cti_path.setText(s.streaming.gentl_cti_path)
        self._gentl_device_index.setValue(s.streaming.gentl_device_index)
        self._gentl_max_dimension.setValue(s.streaming.gentl_max_dimension)
        self._gentl_target_fps.setValue(s.streaming.gentl_target_fps)
        self._update_camera_groups_visibility()
        
        # Modelo
        self._model_path.setText(s.detection.model_path)
        self._device_combo.setCurrentText(s.detection.device)
        self._confidence_slider.setValue(int(s.detection.confidence_threshold * 100))
        self._max_detections.setValue(s.detection.max_detections)
        self._inference_fps.setValue(s.detection.inference_fps)
        self._stable_frames.setValue(getattr(s.detection, "stable_frames", 3))
        self._centroid_epsilon.setValue(
            getattr(s.detection, "centroid_epsilon_px", 15.0)
        )

        method = getattr(s.detection, "pick_selection_method", "area_then_conf")
        idx = self._pick_method_combo.findData(method)
        self._pick_method_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._pick_conf_weight.setValue(s.detection.pick_confidence_weight)
        self._pick_area_weight.setValue(s.detection.pick_area_weight)
        unit_idx = self._plc_area_unit_combo.findData(
            getattr(s.detection, "plc_area_unit", "cm2")
        )
        self._plc_area_unit_combo.setCurrentIndex(unit_idx if unit_idx >= 0 else 0)
        self._on_pick_method_changed()
        
        # Imagem (ROI em px, calibração centroide mm/px)
        if s.preprocess.roi and len(s.preprocess.roi) == 4:
            px_vals = [float(s.preprocess.roi[i]) for i in range(4)]
        else:
            from config.settings import DEFAULT_ROI_QUARTER_AREA
            px_vals = list(DEFAULT_ROI_QUARTER_AREA)

        self._roi_x.setValue(px_vals[0])
        self._roi_y.setValue(px_vals[1])
        self._roi_w.setValue(px_vals[2])
        self._roi_h.setValue(px_vals[3])
        self._roi_enabled.setChecked(bool(getattr(s.preprocess, "roi_enabled", True)))
        self._centroid_mm_per_px.setValue(
            getattr(s.preprocess, "roi_calibration_mm_per_px", 1.0)
        )
        
        # CLP
        self._plc_ip.setText(s.cip.ip)
        self._plc_port.setValue(s.cip.port)
        self._conn_timeout.setValue(s.cip.connection_timeout)
        self._simulated.setChecked(s.cip.simulated)
        self._retry_interval.setValue(s.cip.retry_interval)
        self._max_retries.setValue(s.cip.max_retries)
        self._heartbeat_interval.setValue(s.cip.heartbeat_interval)
        
        # Output
        self._rtsp_enabled.setChecked(s.output.rtsp_enabled)
        self._http_port.setValue(s.output.http_port)
        self._http_path.setText(normalize_http_path(s.output.http_path))
    
    def _save_settings(self) -> None:
        """Salva configurações."""
        s = self._settings
        
        # Câmera (source_type definido na aba Operação)
        s.streaming.usb_camera_index = self._usb_index.value()
        s.streaming.gentl_cti_path = self._gentl_cti_path.text()
        s.streaming.gentl_device_index = self._gentl_device_index.value()
        s.streaming.gentl_max_dimension = self._gentl_max_dimension.value()
        s.streaming.gentl_target_fps = self._gentl_target_fps.value()
        
        # Modelo
        s.detection.model_path = self._model_path.text()
        s.detection.device = self._device_combo.currentText()
        s.detection.confidence_threshold = self._confidence_slider.value() / 100
        s.detection.max_detections = self._max_detections.value()
        s.detection.inference_fps = self._inference_fps.value()
        s.detection.stable_frames = self._stable_frames.value()
        s.detection.centroid_epsilon_px = self._centroid_epsilon.value()
        s.detection.pick_selection_method = self._pick_method_combo.currentData()
        s.detection.pick_confidence_weight = self._pick_conf_weight.value()
        s.detection.pick_area_weight = self._pick_area_weight.value()
        s.detection.plc_area_unit = self._plc_area_unit_combo.currentData()
        
        # Imagem (ROI em px, calibração centroide mm/px)
        px_vals = [
            int(round(self._roi_x.value())),
            int(round(self._roi_y.value())),
            max(1, int(round(self._roi_w.value()))),
            max(1, int(round(self._roi_h.value()))),
        ]
        s.preprocess.roi = px_vals
        s.preprocess.roi_enabled = self._roi_enabled.isChecked()
        s.preprocess.roi_calibration_mm_per_px = self._centroid_mm_per_px.value()
        
        # CLP
        s.cip.ip = self._plc_ip.text()
        s.cip.port = self._plc_port.value()
        s.cip.connection_timeout = self._conn_timeout.value()
        s.cip.simulated = self._simulated.isChecked()
        s.cip.retry_interval = self._retry_interval.value()
        s.cip.max_retries = self._max_retries.value()
        s.cip.heartbeat_interval = self._heartbeat_interval.value()
        
        # Output (HTTP MJPEG; rtsp_enabled activado via Copiar URL)
        self._sync_output_settings()
        
        # Salva em arquivo
        config_path = Path(__file__).parent.parent.parent / "config" / "config.yaml"
        s.to_yaml(config_path)
        
        logger.info(
            "config_saved",
            cip_ip=s.cip.ip,
            cip_port=s.cip.port,
            http_stream=s.output.rtsp_enabled,
            http_port=s.output.http_port,
            http_path=s.output.http_path,
            config_path=str(config_path),
        )

        self.settings_saved.emit()
        
        QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!")
    
    def _reset_settings(self) -> None:
        """Restaura configurações padrão carregando valores default do Pydantic."""
        reply = QMessageBox.question(
            self,
            "Confirmar Reset",
            "Restaurar todas as configurações para os valores padrão?\n"
            "As configurações atuais serão perdidas.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        
        from config.settings import (
            StreamingSettings, DetectionSettings, PreprocessSettings,
            CIPSettings, OutputSettings,
        )
        
        # Aplica defaults no objeto settings em memória
        s = self._settings
        s.streaming = StreamingSettings()
        s.detection = DetectionSettings()
        s.preprocess = PreprocessSettings()
        s.cip = CIPSettings()
        s.output = OutputSettings()
        
        # Recarrega a UI com os novos valores
        self._load_settings()
        
        logger.info("settings_reset_to_defaults")
        QMessageBox.information(
            self, "Sucesso",
            "Configurações restauradas aos valores padrão.\n"
            "Clique em 'Salvar Configurações' para persistir no arquivo."
        )
    
    def _browse_gentl_cti(self) -> None:
        """Abre diálogo para selecionar arquivo CTI GenTL."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar arquivo CTI GenTL",
            "",
            "Arquivos CTI (*.cti);;Todos (*)",
        )
        if file_path:
            self._gentl_cti_path.setText(file_path)
    
    def _browse_model(self) -> None:
        """Abre diálogo para selecionar modelo."""
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "Selecionar Diretório do Modelo",
        )
        if dir_path:
            self._model_path.setText(dir_path)
    
    def _on_pick_method_changed(self) -> None:
        """Mostra pesos apenas para o método weighted_score."""
        is_weighted = self._pick_method_combo.currentData() == "weighted_score"
        self._pick_conf_weight.setEnabled(is_weighted)
        self._pick_area_weight.setEnabled(is_weighted)

    def _on_confidence_changed(self, value: int) -> None:
        """Handler para mudança de confiança."""
        self._confidence_label.setText(f"{value}%")
    
    def _test_plc_connection(self) -> None:
        """Testa conexão com CLP usando os parâmetros atuais da UI."""
        ip = self._plc_ip.text().strip()
        port = self._plc_port.value()
        timeout = self._conn_timeout.value()
        simulated = self._simulated.isChecked()
        
        if simulated:
            QMessageBox.information(
                self, "Modo Simulado",
                "O modo simulado está ativado.\n"
                "Desmarque 'Modo simulado' para testar a conexão real com o CLP."
            )
            return
        
        if not ip:
            QMessageBox.warning(self, "Aviso", "Informe o IP do CLP.")
            return
        
        # Teste de alcance via socket (não depende do CIP completo)
        import socket
        
        QMessageBox.information(
            self, "Testando...",
            f"Testando conexão TCP com {ip}:{port}...\n"
            f"Timeout: {timeout}s"
        )
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                QMessageBox.information(
                    self, "Sucesso",
                    f"Conexão TCP com {ip}:{port} estabelecida com sucesso.\n"
                    f"O CLP está acessível na rede."
                )
                logger.info("plc_connection_test_success", ip=ip, port=port)
            else:
                QMessageBox.warning(
                    self, "Falha",
                    f"Não foi possível conectar a {ip}:{port}.\n"
                    f"Código de erro: {result}\n\n"
                    f"Verifique:\n"
                    f"- O CLP está ligado e na rede?\n"
                    f"- O IP e porta estão corretos?\n"
                    f"- Há firewall bloqueando a porta?"
                )
                logger.warning("plc_connection_test_failed", ip=ip, port=port, error_code=result)
        except socket.timeout:
            QMessageBox.warning(
                self, "Timeout",
                f"Timeout ao conectar a {ip}:{port} ({timeout}s).\n"
                f"O CLP não respondeu no tempo esperado."
            )
            logger.warning("plc_connection_test_timeout", ip=ip, port=port)
        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao testar conexão: {e}"
            )
            logger.error("plc_connection_test_error", ip=ip, port=port, error=str(e))
