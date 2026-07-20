# FEATURE: Pick stabilizer e observabilidade

| Campo | Valor |
|--------|--------|
| **Estado** | implementado |
| **Etapa plano** | 3 |

## 1. Contexto

Flicker de detecção (1 frame isolado) podia iniciar ciclo FSM; logs cresciam sem rotação; operador não via saúde agregada.

## 2. Objetivo

Confirmar pick após N frames estáveis; rotação de logs; banner de saúde; `trace_event` nas transições FSM.

## 3. Requisitos (P0)

| ID | Descrição |
|----|-----------|
| RF-01 | `PickStabilizer` — `stable_frames`, `centroid_epsilon_px` |
| RF-02 | `detection_event` só após estabilização; overlay via `detection_result` |
| RF-03 | Log rotation (`logging.max_bytes`, `backup_count`) |
| RF-04 | `StatusPanel.update_system_health()` — CLP, FSM, stream, simulated |
| RF-05 | `trace_event` em transições FSM críticas |

## 5. Configuração

```yaml
detection:
  stable_frames: 3
  centroid_epsilon_px: 15.0
logging:
  max_bytes: 50000000
  backup_count: 10
```

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | 1 frame isolado não emite evento FSM | `test_pick_stabilizer.py` |
| CA-02 | Smoke vídeo exit 0 | `scripts.smoke_test_segmentation` |
| CA-03 | Banner reflecte estados | inspeção UI / testes widget |
