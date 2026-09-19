# Avaliação dos arquivos e evolução para a estrutura SOTA

## Parecer executivo

O material original continha quatro skills úteis para triagem, NX102, CIP/EtherNet/IP e hardening 24×7. A primeira revisão removeu duplicatas/resíduos do macOS, corrigiu a organização e acrescentou visão, calibração, handshake/FSM e startup/restart, chegando a oito skills.

Essa cobertura era forte para diagnóstico, mas ainda incompleta para **customizar o aplicativo**. A versão atual acrescenta cinco competências de engenharia de mudança e quatro camadas de controle: rules especializadas, testes simulados, hooks e revisão independente somente leitura.

## Avaliação do material original

| Arquivo original | Parecer | Tratamento adotado |
|---|---|---|
| `incident-triage-buddmeyer/SKILL.md` | Bom ponto de entrada para causa desconhecida. | Mantido, corrigindo a grafia e delimitando o roteamento. |
| `debug-nx102/SKILL.md` | Sólido em eventos, tarefas e restart do controlador. | Mantido sob a categoria `plc`. |
| `debug-cip-ethernet-ip/SKILL.md` | Boa separação entre aplicação, CIP, rede e físico. | Mantido sob `network`, com escopo discriminante. |
| `harden-buddmeyer-24x7/SKILL.md` | Boa base preventiva de confiabilidade. | Mantido sob `reliability`, separado da triagem ativa. |
| `2SKILL.md`, `3SKILL.md`, `4SKILL.md` | Cópias que não eram descobertas corretamente na raiz. | Removidas do pacote instalável. |
| `5SKILLS_CURSOR_BUDDMEYER.md` e cópia em `docs/` | Duplicação de documentação. | Substituídas por tutorial e arquitetura únicos. |
| `.DS_Store` e `__MACOSX/**` | Metadados do macOS sem valor para o projeto. | Excluídos do pacote. |

## Lacunas fechadas na primeira revisão

| Domínio | Skill adicionada | Motivo |
|---|---|---|
| Ciclo ponta a ponta | `validate-pick-place-cycle` | Formalizar ACK, identidade, timeout e recuperação. |
| Visão | `validate-vision-inference` | Separar aquisição, modelo, pós-processamento e seleção. |
| Calibração | `validate-camera-robot-calibration` | Validar referencial, geometria e erro espacial. |
| Lifecycle | `debug-startup-restart` | Investigar recursos e estado residuais após Stop/Start. |

## Lacunas fechadas nesta versão SOTA

| Necessidade | Novo recurso | Resultado esperado |
|---|---|---|
| Feature/customização de ponta a ponta | `customize-buddemeyer-supervisory` | Requisitos, mapa de impacto, implementação mínima e rollback. |
| Arquitetura de UI | `develop-pyside6-supervisory-ui` + rule PySide6 | Event loop responsivo, sinais/slots, workers e cleanup testáveis. |
| Validação sem hardware | `test-buddemeyer-with-simulators` | Fakes, fault injection, replay e integração determinística. |
| Receitas/configuração | `manage-buddemeyer-recipes-config` | Schema, versão, unidades, atomicidade e migração. |
| Build/liberação | `package-release-buddemeyer` | Reprodutibilidade, manifesto, compatibilidade e rollback. |
| Fronteiras de hardware | `hardware-adapters.mdc` | Lifecycle, timeouts, freshness e proibição de bypass. |
| Ação de shell arriscada | `guard-industrial-commands.py` | Solicitação de aprovação antes de comandos suspeitos. |
| Erro sintático após edição | `validate-edited-file.py` | Feedback rápido para Python, JSON, TOML e frontmatter. |
| Viés de autoavaliação | `industrial-change-verifier` | Revisão separada e somente leitura. |

## Estrutura e instalação

Todos os componentes específicos do POC ficam dentro do repositório. Isso permite revisão por Git, comportamento consistente entre desenvolvedores e carregamento por agentes que operam sobre o projeto.

- Skills: `.cursor/skills/<categoria>/<nome>/SKILL.md`.
- Rules: `.cursor/rules/*.mdc`.
- Hooks: `.cursor/hooks.json` e `.cursor/hooks/`.
- Subagentes: `.cursor/agents/*.md`.
- Conhecimento local confirmado: `docs/project/`.
- Tutorial e prompts: `docs/cursor-agent/` e raiz.

O pacote não deve ser instalado globalmente em `~/.cursor/skills/`: essas instruções são específicas do POC, precisam acompanhar o código e não devem interferir em outros projetos.

## Roteamento

As 13 skills têm descrições específicas e não usam `disable-model-invocation: true`. Portanto, ficam disponíveis para seleção semântica automática e por `/nome-da-skill`. O Agent pode combinar skills quando um pedido atravessa mais de um domínio.

Rules de contexto/safety são permanentes; rules especializadas são selecionadas por relevância até os caminhos reais serem confirmados. `CODEBASE_MAP.md` foi incluído justamente para permitir escopo por paths/globs em uma futura revisão sem adivinhação.

## Limites do desenho

- Prompt, rule, skill, hook e subagente não são função certificada de segurança.
- O gate de shell é baseado em padrões e pode apresentar falsos positivos/negativos.
- Simulação não substitui teste HIL, comissionamento e validação operacional.
- Informação do POC marcada como `A confirmar` não deve ser promovida a fato pelo Agent.
- A qualidade final depende de critérios de aceite, testes do repositório, PR e responsáveis locais.

Para detalhes, consulte `ARQUITETURA_SOTA_CURSOR.md`, `PROMPTS_CURSOR_POC.md` e o tutorial da raiz.

## Fontes oficiais

- https://cursor.com/docs/skills
- https://cursor.com/docs/rules
- https://cursor.com/docs/hooks
- https://cursor.com/docs/subagents
- https://agentskills.io/specification

Revisão concluída em 8 de setembro de 2026.
