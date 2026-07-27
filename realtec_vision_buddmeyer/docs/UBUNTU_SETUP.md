# Realtec Vision Buddmeyer – uso no Ubuntu

Baseline **v1607**. Índice: [OVERVIEW.md](OVERVIEW.md) · Modelo: [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md) · Clone: [CLONE_BOX_PC.md](CLONE_BOX_PC.md).

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
    libxrender1
```

## Instalação

1. **Clone ou abra o projeto** e entre na pasta raiz do repositório.

2. **Crie e ative um ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências Python:**
   ```bash
   pip install -r realtec_vision_buddmeyer/requirements.txt
   ```

   Para GPU NVIDIA (CUDA):
   ```bash
   pip install torch torchvision
   ```

4. **Configuração:** edite `realtec_vision_buddmeyer/config/config.yaml` se necessário:
   - `streaming.source_type`: use `video`, `usb` ou `rtsp`.
   - `streaming.video_path`: caminho relativo ou absoluto.
   - `detection.device`: `auto` (usa CUDA se disponível), `cuda` ou `cpu`.

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
