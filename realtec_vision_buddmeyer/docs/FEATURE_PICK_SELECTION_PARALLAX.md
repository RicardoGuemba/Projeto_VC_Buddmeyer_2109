# FEATURE: Seleção pick por paralaxe (método configurável)

| Campo | Valor |
|--------|--------|
| **Autor** | Realtec |
| **Data** | 2026-07-15 |
| **Estado** | implementado |
| **Issue / ticket** | — |

---

## 1. Contexto e problema

- **Situação atual:** o sistema detectava múltiplas embalagens mas exibia e enviava ao CLP apenas uma, com seleção por score ponderado fixo; área no CLP em mm².
- **Utilizador afetado:** operador (overlay), integração CLP (pick), manutenção (calibração).
- **Porque agora:** no mesmo container, SKUs iguais têm áreas aparentes diferentes por paralaxe; o mais próximo da câmera deve ser priorizado no pick.

---

## 2. Objetivo

- **Objetivo principal:** detectar todos os objetos com centroide (mm) e área (cm²); enviar ao CLP apenas o alvo selecionável por método (default: maior área, desempate confiança).
- **Não-objectivos:** array de N alvos no CLP; correção 3D de paralaxe; classificação por SKU distinto.

---

## 3. Requisitos funcionais

| ID | Descrição | Prioridade |
|----|-----------|------------|
| RF-01 | Overlay mostra todas as detecções com mm e cm² | P0 |
| RF-02 | Método `area_then_conf` como default | P0 |
| RF-03 | Métodos alternativos: weighted_score, area_only, confidence_only | P0 |
| RF-04 | CLP recebe um único alvo; DetectionCount = total | P0 |
| RF-05 | OBJECT_AREA configurável (default cm²) | P1 |

---

## 4. Requisitos não-funcionais

- Seleção determinística por frame; log `pick_target_selected`.
- Config em `config.yaml` + UI Configuração → Detecção.
- Migração de `prioritize_area` legado.

---

## 5. Contratos e dados

**Config (`detection`):**
- `pick_selection_method`: `area_then_conf` | `weighted_score` | `area_only` | `confidence_only`
- `pick_confidence_weight`, `pick_area_weight` (weighted_score)
- `plc_area_unit`: `cm2` | `mm2` | `px2` (default `cm2`)

**CLP:** tags existentes; `OBJECT_AREA` em unidade configurada.

---

## 6. Desenho técnico

- `detection/pick_selection.py` — seleção e conversão
- `detection/events.py` — `DetectionEvent.all_detections_scaled`
- `inference_engine`, `robot_controller`, UI overlay

---

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | Overlay multi-objeto mm/cm² | Manual / UI |
| CA-02 | Default area_then_conf | `tests/test_pick_selection.py` |
| CA-03 | Troca de método na config | UI + pytest settings |
| CA-04 | CLP um alvo, count total | robot_controller |
| CA-05 | OBJECT_AREA cm² default | config + testes |
| CA-06 | 4 métodos cobertos | pytest |

---

## 11. Checklist

- [x] `pick_selection.py`
- [x] Config + migração
- [x] Pipeline + CLP
- [x] UI overlay + status + config page
- [x] Testes pytest
- [x] TAG_CONTRACT atualizado
