# Realtec Vision Buddmeyer – uso no macOS (Apple Silicon M1/M2/M3/M4)

Baseline **v1607**. Índice: [OVERVIEW.md](OVERVIEW.md) · Modelo: [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md) · Clone: [CLONE_BOX_PC.md](CLONE_BOX_PC.md).

## Requisitos

- macOS 12+ (Monterey ou superior recomendado)
- Python 3.10+ (3.11/3.12 preferível)
- PyTorch com suporte a **MPS** (Metal Performance Shaders) para aceleração no Apple Silicon
- Git LFS se clonar o repositório (pesos em `model_best/`)

## Instalação

1. **Clone ou abra o projeto** e entre na pasta raiz do repositório.

2. **Crie e ative um ambiente virtual:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r realtec_vision_buddmeyer/requirements.txt
   ```

   Para melhor desempenho no M4, use PyTorch com MPS (já incluso em builds recentes do PyTorch para macOS):
   ```bash
   pip install torch torchvision
   ```

4. **Configuração:** edite `realtec_vision_buddmeyer/config/config.yaml` se necessário:
   - `streaming.source_type`: use `video`, `usb` ou `rtsp` (GenTL/GigE costuma ser específico de Windows).
   - `streaming.video_path`: caminho relativo, ex.: `videos/Colcha.mp4`, ou absoluto.
   - `detection.device`: `auto` (usa MPS no M4 quando disponível), ou `mps`, ou `cpu`.

## Execução

**Opção 1 – duplo-clique (recomendado):**
- Na raiz do repositório, dê **duplo-clique** em **`Iniciar Realtec Vision.command`**.
- O Terminal abrirá e o sistema será iniciado (venv ativado automaticamente se existir).

**Opção 2 – script no Terminal:**
```bash
chmod +x Iniciar_Realtec_Vision.sh
./Iniciar_Realtec_Vision.sh
```

**Opção 3 – manualmente:**
```bash
cd realtec_vision_buddmeyer
python main.py
```

Ou a partir da raiz do repo:
```bash
python realtec_vision_buddmeyer/main.py
```

## Device de inferência (MPS)

- Com `device: auto`, o sistema usa **CUDA** em PCs com NVIDIA, **MPS** no Apple Silicon (M1/M2/M3/M4) e **CPU** nos demais casos.
- Para forçar MPS: em `config.yaml`, defina `detection.device: mps`.
- Se houver falhas com MPS, use `detection.device: cpu`.

## Stream para navegador (MJPEG)

Para visualizar o vídeo com detecções no navegador:

1. Em **Configuração → Saída**, marque **Habilitar stream para navegador**.
2. Salve e inicie o sistema.
3. Copie a URL exibida (ex.: `http://127.0.0.1:8080/stream`) e cole na barra de endereços do Chrome, Firefox ou Safari.

**No macOS:** use `http://127.0.0.1:8080/stream` para acesso no mesmo PC. Se não funcionar, verifique se o firewall permite conexões de entrada na porta configurada (Preferências do Sistema → Segurança e Privacidade → Firewall).

## Observações

- **GenTL / câmeras GigE:** drivers e CTI são em geral fornecidos para Windows. No Mac, use câmera **USB** (aba Operação) ou configure fontes de lab via YAML.
- **Caminhos:** use sempre `/` ou `pathlib.Path`; evite `C:\` ou barras invertidas.
- **Logs:** por padrão em `realtec_vision_buddmeyer/logs/realtec_vision.log` (criado em tempo de execução).
- **Modelo:** ver [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md); confirme `git lfs pull` se `model.safetensors` tiver ~130 bytes.
