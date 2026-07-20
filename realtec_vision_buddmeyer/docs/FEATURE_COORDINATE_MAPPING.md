# FEATURE: Mapeamento de coordenadas (v1 scale)

| Campo | Valor |
|--------|--------|
| **Estado** | implementado |
| **Etapa plano** | 4 |

## 1. Contexto

Conversão px→mm estava duplicada em quatro módulos com risco de divergência na integração Omron.

## 2. Objetivo

Módulo `coordinate/` com modo **scale** (`mm_per_px`); único ponto para envio CLP; display UI usa mesma escala.

**Não-objectivos:** homografia, calibração affine em campo (P2).

## 3. Requisitos (P0)

| ID | Descrição |
|----|-----------|
| RF-01 | `CoordinateTransform.vision_to_robot(x_px, y_px, ...)` |
| RF-02 | `get_coordinate_transform()` cacheado a partir de settings |
| RF-03 | `robot_controller`, overlay, status panel usam transform |
| RF-04 | Clamp ROI antes da conversão (mantido em controller) |

## 6. Módulos

- `coordinate/transform.py`, `coordinate/models.py`
- Consumidores: `robot_controller`, `inference_engine`, `operation_page`, `status_panel`

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | Escala 10 mm/px coerente | `test_coordinate_transform.py` |
| CA-02 | TAG_CONTRACT v1.1 documenta mm | `docs/TAG_CONTRACT.md` |
