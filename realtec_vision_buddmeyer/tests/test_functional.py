# -*- coding: utf-8 -*-
"""Testes funcionais do fluxo da aplicação."""

import sys
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

# Garante path do pacote
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class TestApplicationStartup:
    """Testes de inicialização da aplicação."""

    def test_import_main_module(self):
        """Módulo main importa sem erros."""
        import main  # noqa: F401

    def test_config_module_available(self):
        """Módulo config está disponível."""
        from config import get_settings

        s = get_settings(reload=True)
        assert s is not None

    def test_main_window_import(self):
        """MainWindow importa sem erros."""
        from ui.main_window import MainWindow

        assert MainWindow is not None

    def test_configuration_page_import(self):
        """ConfigurationPage importa sem erros."""
        from ui.pages.configuration_page import ConfigurationPage

        assert ConfigurationPage is not None


class TestConfigurationFlow:
    """Testes de fluxo na página de Configuração."""

    def test_open_configuration_page(self, qtbot):
        """Abre página de Configuração e verifica abas."""
        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        assert page._tabs.count() == 5
        # Navega pelas abas
        for i in range(page._tabs.count()):
            page._tabs.setCurrentIndex(i)
            assert page._tabs.currentIndex() == i

    def test_reset_loads_defaults(self, qtbot):
        """Restaurar Padrões carrega valores padrão nos widgets."""
        from ui.pages.configuration_page import ConfigurationPage

        page = ConfigurationPage()
        qtbot.addWidget(page)
        page.show()
        qtbot.waitExposed(page)

        # Altera um valor
        page._inference_fps.setValue(8)
        # Restaura padrões
        qtbot.mouseClick(page._reset_btn, Qt.MouseButton.LeftButton)
        assert page._inference_fps.value() == page._settings.detection.inference_fps
