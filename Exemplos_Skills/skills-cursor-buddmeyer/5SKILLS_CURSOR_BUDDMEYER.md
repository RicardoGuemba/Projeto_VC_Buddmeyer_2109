# Skills do Cursor para estabilidade Buddemeyer

## Onde ficam

As skills deste repositório ficam em:

```text
.cursor/skills/
├── incident-triage-buddmeyer/SKILL.md
├── debug-nx102/SKILL.md
├── debug-cip-ethernet-ip/SKILL.md
└── harden-buddmeyer-24x7/SKILL.md
```

Esse é o escopo de projeto: os arquivos devem ser versionados no Git para que a equipe e agentes remotos que clonem o repositório recebam as mesmas instruções. O Cursor também reconhece `.agents/skills/`, mas `.cursor/skills/` deixa explícito que estes exemplos foram preparados para o Cursor.

Para uma skill pessoal, disponível em vários projetos apenas na máquina do usuário, use `~/.cursor/skills/<nome>/SKILL.md`. Não mova estas skills industriais para lá se a intenção for compartilhá-las e revisá-las junto com o código.

## Como usar

Reabra/inicie uma conversa do Agent após adicionar ou alterar as skills. O Cursor as descobre automaticamente e pode escolher uma pela descrição. Para acionamento manual, digite `/` no chat do Agent e procure o nome:

- `/incident-triage-buddmeyer`: incidente ainda sem domínio causal conhecido;
- `/debug-nx102`: evento, lógica, tarefa ou estado relacionado ao NX102;
- `/debug-cip-ethernet-ip`: perda, timeout ou inconsistência na comunicação CIP;
- `/harden-buddmeyer-24x7`: revisão preventiva e backlog de confiabilidade.

Exemplos de pedido:

```text
/incident-triage-buddmeyer Analise os logs anexos. A máquina parou às 02:14, mas a IHM continuou respondendo.

/debug-nx102 Revise este export do projeto e os eventos do Sysmac. Procure uma máquina de estados que possa ficar presa após reconexão.

/debug-cip-ethernet-ip Correlacione este PCAP, os contadores do switch e os status CIP. Não proponha mudança até separar perda de rede de atraso da aplicação.

/harden-buddmeyer-24x7 Avalie este repositório para operação contínua e gere um backlog priorizado com testes e rollback.
```

## Como adaptar ao ambiente real

As skills não contêm tags, IPs, assemblies, modelos de dispositivos, períodos de tarefa ou SLOs inventados. Quando esses dados forem conhecidos e estáveis, mantenha-os em documentação versionada do projeto e referencie-a nas skills. Dados variáveis de produção devem vir de exportações e telemetria atual, não de instruções estáticas.

Adaptações recomendadas:

1. Documentar a topologia e matriz de comunicação, incluindo produtor, consumidor, tipo de conexão, RPI, timeout e comportamento seguro.
2. Registrar modelos completos, firmware/unit version, versão do Sysmac Studio e manuais aplicáveis.
3. Definir SLOs, RTO/RPO, critérios de dado obsoleto e responsáveis por aprovação.
4. Acrescentar comandos reais de teste, lint, simulação e análise de logs quando o software entrar no repositório.
5. Criar runbooks por falha recorrente apenas depois que a causa e a recuperação forem validadas.

## Segurança e governança

Estas skills orientam diagnóstico e desenvolvimento; não substituem procedimentos de segurança funcional, LOTO, validação do fabricante ou responsabilidade do engenheiro de automação. Mudanças online, transferência para o CLP, alteração de modo, forces, reset, firmware e rede de controle exigem autorização explícita, backup, janela, rollback e validação local.

Revise as skills por pull request. Mudanças nas instruções podem alterar como o Agent investiga e propõe ações, portanto devem receber o mesmo cuidado dado ao código operacional.

## Estrutura de uma nova skill

Cada skill deve ter uma pasta cujo nome coincide com o campo `name` do `SKILL.md`:

```markdown
---
name: nome-da-skill
description: O que faz e quando deve ser usada.
---

# Objetivo

Instruções específicas, limites de segurança, entradas e saída esperada.
```

Use nomes em minúsculas com hífens. Mantenha o fluxo principal no `SKILL.md`; coloque documentação longa e específica em `references/`, scripts determinísticos em `scripts/` e modelos estáticos em `assets/` somente quando forem realmente necessários.
