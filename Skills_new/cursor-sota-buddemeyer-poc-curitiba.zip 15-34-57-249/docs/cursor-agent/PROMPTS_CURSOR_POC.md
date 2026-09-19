# Prompts estruturados para o chat do Cursor — POC Buddemeyer

## Como usar

Substitua tudo que estiver entre colchetes. Anexe logs, arquivos ou imagens somente quando forem necessários e estiverem sanitizados. Para testar o roteamento automático, não cite a skill. Para exigir uma skill, comece com `/nome-da-skill`.

Um bom pedido contém: resultado desejado, contexto confirmado, critérios mensuráveis, restrições, evidências disponíveis e formato da entrega. Diga ao Agent para começar em **Plan** quando a mudança ultrapassar uma edição trivial.

## Bloco comum recomendado

Copie este bloco para mudanças relevantes:

```text
MODO DE TRABALHO
- Comece em Plan. Antes de editar, inspecione o repositório e cite os arquivos, classes, chamadores, contratos e testes realmente encontrados.
- Consulte docs/project/POC_CURITIBA_CONTEXT.md, CODEBASE_MAP.md e INTERFACES_AND_STATE_MACHINE.md quando forem relevantes.
- Separe fatos confirmados, inferências e itens não verificados. Não invente paths, tags, IPs, versões, estados ou comandos.
- Preserve mudanças locais e não refatore itens fora do escopo.
- Não acesse hardware real, não force I/O e não altere CLP, robô, safety, firmware ou rede sem autorização explícita.
- Valide primeiro com testes unitários e simuladores. Marque claramente tudo o que ainda exige HIL ou validação local.
- Após implementar, peça revisão ao subagente industrial-change-verifier.

ENTREGA
- Resumo do comportamento antes/depois.
- Arquivos alterados e motivo.
- Testes executados com resultado literal.
- Riscos residuais e itens não verificados.
- Procedimento de rollback.
```

---

## 1. Prompt para adicionar uma nova feature

### Modelo completo

```text
OBJETIVO
Adicione a feature [NOME DA FEATURE] ao supervisório Buddemeyer para que [USUÁRIO/PROCESSO] consiga [RESULTADO OPERACIONAL].

CONTEXTO CONFIRMADO
- Fluxo atual: [COMO FUNCIONA HOJE].
- Ponto de entrada conhecido, se houver: [ARQUIVO/CLASSE ou NÃO VERIFICADO].
- Modos/estados envolvidos: [ESTADOS DA FSM].
- Dependências envolvidas: [UI / VISÃO / CALIBRAÇÃO / NX102-CIP / ROBÔ / RECEITA / OUTRA].
- Evidências ou referências: [ISSUE, LOG, IMAGEM, DOCUMENTO, COMMIT].

COMPORTAMENTO DESEJADO
1. [AÇÃO OU EVENTO].
2. [RESPOSTA ESPERADA].
3. [TRATAMENTO DE ERRO/INDISPONIBILIDADE].

CRITÉRIOS DE ACEITE
- Dado [CONDIÇÃO], quando [AÇÃO], então [RESULTADO MENSURÁVEL].
- Dado [ERRO/EDGE CASE], quando [AÇÃO], então [FALHA SEGURA/MENSAGEM].
- A UI permanece responsiva durante [OPERAÇÃO].
- Stop/Start repetido não duplica callbacks, threads, comandos nem dados antigos.
- Compatibilidade preservada com [CONTRATO/FORMATO/VERSÃO].

NÃO OBJETIVOS
- Não alterar [COMPONENTES FORA DO ESCOPO].
- Não mudar [CONTRATO/SAFETY/HARDWARE].

RESTRIÇÕES
- [VERSÕES, BIBLIOTECAS OU PADRÕES JÁ ADOTADOS].
- [LIMITE DE LATÊNCIA, UNIDADE, TELA ALVO].
- Hardware real indisponível; use fakes/simuladores.

EXECUÇÃO SOLICITADA
1. Comece em Plan e produza um mapa de impacto.
2. Proponha a menor solução reversível e espere minha confirmação se houver decisão arquitetural material ou dado bloqueante.
3. Implemente mantendo apresentação, aplicação, domínio/FSM e adaptadores separados.
4. Crie testes que demonstrem cada critério de aceite.
5. Execute os checks do repositório e a integração simulada relevante.
6. Acione o industrial-change-verifier e corrija achados bloqueadores/altos dentro do escopo.

[COLE AQUI O BLOCO COMUM RECOMENDADO]
```

### Exemplo preenchido

```text
Adicione uma tela de seleção de receita ao supervisório. A troca só pode ser solicitada em Idle, deve mostrar identificador e revisão, validar o arquivo antes da ativação e manter a receita anterior quando houver erro. A revisão usada deve ser registrada junto ao cycle_id.

Critérios: receita inválida nunca chega ao domínio; troca durante Pick ou Place é recusada com mensagem; escrita interrompida preserva a última versão válida; abrir/fechar a tela cinco vezes não duplica sinais; os testes usam repositório de receitas fake e FSM simulada.

Comece em Plan, descubra a arquitetura real e não suponha nomes de classes. Implemente a menor mudança, execute testes unitários/Qt/simulados, use o industrial-change-verifier e entregue riscos e rollback. Não conecte ao NX102 ou robô.
```

### Versão curta

```text
Adicione [FEATURE] para [RESULTADO]. Comece em Plan, descubra o fluxo e os contratos reais, apresente o mapa de impacto e implemente a menor mudança reversível. Aceite quando: [CRITÉRIOS]. Não altere [NÃO OBJETIVOS] nem acesse hardware. Teste unidade + Qt + integração simulada, peça revisão ao industrial-change-verifier e entregue diff, resultados, riscos e rollback.
```

Skill provável: `customize-buddemeyer-supervisory`; o Cursor pode combinar UI, configuração, integração ou testes conforme o escopo.

---

## 2. Prompt para customizar uma função existente

### Modelo completo

```text
OBJETIVO
Customize a função/método [NOME OU COMPORTAMENTO] para [NOVO RESULTADO], preservando [CONTRATOS QUE NÃO PODEM MUDAR].

LOCALIZAÇÃO
- Referência inicial: [ARQUIVO/LINHA/CLASSE ou DESCONHECIDA].
- Chamador observado: [CHAMADOR ou DESCONHECIDO].
- Sintoma/limitação atual: [DESCRIÇÃO E EVIDÊNCIA].

CONTRATO ATUAL A PRESERVAR
- Entradas e unidades: [TIPOS/UNIDADES].
- Saídas, exceções e efeitos: [CONTRATO].
- Concorrência/thread: [UI/WORKER/ASYNC/DESCONHECIDO].
- Compatibilidade de dados/API: [VERSÕES/CONSUMIDORES].

NOVA REGRA
- [REGRA 1 EM FORMA DETERMINÍSTICA].
- [REGRA 2].
- Em caso de [ERRO], deve [COMPORTAMENTO SEGURO].

CASOS DE TESTE
| Caso | Entrada/estado | Resultado esperado |
|---|---|---|
| Nominal | [VALOR] | [RESULTADO] |
| Limite inferior/superior | [VALOR] | [RESULTADO] |
| Inválido | [VALOR] | [ERRO/REJEIÇÃO] |
| Timeout/restart | [CENÁRIO] | [RESULTADO] |

EXECUÇÃO SOLICITADA
1. Localize todas as definições, chamadas, overrides, sinais/slots e testes da função.
2. Explique o comportamento atual com evidência de código.
3. Mostre a proposta de assinatura/algoritmo e impacto de compatibilidade antes de editar.
4. Faça mudança mínima; evite renomear ou mover APIs sem necessidade.
5. Adicione teste de regressão e casos de borda.
6. Execute o conjunto afetado e o industrial-change-verifier.

[COLE AQUI O BLOCO COMUM RECOMENDADO]
```

### Exemplo preenchido

```text
Customize a função que seleciona o alvo final da visão. Primeiro localize a implementação real e todos os consumidores; não suponha que ela se chama selecionar_alvo.

Nova regra: rejeitar detecções cuja idade exceda o limite configurado; dentre as válidas, preservar a política atual e usar um critério de desempate determinístico. A saída deve manter o tipo e o referencial atuais. Ausência de alvo válido deve produzir o erro de domínio já adotado, nunca coordenada default.

Crie testes para frame atual, frame obsoleto, empate, nenhuma detecção e restart com fila antiga. Não altere modelo/checkpoint, calibração ou tags. Execute testes offline, peça revisão independente e entregue compatibilidade e rollback.
```

### Versão curta

```text
Customize [FUNÇÃO/COMPORTAMENTO] para [RESULTADO]. Antes de editar, localize definição, chamadores, contrato e testes. Preserve [ASSINATURA/UNIDADES/EFEITOS]. Cubra [CASOS]. Faça o menor diff, rode regressão e simuladores, use industrial-change-verifier e informe riscos/rollback. Sem hardware real.
```

Skill provável: `customize-buddemeyer-supervisory`; para código Qt, `develop-pyside6-supervisory-ui`; para visão, `validate-vision-inference`.

---

## 3. Prompt para resolver um problema

### Modelo completo

```text
INCIDENTE/PROBLEMA
- Sintoma observável: [O QUE ACONTECEU, SEM INTERPRETAÇÃO].
- Início/frequência: [TIMESTAMP/FREQUÊNCIA].
- Último ciclo bom: [IDENTIFICADOR/HORA].
- Impacto: [PARADA, QUALIDADE, LATÊNCIA, OUTRO].
- Ambiente/versão/commit: [DADOS CONFIRMADOS].
- Última mudança conhecida: [COMMIT/CONFIGURAÇÃO/MANUTENÇÃO ou NENHUMA CONHECIDA].

REPRODUÇÃO
1. [ESTADO INICIAL].
2. [AÇÃO].
3. [RESULTADO ATUAL].
4. Resultado esperado: [RESULTADO].

EVIDÊNCIAS DISPONÍVEIS
- Logs: [CAMINHO/ANEXO E INTERVALO].
- Eventos NX102/rede/robô: [FONTE ou NÃO DISPONÍVEL].
- Teste já tentado: [AÇÃO E RESULTADO].
- Trecho suspeito, sem afirmar causa: [ARQUIVO].

LIMITES
- Inicie somente leitura.
- Não reinicie, não limpe erro, não force I/O e não altere configuração para “testar”.
- No máximo três hipóteses simultâneas; para cada uma, mostre evidência favorável, contrária e teste discriminante de baixo risco.

EXECUÇÃO SOLICITADA
1. Construa uma linha do tempo com relógios/fusos explícitos.
2. Identifique a primeira falha causal, não apenas o último alarme.
3. Reproduza com teste automatizado ou simulador quando possível.
4. Só depois da causa plausível, proponha e implemente a menor correção.
5. Adicione um teste que falhava antes e passa depois.
6. Execute regressões, teste Stop/Start quando relevante e peça revisão ao industrial-change-verifier.

CRITÉRIO DE RESOLUÇÃO
- [MÉTRICA/QUANTIDADE DE CICLOS/PERÍODO SEM FALHA].
- [SEM REGRESSÃO EM X].

[COLE AQUI O BLOCO COMUM RECOMENDADO]
```

### Exemplo preenchido

```text
O supervisório abre e a câmera funciona no primeiro Start. Depois de Stop e novo Start, a UI permanece aberta, mas não chegam frames. Ocorre sempre no ambiente de desenvolvimento desde o commit [HASH]. O log entre [HORÁRIOS] está anexado; não há evidência de falha física.

Comece somente leitura. Compare primeira inicialização, parada e segunda inicialização. Liste câmera, threads, timers, callbacks, filas e conexões adquiridos/liberados. Formule até três hipóteses e crie o menor teste de restart sem hardware. Só implemente após demonstrar o recurso/estado residual. O aceite exige 20 ciclos Start/Stop simulados, sem aumento de threads/callbacks e com novo frame/cycle_id em cada início. Use industrial-change-verifier; não reinicie equipamento real.
```

### Versão curta

```text
Resolva: [SINTOMA]. Comece por triagem somente leitura, reconstrua a linha do tempo e separe evidência de hipótese. Reproduza com simulador; mantenha no máximo três hipóteses e use teste discriminante. Depois da causa, faça correção mínima + teste de regressão, execute checks e industrial-change-verifier. Aceite: [CRITÉRIO]. Não altere hardware/safety.
```

Skill provável quando a causa é desconhecida: `incident-triage-buddemeyer`. O diagnóstico pode migrar para a skill de NX102, rede, visão, calibração, integração ou restart conforme as evidências.

---

## Prompt de revisão final antes do PR

```text
Revise esta mudança antes do PR usando o subagente industrial-change-verifier em modo somente leitura. Compare pedido, critérios de aceite e diff; verifique arquitetura, event loop/threads, lifecycle, FSM, freshness, idempotência, configuração, testes, segredos e rollback conforme aplicável. Não edite. Classifique achados por severidade, cite evidências e finalize com APROVADO, APROVADO COM RESSALVAS ou NÃO APROVADO. Liste testes observados e tudo que ainda exige HIL/validação local.
```

## Prompt para testar roteamento automático

Abra uma conversa nova e envie apenas um destes exemplos, sem `/skill`:

| Prompt curto | Skill esperada |
|---|---|
| “Adicione uma tela de gestão de receitas com validação e rollback.” | `customize-buddemeyer-supervisory` + `manage-buddemeyer-recipes-config` |
| “Esta tela congela durante a inferência e deixa threads depois de fechar.” | `develop-pyside6-supervisory-ui` |
| “Crie fakes de câmera, NX102 e robô para testar a FSM sem hardware.” | `test-buddemeyer-with-simulators` |
| “Gere um build reproduzível com manifesto e plano de rollback.” | `package-release-buddemeyer` |
| “A célula parou e não sabemos se foi visão, CLP ou rede.” | `incident-triage-buddemeyer` |

O roteamento é contextual e pode combinar skills. Se precisar de seleção determinística, use `/nome-da-skill` no início do prompt.
