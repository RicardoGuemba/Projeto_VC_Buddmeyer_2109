# Arquitetura por Features — Por que cada recurso

Documento que explica as decisões arquiteturais do Realtec Vision Buddmeyer (baseline **v1607**, jul/2026).

Índice: [OVERVIEW.md](OVERVIEW.md) · Status 24×7: [AVALIACAO_24x7_PICK_PLACE.md](AVALIACAO_24x7_PICK_PLACE.md)

---

## 1. PySide6 (não Tkinter)

**Por que:** PySide6 (Qt for Python) oferece threading robusto (QThread, signals/slots), widgets industriais e suporte multiplataforma (Windows, macOS, Linux). Tkinter tem limitações em workers e atualização de UI a partir de threads. Para um sistema de visão em tempo real com stream de câmera e polling CLP, Qt é a escolha adequada.

---

## 2. Dois logs (system + process_trace)

**Por que:** Separar "por que quebrou" (infra, exceções, reconexões) de "em qual passo quebrou" (transições de estado, eventos por ciclo) reduz ruído e acelera diagnóstico. O `process_trace.log` não registra por frame, apenas eventos e transições, evitando explosão de volume. Correlação via `cycle_id`, `frame_id`, `feature`, `use_case` permite rastrear falhas entre os dois trilhos. Rotação via `logging.max_bytes` / `backup_count`.

---

## 3. UI enxuta (ISA-101 / alarm banner)

**Por que:** Em HMIs industriais, menos elementos visuais reduz carga cognitiva e destaca o anormal. Contadores (detecções, ciclos, erros) foram removidos da Operação; alarmes e estado do sistema permanecem em destaque. ROI foi movido para Operação para ajuste rápido durante a produção. Saúde do sistema (stream / inferência / CLP) aparece no painel de status.

---

## 4. Configuração sem "Tipo" e sem "Ajustes de Imagem"

**Por que:** O tipo de fonte é definido na aba Operação (combo Fonte: **USB** ou **GenTL**), onde o operador escolhe a fonte ativa. A Configuração mantém apenas os parâmetros de cada fonte. Ajustes de Imagem (brilho/contraste) foram removidos da UI; parâmetros GenICam (gain/exposição) permanecem no adapter quando necessário.

---

## 5. Ports/Adapters (GenTL, CLP)

**Por que:** Isolar integrações em adapters permite trocar implementação (ex.: outro CTI GenTL ou outro protocolo CLP) sem alterar o core. A infraestrutura não conhece Qt; a orquestração usa interfaces (ports). Adapters de vídeo/RTSP/GigE existem para lab; a HMI de Operação expõe USB + GenTL.

---

## 6. Threading (workers para stream, inferência e CLP)

**Por que:** A GUI thread do Qt não deve bloquear. Stream de câmera e inferência Mask2Former rodam em QThread; a UI é atualizada via signals/slots. Isso evita travamentos e mantém a interface responsiva.

---

## 7. Resiliência P0 (v1607)

**Por que:** Operação industrial exige recuperação e fail-closed sem caminhos paralelos de comando.

| Decisão | Motivo |
|---------|--------|
| Um único caminho FSM → CIP | Evita race com envio paralelo na UI |
| `reliability.production_mode` | Bloqueia SimulatedPLC e safety fail-open em produção |
| Stream / inference auto-restart | Câmera ou GPU hang não matam o turno |
| PickStabilizer | Pose estável antes do handshake |
| Audit SQLite | RCA entre restarts sem PostgreSQL |

Specs: [FEATURE_FSM_HANDSHAKE_HARDENING.md](FEATURE_FSM_HANDSHAKE_HARDENING.md), [FEATURE_PRODUCTION_MODE.md](FEATURE_PRODUCTION_MODE.md), [FEATURE_PICK_STABILIZER.md](FEATURE_PICK_STABILIZER.md), [FEATURE_COORDINATE_MAPPING.md](FEATURE_COORDINATE_MAPPING.md).
