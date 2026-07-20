#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Realtec Vision Buddmeyer
Sistema de visão computacional para automação de expedição (pick-and-place).

Ponto de entrada principal da aplicação.
Suporta Windows, macOS (Apple Silicon: MPS) e Linux/Ubuntu.
"""

import sys
import asyncio
import platform
from pathlib import Path

# Adiciona diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

# qasync para integração async/await com Qt
try:
    import qasync
    HAS_QASYNC = True
except ImportError:
    HAS_QASYNC = False

from config import get_settings
from core.logger import setup_logging, get_logger


def setup_environment() -> None:
    """Configura o ambiente de execução."""
    # High DPI é habilitado por padrão no Qt 6
    pass


def main() -> int:
    """
    Função principal.
    
    Returns:
        Código de saída
    """
    # Configura ambiente
    setup_environment()
    
    # Carrega configurações
    config_path = Path(__file__).parent / "config" / "config.yaml"
    settings = get_settings(config_path)
    
    # Configura logging
    setup_logging(
        level=settings.log_level,
        log_file=settings.log_file,
        max_bytes=settings.logging.max_bytes,
        backup_count=settings.logging.backup_count,
    )
    
    logger = get_logger("main")
    logger.info("application_starting", version="2.0.0")
    
    # Cria aplicação Qt
    app = QApplication(sys.argv)
    app.setApplicationName("Realtec Vision Buddmeyer")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("Realtec")
    
    # Fonte: Segoe UI no Windows; fontes do sistema em macOS/Linux
    if platform.system() == "Windows":
        font = QFont("Segoe UI", 10)
    else:
        font = QFont()  # Usa fonte padrão do sistema (SF Pro no macOS, Ubuntu/DejaVu no Linux)
        font.setPointSize(10)
    app.setFont(font)
    
    # Importa MainWindow aqui para evitar importações circulares
    from ui.main_window import MainWindow
    
    # Cria janela principal
    window = MainWindow()
    window.show()
    
    logger.info("main_window_displayed")
    
    # Executa com qasync se disponível
    if HAS_QASYNC:
        loop = qasync.QEventLoop(app)
        asyncio.set_event_loop(loop)
        
        with loop:
            exit_code = loop.run_forever()
    else:
        # Fallback para execução síncrona
        logger.warning("qasync_not_available_async_features_limited")
        exit_code = app.exec()
    
    logger.info("application_exiting", exit_code=exit_code)
    
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
