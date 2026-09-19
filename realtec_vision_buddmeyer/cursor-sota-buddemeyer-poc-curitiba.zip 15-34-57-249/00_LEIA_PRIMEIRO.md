# LEIA PRIMEIRO — pacote SOTA do Cursor para o POC Buddemeyer

Este ZIP deve ser descompactado **diretamente na raiz do repositório do POC**. Ele não possui uma pasta intermediária: a extração cria `.cursor/`, `docs/` e os arquivos de orientação no local atual.

## A pasta `.cursor` está oculta no macOS

O ponto no início do nome faz o Finder ocultá-la. Na raiz do projeto, pressione:

```text
Command + Shift + .
```

O Cursor a reconhece mesmo quando o Finder não a mostra.

## Confirmação rápida

No Terminal aberto na raiz do repositório:

```bash
find .cursor -type f | sort
find .cursor/skills -name SKILL.md | wc -l
find .cursor/rules -name '*.mdc' | wc -l
python3 --version
```

Resultados esperados:

- `13` arquivos `SKILL.md`;
- `3` rules `.mdc`;
- `1` subagente em `.cursor/agents/`;
- `2` scripts em `.cursor/hooks/` e `.cursor/hooks.json`;
- Python 3 disponível para os hooks locais.

A instalação está no local correto quando, por exemplo, este arquivo existir:

```text
<raiz-do-repositorio>/.cursor/skills/application/customize-buddemeyer-supervisory/SKILL.md
```

Se aparecer `<raiz>/cursor-sota-buddemeyer-poc-curitiba/.cursor/...`, a extração criou uma pasta intermediária e o conteúdo precisa ser movido um nível acima.

## Próximos documentos

1. Leia `TUTORIAL_INSTALACAO_E_SKILLS.md` para instalar ou atualizar com segurança.
2. Preencha `docs/project/CODEBASE_MAP.md` com os caminhos e comandos reais do POC.
3. Use os modelos de `docs/cursor-agent/PROMPTS_CURSOR_POC.md` no chat do Cursor.

As instruções do Agent não substituem intertravamentos, safety, procedimentos de máquina, validação HIL ou aprovação do responsável local.
