# FEATURE: Pega VCPn e heading 0–360

| Campo | Valor |
|--------|--------|
| **Autor** | Realtec |
| **Data** | 2026-09-19 |
| **Estado** | implementado |

## 1. Contexto

O pick usava o centroide da máscara e `CENTROID_ANGLE` em `[0, 180)` sem sentido. O pico da embalagem fica a 55 mm do centro no eixo maior.

## 2. Objetivo

Enviar ao NX102 o **VCPn** como XY de pega e o heading **0–360°** (leste=0, norte=90).

**Não-objectivos:** tags Sysmac novas, wrap ±180 no robô, homografia.

## 3. Requisitos

| ID | Descrição | Prioridade |
|----|-----------|------------|
| RF-01 | VCPn / VCP_s a `vcp_offset_mm` no eixo maior | P0 |
| RF-02 | VCPn = extremo mais perto da mediana do topo do ROI (fallback FOV `W/2, 0`) | P0 |
| RF-03 | `CENTROID_X/Y` = VCPn (após clamp colinear com ângulo de eixo 0–180) | P0 |
| RF-04 | `CENTROID_ANGLE` = atan2(-dy, dx) de C→VCPn em `[0, 360)` | P0 |
| RF-05 | `vcp_offset_mm=0` restaura pick no centroide | P0 |

## 5. Configuração

`detection.vcp_offset_mm` (default 55), `detection.vcp_reference` (`roi_top_mid` \| `fov_top_mid`).

## 8. Aceitação

| ID | Critério | Teste |
|----|----------|--------|
| CA-01 | Distância C–VCPn ≈ offset/mm_per_px | `test_vcp_geometry.py` |
| CA-02 | VCPn mais perto da referência que VCP_s | `test_vcp_geometry.py` |
| CA-03 | Headings 0/90/180/270 | `test_vcp_geometry.py` |
| CA-04 | Evento FSM/PLC usa VCPn e heading | `test_events_segmentation.py` |
| CA-05 | Estabilizador segue o pico | `test_pick_stabilizer.py` |
