---
name: incident-triage-buddmeyer
description: Triar falhas e intermitências no software industrial Buddemeyer, correlacionando aplicação, CLP, rede e equipamentos. Use quando houver parada, comportamento anormal, alarmes recorrentes ou causa ainda desconhecida.
---

# Triagem de incidentes Buddemeyer

Conduza uma investigação baseada em evidências e preserve a segurança da máquina. O objetivo é restaurar ou estabilizar o serviço com o menor risco e produzir uma hipótese causal testável.

## Limites de segurança

- Comece por inspeção somente leitura.
- Não altere lógica, estado do CLP, saídas, intertravamentos, parâmetros de safety, topologia, firmware ou configuração de rede sem autorização explícita e janela aprovada.
- Nunca force I/O nem contorne permissivos ou intertravamentos.
- Se houver risco a pessoas, produto ou equipamento, pare a investigação remota e solicite atuação do responsável de automação/segurança.
- Preserve projeto, parâmetros e logs originais. Não trate reinicialização como correção definitiva.

## Fluxo

1. Registre o início/fim do sintoma, turno, máquina, lote/receita, modo operacional, impacto e última mudança conhecida.
2. Confirme a linha do tempo e o fuso horário de aplicação, IHM, NX102, switches e servidores.
3. Colete evidências disponíveis: logs da aplicação, eventos/alarmes do Sysmac Studio, estado das tarefas do CLP, diagnóstico de portas, contadores de comunicação, métricas do host e alterações recentes no Git.
4. Separe o domínio provável: aplicação, lógica/tempo de ciclo do CLP, CIP/EtherNet/IP, EtherCAT/I/O, dispositivo de campo, infraestrutura ou operação.
5. Reproduza fora de produção quando possível. Reduza para o menor caso que mantém o sintoma.
6. Formule no máximo três hipóteses priorizadas. Para cada uma, declare evidência favorável, evidência contrária e teste discriminante de baixo risco.
7. Só proponha mudança depois de identificar mecanismo causal plausível. Inclua rollback, critério de sucesso e período de observação.
8. Após restaurar o serviço, produza ações para impedir recorrência e melhorar detecção.

## Saída obrigatória

Entregue:

- resumo do impacto e estado atual;
- linha do tempo com lacunas explicitadas;
- evidências observadas, separadas de inferências;
- hipóteses ordenadas por probabilidade e impacto;
- próximo teste seguro;
- mitigação temporária, se houver;
- correção proposta, rollback e validação;
- itens para RCA, monitoramento e acompanhamento.

Use “não verificado” para qualquer detalhe ausente. Não invente endereços CIP, tags, códigos de evento, versões, períodos de tarefa ou limites.
