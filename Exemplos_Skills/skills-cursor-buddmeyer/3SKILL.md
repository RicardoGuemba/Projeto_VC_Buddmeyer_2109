---
name: debug-cip-ethernet-ip
description: Diagnosticar perdas, timeouts e dados inconsistentes em CIP sobre EtherNet/IP entre NX102 e dispositivos industriais. Use quando houver queda de conexão, tag data link instável, falha de mensagem explícita ou suspeita de rede.
---

# Diagnóstico CIP e EtherNet/IP

Analise de forma não intrusiva primeiro. Diferencie CIP (objetos, conexões e serviços), EtherNet/IP, IP/Ethernet e a lógica consumidora dos dados.

## Contexto mínimo

Registre:

- origem e destino, modelo/firmware, IP, porta física e caminho CIP;
- tipo da comunicação: I/O implícito/tag data link ou mensagem explícita;
- direção produtor/consumidor, tamanho dos dados, RPI/intervalo e timeout configurado;
- unicast ou multicast, switches, VLAN, redundância e sincronismo de relógio;
- código de status geral/estendido, contador, timestamp e frequência da falha.

Masque credenciais e dados sensíveis. Não publique dumps completos sem revisar seu conteúdo.

## Isolamento por camada

1. **Aplicação:** valide freshness, contador de sequência/heartbeat, qualidade e comportamento quando os dados ficam obsoletos.
2. **CIP:** examine estado da conexão, status geral e estendido, caminho, instância/assembly/tag, limites e reconexões.
3. **Transporte/rede:** procure perda, jitter, duplicidade de IP, flap de link, erros/descartes de porta, tempestade multicast e filas congestionadas.
4. **Carga:** correlacione falhas com RPI, quantidade de conexões/pacotes e carga do controlador/dispositivo. Compare com os limites documentados para o modelo e versão reais.
5. **Físico:** verifique cabos industriais adequados, blindagem/aterramento conforme projeto, conectores, alimentação e interferência, com equipe habilitada.

Não conclua “problema de rede” apenas porque houve timeout. Mostre qual observação separa atraso da lógica, falha do endpoint, perda de pacote ou configuração incompatível.

## Captura e testes

- Prefira espelhamento de porta/TAP e estatísticas do switch a inserir software ou equipamento no caminho de controle.
- Defina filtro, duração e horário da captura; correlacione por timestamps.
- Faça alteração de RPI, QoS, IGMP, topologia ou firmware somente após baseline e em janela aprovada.
- Não realize varredura agressiva, flood, fuzzing ou teste de carga na rede de produção.

## Saída

Apresente topologia observada, conexão afetada, linha do tempo, métricas baseline versus falha, interpretação dos status CIP, hipótese, teste discriminante, correção reversível e validação sob carga representativa.
