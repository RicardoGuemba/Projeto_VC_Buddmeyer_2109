# Contexto técnico do POC Buddemeyer — Curitiba

Este arquivo contém o contexto estável conhecido que pode orientar o Cursor sem transformar hipóteses em fatos. Atualize-o por pull request sempre que a arquitetura real mudar.

## Objetivo

Integrar visão computacional, conversão de coordenadas e automação para executar pick-and-place de embalagens com operação segura, rastreável e progressivamente robusta para 24×7.

## Componentes conhecidos

- câmera e iluminação dedicada na região de manipulação;
- preditor de visão para localizar/selecionar embalagem;
- transformação de coordenadas de imagem para o referencial operacional;
- supervisório/aplicação de integração;
- CLP Omron NX102 e projeto Sysmac;
- comunicação industrial CIP sobre EtherNet/IP;
- robô e plataforma com oito ventosas;
- máquina de estados com conceitos ACK, Pick, Place e Complete.

## Premissas que exigem confirmação no repositório/célula

- modelos, firmwares e versões exatas;
- biblioteca Python usada na comunicação com o NX102;
- topologia, IPs, tags, assemblies, RPI e timeouts;
- contratos de sinais e proprietário de cada transição;
- modelo matemático da transformação câmera–robô;
- tolerância espacial, tempo de ciclo e critérios de aceite;
- comportamento seguro em cada perda de dependência;
- caminhos reais do código, comandos de teste e processo de deploy.
- framework e versão reais da interface (confirmar PySide6/Qt antes de aplicar regras específicas de UI).

## Convenções de engenharia

- Correlação: cada tentativa de ciclo deve ter identificador e timestamps comparáveis entre componentes.
- Freshness: imagem, detecção, coordenada e dados do CLP precisam declarar validade; dado antigo não pode parecer novo.
- Observabilidade: logs devem registrar componente, versão, ciclo, estado anterior/novo e erro original.
- Mudança: toda alteração operacional deve ter evidência, teste, critério de sucesso e rollback.
- Segurança: software de IA e estas instruções não substituem análise de safety, intertravamentos, LOTO ou validação do responsável local.

## Como manter este documento

Substitua itens “a confirmar” por fatos somente com fonte verificável: código versionado, export Sysmac, manual aplicável, desenho elétrico/mecânico, teste aprovado ou registro operacional. Inclua data e revisão da fonte.
