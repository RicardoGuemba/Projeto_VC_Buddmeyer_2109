# Runbook — Integração CLP Omron NX102

Checklist pré-deploy e validação no box PC antes de `production_mode: true`.

Índice: [OVERVIEW.md](OVERVIEW.md) · Contrato: [TAG_CONTRACT.md](TAG_CONTRACT.md) · Modelo: [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md)

## 1. Pré-requisitos

- Rede EtherNet/IP: PC e CLP na mesma sub-rede; IP em `config/config.yaml` → `cip.ip`
- Tags físicas alinhadas a `docs/TAG_CONTRACT.md` v1.1
- `preprocess.roi_calibration_mm_per_px` calibrado em campo
- Modelo carregável (`model_best/` completo via Git LFS)

## 2. Dev / piloto (simulado)

```yaml
cip:
  simulated: true
reliability:
  production_mode: false
```

1. Arrancar app: `python main.py`
2. Iniciar sistema → confirmar banner **CLP simulado**
3. Modo contínuo → 1 ciclo completo; logs `state_transition` sem writes paralelos
4. Validar automático:

```bash
cd realtec_vision_buddmeyer
python -m scripts.validate_handshake
python -m pytest tests/ -q
```

## 3. Produção (CLP real)

```yaml
cip:
  simulated: false
reliability:
  production_mode: true
```

1. **Não** arrancar se IP inválido — UI deve bloquear FSM
2. Verificar safety tags: gate, área, cortina
3. 1 ciclo supervisionado: detecção → ACK → pick → place → `ReadyForNext`
4. Confirmar `CENTROID_X/Y` em mm no monitor CLP
5. Verificar `logs/audit.db` — registo de ciclo e falhas

## 4. Recovery runtime

| Sintoma | Acção automática | Log |
|---------|------------------|-----|
| Stream UNHEALTHY | restart após `streaming.unhealthy_restart_after_s` | `stream_recovery_attempted` |
| Inferência N erros | restart worker | `inference_worker_restart` |
| CLP desconectado | reconnect infinito (`max_retries: 0`) | `cip_reconnect` |

## 5. Falhas comuns

| Sintoma | Causa provável | Acção |
|---------|----------------|-------|
| FSM preso em WAITING_AUTHORIZATION | `PlcAuthorizeDetection` false | CLP em auto + autorização |
| TIMEOUT em production | ACK/pick lento | Ajustar timeouts ou timing CLP |
| Coordenadas erradas | mm/px não calibrado | Recalibrar ROI |
| VisionBusy sempre true | FSM em estado activo ou erro | Reset FSM; verificar `ROBOT_ERROR` |

## 6. Soak test (pós-integração)

- 4 h supervisionado → 24 h com operador → 72 h desacompanhado
- Monitorizar `logs/audit.db`, rotação de ficheiros, CPU/GPU
