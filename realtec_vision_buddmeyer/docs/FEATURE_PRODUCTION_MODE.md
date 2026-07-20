# FEATURE: Modo produção fail-closed

| Campo | Valor |
|--------|--------|
| **Estado** | implementado |
| **Etapa plano** | 2 |

## 1. Contexto

Em campo, fallback silencioso para SimulatedPLC ou safety ignorada mascarava falhas de integração CLP.

## 2. Objetivo

`reliability.production_mode: true` bloqueia arranque sem CLP real, exige safety completa e timeouts rigorosos.

## 3. Requisitos (P0)

| ID | Descrição |
|----|-----------|
| RF-01 | `ReliabilitySettings.production_mode` (default `false`) |
| RF-02 | Safety: gate, área, cortina — leitura falha → unsafe em production |
| RF-03 | `CIPClient.connect` não faz fallback simulado se production + CLP real falhou |
| RF-04 | `authorization_timeout` em production → `TIMEOUT` (não bypass implícito) |
| RF-05 | `cip.max_retries: 0` = reconnect infinito com backoff cap |

## 5. Configuração

```yaml
reliability:
  production_mode: false
cip:
  max_retries: 0
  reconnect_backoff_cap_s: 60.0
```

## 8. Critérios de aceitação

| ID | Critério | Verificação |
|----|----------|-------------|
| CA-01 | Production bloqueia simulado | `test_production_mode.py` |
| CA-02 | Safety simulada bloqueia FSM | `test_safety_gate.py` |
| CA-03 | Suíte completa verde | `pytest tests/ -q` |
