# FEATURE: Resiliência Ubuntu 24×7

| Campo | Valor |
|--------|--------|
| **Estado** | implementado |
| **Baseline** | v2108 |

## 1. Contexto

Box PC Ubuntu em fábrica precisa autostart, imunidade a sleep/screensaver, recovery seguro pós-queda de energia e deploy clone-friendly.

## 3. Requisitos (P0)

| ID | Descrição |
|----|-----------|
| RF-01 | `ReliabilitySettings`: `auto_start_operation`, `plc_sync_on_startup`, `inhibit_power_management`, `kiosk_fullscreen` |
| RF-02 | `control/plc_recovery.py` — mapeamento tags CLP → estado FSM seguro |
| RF-03 | `RobotController.prepare_plc_recovery_state()` + `start(initial_state=...)` |
| RF-04 | `core/power_guard.py` — systemd-inhibit + fallback xset |
| RF-05 | `deploy/realtec-vision.service` + `install_systemd.sh` |
| RF-06 | `scripts/preflight_check.py` (ExecStartPre) |
| RF-07 | `GET /health` no servidor MJPEG |
| RF-08 | Timer dedicado de stream health em `StreamManager` |

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | Matriz recovery PLC | `tests/test_plc_recovery.py` |
| CA-02 | Flags reliability + template produção | `tests/test_auto_start_config.py` |
| CA-03 | Endpoint /health | `tests/test_health_endpoint.py` |
| CA-04 | Suíte verde | `pytest tests/ -q` |

## 11. Checklist

- [x] Recovery seguro (sem retomar WAITING_ACK às cegas)
- [x] Auto-start Operação via config
- [x] Power guard Linux
- [x] systemd unit + preflight
- [x] Documentação RUNBOOK_24x7_UBUNTU.md
