# Clonar e executar — baseline v2108 (Guilherme)

Este guia cobre o **Vision Buddmeyer** (`realtec_vision_buddmeyer`) no **portátil** e no **box PC do POC Buddmeyer**, com o modelo **Mask2Former** incluído no repositório via **Git LFS**.

Repositório privado:

```text
https://github.com/RicardoGuemba/Realtec_Vision_Buddmeyer_v2108.git
```

Acesso: convite de collaborator (GitHub user `Schilipake`). Aceitar o e-mail/convite do GitHub antes do clone.

## O que vai descarregar

- Código-fonte (pasta `realtec_vision_buddmeyer/`).
- Metadados do modelo em `model_best/` (`config.json`, `preprocessor_config.json`, `task.json`).
- **Pesos:** `model_best/model.safetensors` (~**181 MB**). Não são “só alguns bytes”: o ficheiro é grande; por isso está em **Git LFS** (limite do GitHub para blobs normais é 100 MB).
- Detalhe do modelo: [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md).

## Pré-requisitos

1. **Git** (2.x ou superior): [https://git-scm.com/downloads](https://git-scm.com/downloads)
2. **Git LFS** (obrigatório para receber os pesos):
   - Windows: instalador em [https://git-lfs.com](https://git-lfs.com) ou `winget install Git.GitLFS`
   - Linux: `sudo apt install git-lfs` (Debian/Ubuntu) e depois `git lfs install` uma vez por utilizador
   - macOS: `brew install git-lfs` e `git lfs install`
3. **Python 3.11 ou 3.12** (64 bits): [https://www.python.org/downloads/](https://www.python.org/downloads/)  
   Marque “Add Python to PATH” no instalador Windows.
4. **Câmera USB** (portátil / POC USB) ou **GenTL** (POC industrial) e permissões de câmera.

## Clone comum (os dois computadores)

```bash
git lfs install
git clone https://github.com/RicardoGuemba/Realtec_Vision_Buddmeyer_v2108.git
cd Realtec_Vision_Buddmeyer_v2108
git lfs pull
```

Confirme que o ficheiro de pesos é real (não 130 bytes de “pointer”):

```bash
# Windows PowerShell
(Get-Item realtec_vision_buddmeyer\model_best\model.safetensors).Length

# Linux / macOS
ls -lh realtec_vision_buddmeyer/model_best/model.safetensors
```

Deve mostrar aproximadamente **181 MB**. Se vir ~130 bytes, corra de novo `git lfs pull` na raiz do clone.

---

## Caminho A — Portátil (desenvolvimento / validação)

Sem CLP Omron na rede: usar modo simulado.

```bash
cd realtec_vision_buddmeyer
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Em `config/config.yaml`:

- `streaming.usb_camera_index`: índice da USB no OpenCV (0, 1, 2…).
- `detection.model_path`: `model_best` (após `git lfs pull`).
- `cip.simulated: true` para testar **sem** CLP real.

Arranque:

```bash
python main.py
```

Atalhos na raiz do repo: `Iniciar Realtec Vision.command` (macOS) ou `./Iniciar_Realtec_Vision.sh`.

Smoke só visão:

```bash
python -m scripts.smoke_test_segmentation --frames 5 --camera 0 --confidence 0.5
```

---

## Caminho B — POC Buddmeyer (box PC Ubuntu)

Usar o template de produção e o runbook 24×7.

```bash
cd realtec_vision_buddmeyer
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp config/config.production.yaml.example config/config.yaml
# Editar IP do CLP, câmera USB/GenTL e CTI
python scripts/preflight_check.py
```

Autostart (opcional, recomendado no POC):

```bash
sudo deploy/install_systemd.sh /caminho/para/Realtec_Vision_Buddmeyer_v2108
sudo systemctl start realtec-vision
sudo systemctl status realtec-vision
```

Detalhe de systemd, recovery pós-queda e `/health`: [RUNBOOK_24x7_UBUNTU.md](RUNBOOK_24x7_UBUNTU.md).

---

## Ambiente Python (Windows extra)

**Windows (cmd):**

```bat
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### PyTorch

O `requirements.txt` instala `torch` a partir do PyPI. Num PC **só CPU**, isso costuma ser suficiente. Se precisar de **CUDA**, siga a matriz oficial da PyTorch: [https://pytorch.org/get-started/locally/](https://pytorch.org/get-started/locally/)

## Testes automáticos (opcional)

```bash
cd realtec_vision_buddmeyer
pip install pytest pytest-qt
python -m pytest tests/ -q
```

## Documentação adicional

- Índice: [OVERVIEW.md](OVERVIEW.md)
- Modelo Mask2Former: [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md)
- Pipeline de segmentação: [SEGMENTATION_PIPELINE.md](SEGMENTATION_PIPELINE.md)
- Contrato de tags CLP: [TAG_CONTRACT.md](TAG_CONTRACT.md)
- Campo Ubuntu 24×7: [RUNBOOK_24x7_UBUNTU.md](RUNBOOK_24x7_UBUNTU.md)

## Resumo para o Guilherme

| Passo | Portátil | POC Ubuntu |
|--------|----------|------------|
| 1 | Instalar Git + **Git LFS** | Igual |
| 2 | Aceitar convite GitHub (`Schilipake`) | Igual (mesma conta ou PAT) |
| 3 | `git clone` + `git lfs pull` | Igual |
| 4 | venv + `pip install -r requirements.txt` | Igual |
| 5 | `cip.simulated: true` se não houver CLP | Copiar `config.production.yaml.example` → `config.yaml` |
| 6 | `python main.py` | `preflight_check.py` + systemd |

Em caso de falha no `git lfs pull` (firewall, proxy corporativo), peça à equipa IT abertura para `github.com` e `github-cloud.githubusercontent.com` ou use um pacote offline com a pasta `model_best` completa copiada de outra máquina.
