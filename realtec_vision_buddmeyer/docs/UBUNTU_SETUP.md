# Realtec Vision Buddmeyer – uso no Ubuntu

Baseline **v2108**. Índice: [OVERVIEW.md](OVERVIEW.md) · Clone: [CLONE_BOX_PC.md](CLONE_BOX_PC.md) · 24×7: [RUNBOOK_24x7_UBUNTU.md](RUNBOOK_24x7_UBUNTU.md).

## Compatibilidade

O sistema foi desenvolvido para rodar em **macOS**, **Windows** e **Linux/Ubuntu**. Todas as bibliotecas principais (PySide6, PyTorch, OpenCV, aphyt) possuem suporte nativo para Linux.

| Componente | Suporte Ubuntu |
|------------|----------------|
| PySide6 (Qt) | ✅ Nativo (requer libs X11/xcb) |
| PyTorch | ✅ CUDA ou CPU |
| OpenCV | ✅ V4L2 para câmeras USB |
| aphyt (CIP) | ✅ Python puro |
| Harvesters (GenTL) | ⚠️ Depende do CTI do fabricante |

## Requisitos

- Ubuntu 22.04 LTS ou superior (recomendado)
- Python 3.10+
- PyTorch com suporte a **CUDA** (opcional, para GPU NVIDIA) ou CPU

## Dependências de sistema

Antes de instalar as dependências Python, instale as bibliotecas necessárias para PySide6 e OpenCV:

```bash
sudo apt update
sudo apt install -y \
    python3.10-venv \
    python3-pip \
    libxcb-cursor0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    libxcb1 \
    libxcb-glx0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-render-util0 \
    libxcb-util1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    x11-xserver-utils
```

Para **autostart industrial**, instale também `systemd` (incluído no Ubuntu) e use [RUNBOOK_24x7_UBUNTU.md](RUNBOOK_24x7_UBUNTU.md).

## Instalação

1. **Clone** — ver [CLONE_BOX_PC.md](CLONE_BOX_PC.md).

2. **Ambiente virtual** (dentro de `realtec_vision_buddmeyer/`):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Config de campo:** copie o template e edite IP CLP / câmera:
   ```bash
   cp config/config.production.yaml.example config/config.yaml
   ```

4. **Preflight:**
   ```bash
   python scripts/preflight_check.py
   ```

5. **systemd (recomendado em fábrica):**
   ```bash
   sudo deploy/install_systemd.sh /caminho/para/clone
   sudo systemctl start realtec-vision
   ```

## Execução

**Opção 1 – script:**
```bash
chmod +x Iniciar_Realtec_Vision.sh
./Iniciar_Realtec_Vision.sh
```

**Opção 2 – manualmente:**
```bash
cd realtec_vision_buddmeyer
python main.py
```

Ou a partir da raiz do repo:
```bash
python realtec_vision_buddmeyer/main.py
```

## Câmeras USB

No Ubuntu, câmeras USB usam **V4L2** (Video4Linux2). O OpenCV usa esse backend automaticamente.

- Verifique se o dispositivo existe: `ls /dev/video*`
- Liste dispositivos: `v4l2-ctl --list-devices`
- Se o usuário não tiver permissão: `sudo usermod -aG video $USER` (logout/login necessário)

## Câmeras GenTL / GigE

Câmeras industriais (ex.: Omron Sentech GigE) dependem do **CTI (GenICam Transport Layer)** do fabricante. Verifique se o fabricante fornece binários Linux para o seu modelo. Se não houver suporte, use vídeo de arquivo, USB ou RTSP.

## Device de inferência

- Com `device: auto`, o sistema usa **CUDA** em PCs com NVIDIA, **MPS** no Apple Silicon e **CPU** nos demais casos.
- Para forçar CUDA no Ubuntu: `detection.device: cuda`.

## Stream para navegador (MJPEG)

1. Em **Configuração → Saída**, marque **Habilitar stream para navegador**.
2. Salve e inicie o sistema.
3. Copie a URL exibida (ex.: `http://127.0.0.1:8080/stream`) e cole na barra de endereços.

## Problemas comuns

### Erro "Could not load the Qt platform plugin 'xcb'"
Instale as dependências de sistema listadas acima, em especial `libxcb-cursor0`.

### Câmera USB não abre
- Verifique se o usuário está no grupo `video`.
- Teste com `v4l2-ctl --list-devices` e `v4l2-ctl --list-formats-ext -d /dev/video0`.

### Sem GPU NVIDIA
Use `detection.device: cpu` em `config.yaml`; a inferência será mais lenta, mas funcional. Ver riscos de latência em [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md).

### Modelo não carrega
Confirme Git LFS (`git lfs pull`) e o tamanho de `model_best/model.safetensors` (~181 MB).

### Screensaver / sleep durante operação
Com `reliability.inhibit_power_management: true`, o runtime usa `systemd-inhibit`. Desactive também suspensão automática nas definições de energia do Ubuntu.
