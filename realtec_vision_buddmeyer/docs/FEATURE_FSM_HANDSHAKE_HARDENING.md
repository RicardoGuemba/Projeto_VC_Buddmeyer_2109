# FEATURE: Handshake FSM íntegro

| Campo | Valor |
|--------|--------|
| **Estado** | implementado |
| **Etapa plano** | 1 |

## 1. Contexto

O envio periódico de coordenadas ao CLP fora da FSM quebrava o contrato handshake e podia disparar picks não autorizados.

## 2. Objetivo

Um único caminho CLP via `RobotController`: detecções só entram em `DETECTING`; falhas expõem `VisionBusy` / fault tags.

**Não-objectivos:** `production_mode`, PickStabilizer, audit SQLite.

## 3. Requisitos (P0)

| ID | Descrição |
|----|-----------|
| RF-01 | Remover `_communicate_centroid_to_plc` do loop de frames |
| RF-02 | `accepting_detections` True só em `DETECTING` |
| RF-03 | `process_detection` ignorado fora de `DETECTING` |
| RF-04 | `RobotError` → estado `ERROR` + fault tags |
| RF-05 | `VisionBusy` sincronizado com estados activos |

## 6. Módulos

- `control/robot_controller.py`
- `communication/cip_client.py`
- `ui/pages/operation_page.py`
- `tests/test_fsm_handshake.py`

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | Zero writes CLP periódicos fora FSM | grep + teste manual simulado |
| CA-02 | Ciclo contínuo SimulatedPLC completa | `test_fsm_handshake.py` |
| CA-03 | Fault tags em erro simulado | `test_robot_error_sets_fault` |
