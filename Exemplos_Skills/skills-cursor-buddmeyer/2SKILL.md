---
name: debug-nx102
description: Diagnosticar comportamento anormal do CLP Omron NX102 e de projetos Sysmac, incluindo tarefas, eventos, memória, I/O, EtherCAT e portas EtherNet/IP. Use em falhas ligadas ao controlador, sem executar mudanças online automaticamente.
---

# Diagnóstico do Omron NX102

Investigue o controlador por camadas e use como autoridade os manuais correspondentes ao modelo, unit version, firmware e versão do Sysmac Studio informados pelo usuário.

## Antes de analisar

Identifique, sem adivinhar:

- modelo completo do NX102, unit version e firmware;
- versão do Sysmac Studio e revisão do projeto implantado;
- modo e estado atual do controlador;
- períodos/prioridades das tarefas e tempo de execução observado;
- módulos NX, dispositivos EtherCAT e conexões EtherNet/IP envolvidos;
- códigos de evento completos, severidade, timestamp e contexto.

Se os artefatos não estiverem no repositório, peça exportações, capturas ou relatórios somente leitura. Não solicite credenciais.

## Diagnóstico

1. Correlacione o primeiro evento causal; não presuma que o último alarme é a origem.
2. Verifique mudanças de modo, reinícios, watchdogs, exceções de tarefa, saturação de período e picos de execução.
3. Revise inicialização, retenção, estados após warm/cold start e sequências que podem ficar parcialmente concluídas.
4. Procure máquinas de estado sem timeout, espera infinita, pulso perdido, race entre tarefas, escrita múltipla na mesma variável e tratamento incompleto de `Done`, `Busy`, `Error` e `ErrorID`.
5. Diferencie falha de CPU, barramento NX, EtherCAT, EtherNet/IP, dispositivo e lógica da aplicação usando os eventos e estados específicos de cada camada.
6. Compare configuração offline e online apenas em modo seguro. Trate divergências como evidência, não como autorização para sincronizar.
7. Para correções, prefira mudanças pequenas, observáveis e reversíveis. Inclua teste em simulação/bancada quando aplicável.

## Cuidados com produção

- Não transfira projeto, sincronize, altere modo, reinicie, limpe erro, force variável, ajuste relógio ou mude parâmetros online sem autorização explícita.
- Não modifique funções de safety nem sugira bypass de intertravamento.
- Uma correção que oculta o alarme sem remover a causa não é aceita.
- Confirme compatibilidade de versão antes de recomendar instruções ou recursos específicos.

## Resultado

Informe evidências, hipótese causal, trecho/tarefa afetado, teste de confirmação, correção mínima, plano de rollback e critérios mensuráveis: ausência do evento, margem de tempo de tarefa, estabilidade de comunicação e ciclos/horas de observação.
