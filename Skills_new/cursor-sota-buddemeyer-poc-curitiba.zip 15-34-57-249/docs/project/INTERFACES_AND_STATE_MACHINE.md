# Contrato de interfaces e máquina de estados

Preencha este documento com o Guilherme e o responsável por CLP/robô. O Cursor deve tratá-lo como contrato somente depois da validação humana.

## Matriz de sinais

| Sinal/tag | Produtor | Consumidor | Tipo | Unidade | Validade/timeout | Estado seguro | Evidência/fonte |
|---|---|---|---|---|---|---|---|
| A confirmar | A confirmar | A confirmar | nível/pulso/dado | A confirmar | A confirmar | A confirmar | A confirmar |

## Estados e transições

| Estado | Condição de entrada | Ação | ACK esperado | Timeout | Próximo estado | Falha/recuperação |
|---|---|---|---|---|---|---|
| Idle | A confirmar | A confirmar | A confirmar | A confirmar | A confirmar | A confirmar |
| ACK | A confirmar | A confirmar | A confirmar | A confirmar | Pick | A confirmar |
| Pick | A confirmar | A confirmar | A confirmar | A confirmar | Place | A confirmar |
| Place | A confirmar | A confirmar | A confirmar | A confirmar | Complete | A confirmar |
| Complete | A confirmar | A confirmar | A confirmar | A confirmar | Idle | A confirmar |
| Error/Abort | A confirmar | Estado seguro | A confirmar | A confirmar | A confirmar | A confirmar |

## Invariantes a aprovar

- Um comando físico é associado a um único `cycle_id`.
- Repetir mensagem/ACK não pode duplicar movimento.
- Coordenada só é aceita se estado, identidade, qualidade e idade forem válidos.
- Todo estado de espera possui timeout e transição de erro definida.
- Restart ou reconexão nunca presume que um ciclo parcialmente concluído pode continuar sem reconciliação.
- Retorno a `Idle` não contorna permissivos/intertravamentos.

## Evidências por ciclo

Registrar, quando tecnicamente disponível: `cycle_id`, timestamps, imagem/frame, predição, coordenada câmera/mundo/robô, estados, comandos, ACKs, alarmes, versão do modelo, versão do software e revisão do projeto do CLP.

