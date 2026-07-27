# Modelo de visão — Mask2Former (Embalagem)

Documento de referência do modelo usado pelo Realtec Vision Buddmeyer (baseline **v1607**, app **v2.0.0**).

Pipeline de runtime e geometria: [SEGMENTATION_PIPELINE.md](SEGMENTATION_PIPELINE.md).  
Instalação dos pesos (Git LFS): [CLONE_BOX_PC.md](CLONE_BOX_PC.md).

---

## 1. Identificação e versão

| Campo | Valor |
|--------|--------|
| Arquitetura | `Mask2FormerForUniversalSegmentation` |
| `model_type` | `mask2former` |
| Backbone | Swin-T (`depths: [2, 2, 6, 2]`, `embed_dim: 96`) |
| Task | `instance_segmentation` (`model_best/task.json`) |
| Classes | 1 — **`Embalagem`** (`id2label: {"0": "Embalagem"}`) |
| Pesos | `model_best/model.safetensors` (~181 MB, Git LFS) |
| Metadados | `config.json`, `preprocessor_config.json`, `task.json` |
| Transformers (export) | `4.57.3` (`transformers_version` em `config.json`) |
| Processor | `Mask2FormerImageProcessor`, resize **384×384** |
| Path runtime | `detection.model_path: model_best` (`config/config.yaml`) |
| Confiança shipped | `detection.confidence_threshold: 0.61` |

Artefacto local; não há URL de dataset nem repositório Hugging Face de fine-tune versionado neste repo.

---

## 2. Quem desenvolveu

| Camada | Responsável | Notas |
|--------|-------------|--------|
| Arquitetura base Mask2Former | **Meta AI** (Facebook Research) | Paper / modelo universal de segmentação |
| Runtime Hugging Face | **Hugging Face Transformers** | Loader: `detection/model_loader.py` |
| Fine-tune classe `Embalagem` | **Cliente** (conforme documentação do projeto) | Pesos entregues em `model_best/`; origem do dataset **não rastreada** no repositório |
| Integração no app | **Realtec** | Pipeline, pick, FSM, tags CLP |

Rastreabilidade: os pesos vivem como artefacto LFS. O ficheiro `training_args.bin` **não** faz parte do conjunto mínimo documentado para clone/deploy.

Se a atribuição do fine-tune for outra (Realtec interno / fornecedor), atualizar esta secção e manter o resto do contrato técnico.

---

## 3. Características principais

- **Instance segmentation** com máscara por instância (não só bounding box).
- Saídas usadas no pick-and-place (derivadas da máscara):
  - Centróide geométrico (X, Y)
  - Ângulo do eixo maior via PCA (`[0, 180)`)
  - Área (px → cm²/mm² via calibração) para priorização por paralaxe
- Filtro de classe alinhado ao domínio: `target_classes: [Embalagem]`.
- Device automático: MPS / CUDA / CPU (`detection.device: auto`).
- Integração a jusante: PickStabilizer, seleção de pick, `CoordinateTransform` (scale), tags CIP.

Alias de hub suportado pelo loader (fallback / referência): `facebook/mask2former-swin-tiny-coco-instance` — o **runtime de produção** usa a pasta local `model_best/`.

---

## 4. Por que usar neste projeto

1. **Embalagens irregulares / rotacionadas** — centróide e ângulo da máscara são mais estáveis que o centro do bbox.
2. **Uma classe de domínio** — simplifica pós-processamento e contrato com o CLP (pose + área + confiança).
3. **Paralaxe por área aparente** — maior máscara tende a ser o objeto mais próximo da câmera no stack.
4. **Já endurecido no app** — handshake FSM, production_mode, stabilizer e recovery de stream/inferência cobertos por specs e testes na v1607.
5. **Deployável em box PC** — Swin-T + 384×384 é um compromisso razoável entre qualidade e latência (GPU/MPS preferível a CPU pura).

---

## 5. Riscos

| Risco | Impacto | Mitigação |
|-------|---------|-----------|
| **Domain shift** (iluminação, SKU novo, fundo de linha) | Misses / falsos positivos | Recalibrar threshold; re-treinar com dados do campo; ROI |
| **Threshold mal calibrado** | Ciclos vazios ou picks errados | Logs `inference_diagnostic`; default 0.61 como ponto de partida |
| **Latência em CPU** | FPS baixo, handshake atrasado | Preferir CUDA/MPS; reduzir `inference_fps` / resolução GenTL |
| **Residuais COCO no preprocessor** (`num_labels: 80`) vs head 1-classe | Confusão operacional ao inspecionar configs | Confiar em `task.json` + `id2label` top-level; não misturar labels ImageNet do backbone |
| **Clone LFS incompleto** | App não carrega modelo | `git lfs pull`; validar tamanho ~181 MB de `model.safetensors` |
| **Sem soak 72 h documentado** | Degradação só aparece em campo | Ver critérios em [AVALIACAO_24x7_PICK_PLACE.md](AVALIACAO_24x7_PICK_PLACE.md) |
| **Calibração só scale** | Erro de pose se câmera inclinada / hand-eye real | Affine/homography ainda no backlog |
| **Modelo opaco sem dataset versionado** | Dificulta auditoria / reprodução de treino | Versionar dataset e recipe fora do app; tagar pesos |

---

## 6. Operação e troca de modelo

1. Colocar pasta completa em `model_best/` (ou outro path e atualizar `detection.model_path`).
2. Garantir `task.json` com `"task": "instance_segmentation"`.
3. Alinhar `target_classes` ao `id2label` do novo modelo.
4. Ajustar `confidence_threshold` na UI (Configuração → Detecção) ou YAML.
5. Validar com `python -m scripts.check_model` / smoke de segmentação e um ciclo SimulatedPLC.

UI: **Configuração → Detecção**.  
Operador: [GUIA_OPERADOR.md](GUIA_OPERADOR.md).

---

## 7. Documentos relacionados

| Documento | Uso |
|-----------|-----|
| [SEGMENTATION_PIPELINE.md](SEGMENTATION_PIPELINE.md) | Pipeline e geometria |
| [REFERENCE.md](REFERENCE.md) | Chaves `detection.*` |
| [CLONE_BOX_PC.md](CLONE_BOX_PC.md) | LFS / instalação |
| [FEATURE_PICK_SELECTION_PARALLAX.md](FEATURE_PICK_SELECTION_PARALLAX.md) | Escolha do alvo |
| [FEATURE_PICK_STABILIZER.md](FEATURE_PICK_STABILIZER.md) | Estabilidade multi-frame |
| [AVALIACAO_24x7_PICK_PLACE.md](AVALIACAO_24x7_PICK_PLACE.md) | Prontidão 24×7 |

---

© Realtec — Buddmeyer Vision System v2.0 (baseline v1607)
