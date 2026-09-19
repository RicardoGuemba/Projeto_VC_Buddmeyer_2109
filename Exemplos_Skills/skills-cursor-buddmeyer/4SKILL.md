---
name: harden-buddmeyer-24x7
description: Avaliar e melhorar a confiabilidade 24x7 do software Buddemeyer e sua integração com NX102, CIP/EtherNet/IP e dispositivos de campo. Use para hardening, disponibilidade, observabilidade, recuperação e prevenção de recorrências.
---

# Hardening Buddemeyer 24x7

Transforme riscos reais em mudanças graduais e verificáveis. “24x7” significa operação contínua com falhas detectáveis, degradação segura e recuperação ensaiada; não significa prometer ausência total de falhas.

## Baseline

Antes de propor arquitetura, descubra:

- serviços/processos e dependências críticas;
- interfaces com NX102, CIP/EtherNet/IP, banco, arquivos, IHM e dispositivos;
- SLOs de disponibilidade, latência, perda aceitável de dados, RTO e RPO;
- volume nominal/pico, ciclos, turnos e janelas de manutenção;
- modos de falha históricos, MTBF/MTTR quando disponíveis e componentes sem redundância;
- estratégia atual de deploy, rollback, backup, retenção e restauração.

## Avaliação

1. Modele o fluxo ponta a ponta e identifique pontos únicos de falha.
2. Revise serviços para timeout finito, cancelamento, retry limitado com backoff e jitter, idempotência, circuit breaker e limites de fila/memória.
3. Garanta que reconexões CIP não reutilizem dados antigos como válidos. Use qualidade, timestamp, heartbeat/contador e estado explícito de comunicação.
4. Defina comportamento seguro para perda do CLP, dispositivo, rede, banco, disco, relógio e energia. Não substitua a análise de segurança funcional.
5. Separe liveness, readiness e saúde de dependências. Evite reinício automático infinito que masque defeito persistente.
6. Estruture logs com timestamp sincronizado, componente, máquina, ciclo/lote, correlação, estado anterior/novo e erro original, sem segredos.
7. Crie métricas e alertas acionáveis: disponibilidade, latência, backlog, reconexões, idade do dado, timeouts, perdas, uso de recurso e tempo de ciclo.
8. Planeje implantação canário/por máquina quando possível, rollback testado e observação suficiente para cobrir picos e trocas de turno/receita.
9. Teste recuperação em ambiente seguro: processo morto, dependência lenta/indisponível, link interrompido, dados inválidos, disco cheio e reinício ordenado.

## Priorização

Classifique cada ação por risco operacional reduzido, esforço, dependências e reversibilidade. Prefira primeiro:

- observabilidade que confirme o problema;
- eliminação de corrupção/perda silenciosa;
- limites que impeçam cascata;
- recuperação automática limitada e segura;
- remoção de ponto único de falha;
- otimizações sem evidência somente depois.

## Entregáveis

Produza uma matriz de riscos com evidência e proprietário, backlog priorizado, proposta de mudanças pequenas, plano de testes, rollback, dashboards/alertas e runbook operacional. Declare hipóteses não verificadas e não invente SLOs: proponha valores para aprovação quando não existirem.
