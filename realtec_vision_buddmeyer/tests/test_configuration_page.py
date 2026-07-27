# -*- coding: utf-8 -*-
"""Testes unitários da página de Configuração."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from pytestqt.qtbot import QtBot

from ui.pages.configuration_page import ConfigurationPage, CONFIG_GROUP_STYLE


@pytest.fixture
def config_page(qtbot):
    """Cria ConfigurationPage para testes."""
    page = ConfigurationPage()
    qtbot.addWidget(page)
    return page


class TestConfigurationPage:
    """Testes da ConfigurationPage."""

    def test_page_creates_successfully(self, config_page):
        """Página é criada sem erros."""
        assert config_page is not None
        assert config_page._tabs is not None

    def test_has_all_tabs(self, config_page):
        """Todas as abas esperadas existem."""
        tab_names = [config_page._tabs.tabText(i) for i in range(config_page._tabs.count())]
        assert "Câmera" in tab_names
        assert "Detecção" in tab_names
        assert "Imagem" in tab_names
        assert "CLP" in tab_names
        assert "Saída" in tab_names

    def test_has_action_buttons(self, config_page):
        """Botões Restaurar, Salvar e Sair existem."""
        assert config_page._reset_btn is not None
        assert config_page._save_btn is not None
        assert config_page._exit_btn is not None
        assert config_page._exit_btn.text() == "Sair"

    def test_reset_button_clickable(self, qtbot, config_page):
        """Botão Restaurar Padrões é clicável."""
        config_page.show()
        qtbot.waitExposed(config_page)
        qtbot.mouseClick(config_page._reset_btn, Qt.MouseButton.LeftButton)
        # Não deve lançar exceção

    def test_config_group_style_defined(self):
        """CONFIG_GROUP_STYLE está definido (ISA-101)."""
        assert CONFIG_GROUP_STYLE
        assert "QGroupBox" in CONFIG_GROUP_STYLE
        assert "border" in CONFIG_GROUP_STYLE
        assert "background-color" in CONFIG_GROUP_STYLE

    def test_output_tab_has_copy_url(self, config_page):
        """Aba Saída tem botão Copiar URL que gera URL HTTP válida."""
        url = config_page._get_stream_url()
        assert url.startswith("http://")
        assert config_page._http_path.text() in url or "/stream" in url

    def test_copy_stream_url_to_clipboard(self, config_page):
        """Copiar URL cola conteúdo HTTP válido na área de transferência."""
        from PySide6.QtWidgets import QApplication

        config_page._tabs.setCurrentIndex(4)  # Aba Saída
        config_page._copy_stream_url()
        clipboard = QApplication.clipboard()
        assert clipboard.text().startswith("http://")
        assert "/stream" in clipboard.text()

    def test_get_stream_url_uses_custom_path(self, config_page):
        """_get_stream_url honra http_path da UI."""
        config_page._http_path.setText("/cam")
        config_page._http_port.setValue(9090)
        url = config_page._get_stream_url()
        assert url.endswith(":9090/cam")
        assert "/stream" not in url.split("9090", 1)[-1]

    def test_save_persists_custom_http_path(self, config_page, monkeypatch):
        """Salvar não força /stream; persiste path custom e emite settings_saved."""
        from PySide6.QtWidgets import QMessageBox
        from config.settings import Settings

        monkeypatch.setattr(
            QMessageBox, "information", lambda *a, **k: QMessageBox.Ok
        )

        saved = {}

        def fake_to_yaml(self, path):
            saved["path"] = str(path)
            saved["http_path"] = self.output.http_path
            saved["rtsp_enabled"] = self.output.rtsp_enabled
            saved["http_port"] = self.output.http_port

        monkeypatch.setattr(Settings, "to_yaml", fake_to_yaml)

        config_page._http_path.setText("/video")
        config_page._http_port.setValue(18080)
        config_page._rtsp_enabled.setChecked(True)

        emitted = []
        config_page.settings_saved.connect(lambda: emitted.append(True))
        config_page._save_settings()

        assert saved["http_path"] == "/video"
        assert saved["http_port"] == 18080
        assert saved["rtsp_enabled"] is True
        assert emitted == [True]
        assert config_page._http_path.text() == "/video"

    def test_copy_stream_url_enables_and_emits(self, config_page, monkeypatch):
        """Copiar URL liga stream, persiste e emite settings_saved."""
        from PySide6.QtWidgets import QMessageBox

        monkeypatch.setattr(
            QMessageBox, "information", lambda *a, **k: QMessageBox.Ok
        )
        monkeypatch.setattr(config_page, "_persist_output_yaml", lambda: None)

        emitted = []
        config_page.settings_saved.connect(lambda: emitted.append(True))
        config_page._copy_stream_url()

        assert config_page._settings.output.rtsp_enabled is True
        assert emitted == [True]
        assert config_page._get_stream_url(localhost=True).startswith("http://127.0.0.1:")

    def test_imagem_tab_has_roi(self, config_page):
        """Aba Imagem tem configuração de ROI."""
        assert config_page._roi_x is not None
        assert config_page._roi_y is not None
        assert config_page._roi_w is not None
        assert config_page._roi_h is not None
        assert config_page._roi_enabled is not None

    def test_roi_in_pixels(self, config_page):
        """ROI é sempre em pixels; coordenadas X,Y,W,H são inteiros."""
        config_page._tabs.setCurrentIndex(2)  # Aba Imagem
        config_page._roi_x.setValue(100)
        config_page._roi_y.setValue(50)
        config_page._roi_w.setValue(200)
        config_page._roi_h.setValue(200)
        assert config_page._roi_x.value() == 100
        assert config_page._roi_y.value() == 50

    def test_centroid_mm_per_px_accepts_values(self, config_page):
        """Centroide (mm/px) aceita valores; default 1; 100 multiplica px por 100."""
        config_page._tabs.setCurrentIndex(2)
        assert config_page._centroid_mm_per_px.value() == pytest.approx(1.0)
        config_page._centroid_mm_per_px.setValue(100.0)
        assert config_page._centroid_mm_per_px.value() == pytest.approx(100.0)
