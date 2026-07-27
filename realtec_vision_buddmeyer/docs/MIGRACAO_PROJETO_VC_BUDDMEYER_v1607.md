# Migração — Projeto_VC_Buddmeyer_v1607

**Repositório de desenvolvimento activo (jul/2026):**

`/Users/ricardoguembarovski/Documents/Documentos_MacBook_Pro/Realtec/Projeto_VC_Buddmeyer_v1607`

Baseline anterior: `Realtec_Vision_Buddmeyer_verofi` (mesmo código; este repo contém o pacote completo).

## Validação após clone/migração

```bash
cd Projeto_VC_Buddmeyer_v1607/realtec_vision_buddmeyer
python -m pytest tests/ -q
python -m scripts.validate_handshake
```

## Documentação canónica

| Documento | Propósito |
|-----------|-----------|
| [OVERVIEW.md](OVERVIEW.md) | Índice geral |
| [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md) | Modelo de visão (versão, riscos) |
| [REFERENCE.md](REFERENCE.md) | Referência técnica |
| [TAG_CONTRACT.md](TAG_CONTRACT.md) | Contrato CLP v1.1 |
| [RUNBOOK_INTEGRACAO_CLP.md](RUNBOOK_INTEGRACAO_CLP.md) | Deploy pré-CLP |
| [AVALIACAO_24x7_PICK_PLACE.md](AVALIACAO_24x7_PICK_PLACE.md) | Status 24×7 (P0 feito; aceitação aberta) |
| `FEATURE_*.md` | Specs por etapa FSM |

## Limpeza de artefactos

Removidos do conjunto mínimo de deploy quando não usados em runtime: `model_best/training_args.bin`, `.DS_Store`. Pesos obrigatórios: `model.safetensors` + `config.json` + `preprocessor_config.json` + `task.json`.
