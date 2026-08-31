# -*- coding: utf-8 -*-
"""
Configurações do sistema usando Pydantic Settings.
Carrega configurações de variáveis de ambiente e arquivo YAML.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional, List, Dict, Any

import yaml
from pydantic import BaseModel, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class StreamingSettings(BaseModel):
    """Configurações de streaming de vídeo."""
    
    source_type: str = Field(default="usb", description="Tipo: video, usb, rtsp, gige, gentl. Padrão: usb.")
    video_path: str = Field(default="videos/test.mp4", description="Caminho do arquivo de vídeo")
    usb_camera_index: int = Field(default=0, description="Índice da câmera USB (0 = primeira câmera)")
    rtsp_url: str = Field(default="", description="URL do stream RTSP")
    gige_ip: str = Field(default="", description="IP da câmera GigE")
    gige_port: int = Field(default=3956, description="Porta da câmera GigE")
    gentl_cti_path: str = Field(default="", description="Caminho do arquivo CTI GenTL (ex.: Omron Sentech)")
    gentl_device_index: int = Field(default=0, description="Índice da câmera na lista GenTL (0 = primeira)")
    gentl_max_dimension: int = Field(default=1920, ge=0, le=4096, description="Dimensão máx. do lado maior (px); 0 = sem redimensionar")
    gentl_target_fps: float = Field(default=15.0, ge=1.0, le=60.0, description="FPS alvo do stream GenTL (reduz carga em câmeras de alta resolução)")
    max_frame_buffer_size: int = Field(default=30, description="Tamanho máximo do buffer")
    loop_video: bool = Field(default=True, description="Loop do vídeo")
    unhealthy_restart_after_s: float = Field(
        default=10.0, ge=1.0,
        description="Segundos UNHEALTHY antes de reiniciar captura",
    )
    
    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: str) -> str:
        valid_types = {"video", "usb", "rtsp", "gige", "gentl"}
        if v not in valid_types:
            raise ValueError(f"source_type deve ser um de: {valid_types}")
        return v


class DetectionSettings(BaseModel):
    """Configurações de detecção."""
    
    model_path: str = Field(default="model_best", description="Caminho para modelo local (relativo ao pacote)")
    default_model: str = Field(
        default="model_best",
        description="Modelo padrão (caminho local ou ID do Hugging Face)",
    )
    confidence_threshold: float = Field(default=0.5, ge=0.0, le=1.0, description="Threshold de confiança")
    max_detections: int = Field(default=10, ge=1, description="Máximo de detecções")
    target_classes: Optional[List[str]] = Field(
        default=["Embalagem"],
        description="Classes alvo (null = todas). Padrão: apenas 'Embalagem'",
    )
    inference_fps: int = Field(default=15, ge=1, description="FPS de inferência")
    device: str = Field(default="auto", description="Device: cpu, cuda, mps, auto (mps = Apple Silicon)")

    # Parâmetros específicos de instance segmentation (Mask2Former)
    segmentation_mask_threshold: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Threshold de binarização das máscaras Mask2Former",
    )
    segmentation_overlap_mask_area_threshold: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="Threshold de sobreposição de máscaras (pós-processamento)",
    )
    segmentation_min_mask_pixels: int = Field(
        default=64, ge=1,
        description="Área mínima (px) para aceitar uma máscara e calcular geometria/PCA",
    )
    pick_selection_method: str = Field(
        default="area_then_conf",
        description=(
            "Método de seleção do alvo pick: area_then_conf (paralaxe), "
            "weighted_score, area_only, confidence_only"
        ),
    )
    pick_confidence_weight: float = Field(
        default=1.0, ge=0.0,
        description="Peso da confiança no método weighted_score",
    )
    pick_area_weight: float = Field(
        default=1.0, ge=0.0,
        description="Peso da área no método weighted_score",
    )
    plc_area_unit: str = Field(
        default="cm2",
        description="Unidade de OBJECT_AREA no CLP: cm2, mm2 ou px2",
    )
    stable_frames: int = Field(
        default=3, ge=1, le=30,
        description="Frames consecutivos para estabilizar pick antes da FSM",
    )
    centroid_epsilon_px: float = Field(
        default=15.0, ge=0.0,
        description="Tolerância px para considerar mesmo alvo entre frames",
    )
    inference_max_consecutive_errors: int = Field(
        default=5, ge=1, le=50,
        description="Erros consecutivos antes de reiniciar worker de inferência",
    )
    prioritize_area: Optional[bool] = Field(
        default=None,
        description="Legado: migrado para pick_selection_method se definido",
    )

    @model_validator(mode="before")
    @classmethod
    def _migrate_prioritize_area(cls, data: object) -> object:
        """Migra prioritize_area legado para pick_selection_method."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "pick_selection_method" not in data and "prioritize_area" in data:
            prioritize = data.pop("prioritize_area")
            if prioritize is False:
                data["pick_selection_method"] = "confidence_only"
            elif prioritize is True:
                data["pick_selection_method"] = "weighted_score"
        elif "prioritize_area" in data:
            data.pop("prioritize_area", None)
        return data

    @field_validator("pick_selection_method")
    @classmethod
    def validate_pick_selection_method(cls, v: str) -> str:
        valid = {"area_then_conf", "weighted_score", "area_only", "confidence_only"}
        if v not in valid:
            raise ValueError(f"pick_selection_method deve ser um de: {valid}")
        return v

    @field_validator("plc_area_unit")
    @classmethod
    def validate_plc_area_unit(cls, v: str) -> str:
        valid = {"cm2", "mm2", "px2"}
        if v not in valid:
            raise ValueError(f"plc_area_unit deve ser um de: {valid}")
        return v

    @field_validator("device")
    @classmethod
    def validate_device(cls, v: str) -> str:
        valid_devices = {"cpu", "cuda", "mps", "auto"}
        if v not in valid_devices:
            raise ValueError(f"device deve ser um de: {valid_devices}")
        return v


# ROI padrão: 25% da área do FOV, centralizado (ex.: 640x480 -> 277x277)
# 25% área = sqrt(0.25)=0.5 -> metade de cada lado; 640*0.5=320, 480*0.5=240
# Para 25% mais conservador: sqrt(76800)≈277 (área 76800 = 25% de 307200)
DEFAULT_ROI_QUARTER_AREA: List[int] = [181, 101, 277, 277]  # x, y, w, h (25% de 640x480)


class PreprocessSettings(BaseModel):
    """Configurações de pré-processamento."""

    profile: str = Field(default="default", description="Perfil de pré-processamento")
    brightness: float = Field(default=0.0, ge=-1.0, le=1.0, description="Ajuste de brilho")
    contrast: float = Field(default=0.0, ge=-1.0, le=1.0, description="Ajuste de contraste")
    roi: Optional[List[int]] = Field(default=None, description="ROI [x, y, width, height] em px")
    roi_enabled: bool = Field(
        default=True,
        description="Activa overlay e confinamento do centroide ao ROI",
    )
    roi_unit: str = Field(default="px", description="Unidade ROI: px ou mm")
    roi_calibration_mm_per_px: float = Field(
        default=1.0, ge=0.0001, description="Calibração mm/px: multiplica pixels para obter mm (default 1)"
    )

    @model_validator(mode="before")
    @classmethod
    def _migrate_px_per_mm(cls, data: object) -> object:
        """Migra roi_calibration_px_per_mm (legado) para roi_calibration_mm_per_px."""
        if isinstance(data, dict) and "roi_calibration_px_per_mm" in data:
            data = dict(data)
            px_per_mm = float(data.pop("roi_calibration_px_per_mm"))
            if "roi_calibration_mm_per_px" not in data:
                data["roi_calibration_mm_per_px"] = 1.0 / px_per_mm if px_per_mm else 1.0
        return data


class CIPSettings(BaseModel):
    """Configurações de comunicação CIP."""
    
    ip: str = Field(default="192.168.0.10", description="IP do CLP")
    port: int = Field(default=44818, description="Porta CIP")
    connection_timeout: float = Field(default=10.0, ge=1.0, description="Timeout de conexão (s)")
    timeout_ms: int = Field(default=10000, ge=1000, description="Timeout de operação (ms)")
    retry_interval: float = Field(default=2.0, ge=0.5, description="Intervalo de reconexão (s)")
    max_retries: int = Field(default=3, ge=0, description="Máximo de tentativas (0 = infinito)")
    reconnect_backoff_cap_s: float = Field(default=60.0, ge=1.0, description="Teto backoff reconexão (s)")
    io_retries: int = Field(default=2, ge=0, le=5, description="Tentativas de leitura/escrita por operação")
    simulated: bool = Field(default=False, description="Modo simulado")
    heartbeat_interval: float = Field(default=1.0, ge=0.1, description="Intervalo de heartbeat (s)")
    auto_reconnect: bool = Field(default=True, description="Reconexão automática quando degradado/desconectado")


class ReliabilitySettings(BaseModel):
    """Configurações de resiliência operacional."""

    production_mode: bool = Field(
        default=False,
        description="True: fail-closed, sem fallback SimulatedPLC silencioso",
    )
    auto_start_operation: bool = Field(
        default=False,
        description="Inicia Operação automaticamente após preload do modelo (box PC)",
    )
    plc_sync_on_startup: bool = Field(
        default=True,
        description="Sincroniza FSM com tags do CLP após reboot (estado seguro coerente)",
    )
    inhibit_power_management: bool = Field(
        default=True,
        description="Bloqueia sleep/screensaver do SO durante Operação activa",
    )
    kiosk_fullscreen: bool = Field(
        default=False,
        description="Arranca em fullscreen e restringe Config em production_mode",
    )
    stream_auto_restart: bool = Field(default=True, description="Reinicia captura após UNHEALTHY")
    inference_auto_restart: bool = Field(default=True, description="Reinicia worker após erros consecutivos")


class LoggingSettings(BaseModel):
    """Configurações de logging."""

    max_bytes: int = Field(default=50_000_000, ge=1_000_000, description="Tamanho máx. por ficheiro log")
    backup_count: int = Field(default=10, ge=1, le=100, description="Número de backups rotacionados")


class RobotControlSettings(BaseModel):
    """Configurações da máquina de estados do controle robô/CLP."""
    
    ack_timeout: float = Field(default=5.0, ge=1.0, description="Timeout para ACK do robô (s)")
    pick_timeout: float = Field(default=30.0, ge=5.0, description="Timeout para pick (s)")
    place_timeout: float = Field(default=30.0, ge=5.0, description="Timeout para place (s)")
    authorization_timeout: float = Field(default=30.0, ge=5.0, description="Timeout para autorização CLP (s)")
    bypass_authorization: bool = Field(default=False, description="Bypass autorização CLP (para testes)")


class TagSettings(BaseModel):
    """Mapeamento de TAGs CLP."""
    
    # TAGs de escrita (Visão → CLP)
    VisionReady: str = Field(default="VisionCtrl_VisionReady")
    VisionBusy: str = Field(default="VisionCtrl_VisionBusy")
    VisionError: str = Field(default="VisionCtrl_VisionError")
    VisionHeartbeat: str = Field(default="VisionCtrl_Heartbeat")
    ProductDetected: str = Field(default="PRODUCT_DETECTED")
    CentroidX: str = Field(default="CENTROID_X")
    CentroidY: str = Field(default="CENTROID_Y")
    CentroidAngle: str = Field(default="CENTROID_ANGLE")
    ObjectArea: str = Field(default="OBJECT_AREA")
    Confidence: str = Field(default="CONFIDENCE")
    DetectionCount: str = Field(default="DETECTION_COUNT")
    ProcessingTime: str = Field(default="PROCESSING_TIME")
    VisionEchoAck: str = Field(default="VisionCtrl_EchoAck")
    VisionDataSent: str = Field(default="VisionCtrl_DataSent")
    VisionReadyForNext: str = Field(default="VisionCtrl_ReadyForNext")
    SystemFault: str = Field(default="SYSTEM_FAULT")
    
    # TAGs de leitura (CLP → Visão)
    RobotAck: str = Field(default="ROBOT_ACK")
    RobotReady: str = Field(default="ROBOT_READY")
    RobotError: str = Field(default="ROBOT_ERROR")
    RobotBusy: str = Field(default="RobotStatus_Busy")
    RobotPickComplete: str = Field(default="RobotStatus_PickComplete")
    RobotPlaceComplete: str = Field(default="RobotStatus_PlaceComplete")
    PlcAuthorizeDetection: str = Field(default="RobotCtrl_AuthorizeDetection")
    PlcCycleStart: str = Field(default="RobotCtrl_CycleStart")
    PlcCycleComplete: str = Field(default="RobotCtrl_CycleComplete")
    PlcEmergencyStop: str = Field(default="RobotCtrl_EmergencyStop")
    PlcSystemMode: str = Field(default="RobotCtrl_SystemMode")
    Heartbeat: str = Field(default="SystemStatus_Heartbeat")
    SystemMode: str = Field(default="SystemStatus_Mode")
    
    # TAGs de segurança
    SafetyGateClosed: str = Field(default="Safety_GateClosed")
    SafetyAreaClear: str = Field(default="Safety_AreaClear")
    SafetyLightCurtainOK: str = Field(default="Safety_LightCurtainOK")
    SafetyEmergencyStop: str = Field(default="Safety_EmergencyStop")


class OutputSettings(BaseModel):
    """Configurações de saída de stream (HTTP MJPEG para navegador)."""
    
    rtsp_enabled: bool = Field(default=False, description="Stream HTTP MJPEG habilitado")
    http_port: int = Field(default=8080, description="Porta HTTP para MJPEG (copiar/colar no navegador)")
    http_path: str = Field(default="/stream", description="Path do stream HTTP")


class Settings(BaseSettings):
    """Configurações principais do sistema."""
    
    model_config = SettingsConfigDict(
        env_prefix="BUDDMEYER_",
        env_nested_delimiter="__",
        extra="ignore",
    )
    
    config_version: int = Field(default=1, ge=1, description="Versão do schema YAML")

    # Logging
    log_level: str = Field(default="INFO", description="Nível de log")
    log_file: Optional[str] = Field(default="logs/realtec_vision.log", description="Arquivo de log")
    
    # Subconfigurations
    streaming: StreamingSettings = Field(default_factory=StreamingSettings)
    detection: DetectionSettings = Field(default_factory=DetectionSettings)
    preprocess: PreprocessSettings = Field(default_factory=PreprocessSettings)
    cip: CIPSettings = Field(default_factory=CIPSettings)
    robot_control: RobotControlSettings = Field(default_factory=RobotControlSettings)
    reliability: ReliabilitySettings = Field(default_factory=ReliabilitySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    tags: TagSettings = Field(default_factory=TagSettings)
    output: OutputSettings = Field(default_factory=OutputSettings)
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> "Settings":
        """Carrega configurações de um arquivo YAML."""
        if not yaml_path.exists():
            return cls()
        
        with open(yaml_path, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}
        
        return cls(**config_data)
    
    def to_yaml(self, yaml_path: Path) -> None:
        """Salva configurações em um arquivo YAML."""
        yaml_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(yaml_path, "w", encoding="utf-8") as f:
            yaml.dump(
                self.model_dump(exclude_none=True),
                f,
                default_flow_style=False,
                allow_unicode=True,
                sort_keys=False,
            )
    
    def get_base_path(self) -> Path:
        """Retorna o caminho base do projeto."""
        return Path(__file__).parent.parent

    def resolve_path(self, relative: str) -> Path:
        """Resolve caminho relativo à raiz do pacote."""
        path = Path(relative)
        if path.is_absolute():
            return path
        return self.get_base_path() / path

    def get_log_file_path(self) -> Path:
        """Caminho absoluto do ficheiro de log principal."""
        if not self.log_file:
            return self.get_base_path() / "logs" / "realtec_vision.log"
        return self.resolve_path(self.log_file)

    def get_audit_db_path(self) -> Path:
        """Caminho absoluto da base SQLite de audit."""
        return self.resolve_path("logs/audit.db")
    
    def get_models_path(self) -> Path:
        """Retorna o caminho absoluto do diretório de modelos."""
        base_path = self.get_base_path()
        model_path_str = self.detection.model_path
        
        # Se for caminho relativo, resolve em relação ao base_path
        if Path(model_path_str).is_absolute():
            return Path(model_path_str)
        else:
            return base_path / model_path_str


# Cache global para settings
_settings_instance: Optional[Settings] = None


def get_settings(config_path: Optional[Path] = None, reload: bool = False) -> Settings:
    """
    Retorna a instância de configurações.
    
    Args:
        config_path: Caminho para arquivo YAML de configuração
        reload: Se True, recarrega as configurações
    
    Returns:
        Instância de Settings
    """
    global _settings_instance
    
    # Se reload=True, força recarregar
    if reload:
        _settings_instance = None
    
    if _settings_instance is None:
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        if config_path.exists():
            _settings_instance = Settings.from_yaml(config_path)
        else:
            _settings_instance = Settings()
    
    return _settings_instance
