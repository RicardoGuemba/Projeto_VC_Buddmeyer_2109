# Runbook 24×7 — Ubuntu Box PC

Baseline **v2108**. Complementa [RUNBOOK_INTEGRACAO_CLP.md](RUNBOOK_INTEGRACAO_CLP.md) e [CLONE_BOX_PC.md](CLONE_BOX_PC.md).

## 1. Clone e instalação

```bash
git clone https://github.com/RicardoGuemba/Realtec_Vision_Buddmeyer_v2108.git
cd Realtec_Vision_Buddmeyer_v2108
git lfs install && git lfs pull
cd realtec_vision_buddmeyer
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp config/config.production.yaml.example config/config.yaml
# Editar IP CLP, câmera, GenTL CTI
python scripts/preflight_check.py
```

## 2. systemd (autostart + restart)

```bash
sudo deploy/install_systemd.sh /caminho/para/clone
sudo systemctl start realtec-vision
sudo systemctl status realtec-vision
```

Opcional: `deploy/realtec-vision.env` com overrides `BUDDMEYER__*`.

## 3. Configuração de campo

| Parâmetro | Valor recomendado |
|-----------|-------------------|
| `reliability.production_mode` | `true` |
| `reliability.auto_start_operation` | `true` |
| `reliability.plc_sync_on_startup` | `true` |
| `reliability.inhibit_power_management` | `true` |
| `cip.max_retries` | `0` (infinito) |

## 4. Recovery pós-queda de energia

1. systemd reinicia o processo
2. Operação auto-inicia (`auto_start_operation`)
3. Tags CLP são lidas; FSM entra em estado coerente (nunca retoma handshake a meio)
4. Evento registado em `logs/audit.db` (tabela `recoveries`)

Validação lab: `./scripts/validate_recovery.sh`

## 5. Health check externo

Com stream HTTP activo:

```bash
curl -s http://127.0.0.1:8080/health | jq .
```

Campos: `process`, `stream`, `cip`, `fsm_state`, `uptime_s`.

## 6. Imunidade sleep/screensaver

- Runtime: `systemd-inhibit` durante Operação (`inhibit_power_management: true`)
- SO: desactivar suspensão automática em Definições → Energia
- Opcional `/etc/systemd/logind.conf`: `IdleAction=ignore`

## 7. Soak test 72 h (aceitação)

| Critério | Pass |
|----------|------|
| Zero crash não recuperado | systemd `Restart=always` + logs |
| Stream auto-restart após UNHEALTHY | Diagnósticos / `/health` |
| CLP reconnect infinito | `max_retries: 0` |
| Recovery após reboot simulado | FSM coerente com tags CLP |
| Audit trail | `logs/audit.db` |

## 8. Troubleshooting

| Sintoma | Acção |
|---------|--------|
| Serviço não sobe | `journalctl -u realtec-vision -n 50`; correr `preflight_check.py` |
| FSM em ERROR após reboot | Verificar tags CLP (busy/ack); reset CLP se handshake a meio |
| Screensaver activo | Confirmar `inhibit_power_management`; xset/logind |
| Modelo ~130 bytes | `git lfs pull` |
