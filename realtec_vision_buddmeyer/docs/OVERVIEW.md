# Visão geral — Realtec Vision Buddmeyer

Sistema de visão industrial pick-and-place: captura por **câmera USB/GenTL**, segmentação Mask2Former, handshake FSM com CLP Omron.

**Repo:** `Projeto_VC_Buddmeyer_v1607` — ver [MIGRACAO_PROJETO_VC_BUDDMEYER_v1607.md](MIGRACAO_PROJETO_VC_BUDDMEYER_v1607.md).

## Fluxo operacional

1. Captura vídeo (USB ou GenTL).
2. Inferência segmentação (FPS configurável).
3. PickStabilizer + seleção de alvo.
4. FSM envia coordenadas ao CLP (caminho único).

## Documentação

| Área | Documento |
|------|-----------|
| Operador | [GUIA_OPERADOR.md](GUIA_OPERADOR.md) |
| Técnica | [REFERENCE.md](REFERENCE.md) |
| CLP / tags | [TAG_CONTRACT.md](TAG_CONTRACT.md) v1.1 |
| Integração CLP | [RUNBOOK_INTEGRACAO_CLP.md](RUNBOOK_INTEGRACAO_CLP.md) |
| Pipeline visão | [SEGMENTATION_PIPELINE.md](SEGMENTATION_PIPELINE.md) |
| GenTL | [MANUAL_GENTL(GIGE).md](MANUAL_GENTL(GIGE).md) |
| Roadmap 24×7 | [AVALIACAO_24x7_PICK_PLACE.md](AVALIACAO_24x7_PICK_PLACE.md) |

### Features implementadas (resiliência FSM)

| Etapa | Spec |
|-------|------|
| 1 Handshake | [FEATURE_FSM_HANDSHAKE_HARDENING.md](FEATURE_FSM_HANDSHAKE_HARDENING.md) |
| 2 Produção | [FEATURE_PRODUCTION_MODE.md](FEATURE_PRODUCTION_MODE.md) |
| 3 Pick estável | [FEATURE_PICK_STABILIZER.md](FEATURE_PICK_STABILIZER.md) |
| 4 Coordenadas | [FEATURE_COORDINATE_MAPPING.md](FEATURE_COORDINATE_MAPPING.md) |
| Pick / paralaxe | [FEATURE_PICK_SELECTION_PARALLAX.md](FEATURE_PICK_SELECTION_PARALLAX.md) |

## UI (jul/2026)

- **Operação:** câmera USB ou GenTL; índice USB inline.
- **Configuração → Câmera:** parâmetros da fonte activa.
- **Configuração → Detecção:** modelo, confiança, FPS, estabilização.
- **Configuração → Imagem:** ROI (px) + calibração mm/px.

## Validação

```bash
cd realtec_vision_buddmeyer
python -m pytest tests/ -q
python -m scripts.validate_handshake
```
