# Guia do Operador — Buddmeyer Vision v2.0

Tutorial de uso das abas **Operação**, **Configuração** e **Diagnósticos**.

---

## Antes de começar

1. Instale o ambiente (ver [MACOS_SETUP.md](MACOS_SETUP.md) ou [UBUNTU_SETUP.md](UBUNTU_SETUP.md)).
2. Confirme que `model_best/` está completo (`git lfs pull` se clonou do GitHub).
3. Configure o IP do CLP na aba **Configuração** e **salve** antes de operar.

---

## Aba Operação

### Iniciar o sistema

1. Escolha a **fonte de vídeo** no combo da aba Operação: **USB** ou **GenTL**.
2. Com **USB**, selecione o índice da câmera (0, 1, 2…). Com **GenTL**, configure o CTI em Configuração → Entrada / Câmera se necessário.
3. Clique **▶ Iniciar** (ou **F5**).
4. Aguarde o carregamento do modelo (barra de status). Na primeira execução pode demorar alguns segundos.
5. As detecções aparecem sobre o vídeo (máscara/contorno da embalagem).

> Fontes adicionais (`video`, `rtsp`, `gige`) existem no YAML / adapters para lab, mas **não** estão no combo da aba Operação nesta baseline.

### Parar

- **⏹ Parar** ou **F6** — para stream, inferência e handshake com CLP.

### Painel de status

Exibe em tempo real:

- Estado do ciclo / robô
- Última detecção: confiança, **X, Y, ângulo (°), área**
- Conexão CLP e latência
- FPS de captura e inferência

### Modos de ciclo

| Modo | Comportamento |
|------|---------------|
| **Manual** | Após detecção, operador autoriza envio ao CLP; após ciclo, clica **Novo Ciclo** |
| **Contínuo** | Ciclos seguem automaticamente após handshake |

### ROI (região de interesse)

- Ajuste o retângulo ROI na Operação para limitar a área de detecção.
- O centróide enviado ao CLP é **limitado ao ROI** (segurança).

### Stream para navegador (MJPEG)

1. Configuração → Saída → **Copiar URL do stream** (primeira vez; grava preferência).
2. Cole no navegador: `http://127.0.0.1:8080/stream`.
3. **Após reiniciar o app**, o stream volta sozinho se já foi activado antes (mesma URL).
4. Para vídeo ao vivo, use Operação → **▶ Iniciar**.

### Atalhos

| Atalho | Ação |
|--------|------|
| F5 | Iniciar |
| F6 | Parar |
| F11 | Fullscreen |
| Ctrl+Q | Sair |

### Câmera GenTL

Com fonte **GenTL**, use o botão de ajustes para exposição/ganho quando disponível.

---

## Aba Configuração

Sub-abas: **Entrada**, **Detecção**, **Imagem**, **CLP**, **Saída**.

### Entrada / Câmera

Parâmetros da fonte activa (USB ou GenTL): índice USB, CTI GenTL, exposição/ganho quando disponível.

### Detecção

- Modelo: padrão `model_best` (Mask2Former treinado para Embalagem). Ver [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md).
- Limiar de confiança (default shipped ≈ **0.61**): valores altos reduzem falsos positivos mas podem silenciar detecções reais — use logs `inference_diagnostic` para calibrar.

### Imagem / ROI

- ROI e calibração mm/px para exibição de coordenadas em mm.

### CLP

- IP, porta, modo simulado.
- **Salvar** após alterar IP — a conexão usa o valor do ficheiro no momento do connect.

### Saída

- **Copiar URL do stream** — um clique liga o MJPEG, grava config e copia `http://127.0.0.1:…` para colar no navegador.
- Porta e Path opcionais (default 8080 `/stream`).

**Importante:** parâmetros avançados de segmentação (`segmentation_*`, `target_classes`) estão apenas em `config/config.yaml`.

---

## Aba Diagnósticos

- **Visão geral:** contadores (detecções, ciclos, erros), saúde do sistema.
- **Métricas:** gráficos de FPS e latência.
- **Logs:** visualização de `realtec_vision.log`.
- **Sistema:** informações de hardware e versão.

---

## Fluxo típico pick-and-place

1. CLP autoriza detecção (`RobotCtrl_AuthorizeDetection`).
2. Visão detecta embalagem → envia X, Y, ângulo, área, confiança.
3. Robô confirma ACK → executa pick → place.
4. Ciclo completa → pronto para próximo (manual ou automático).

Detalhe da máquina de estados (fluxo simulado/manual): [PICK_PLACE_EXPEDICAO.md](PICK_PLACE_EXPEDICAO.md).  
Integração com CLP real: [RUNBOOK_INTEGRACAO_CLP.md](RUNBOOK_INTEGRACAO_CLP.md).

---

## Problemas comuns

| Problema | O que fazer |
|----------|-------------|
| Tela preta (USB) | Aguarde warm-up; troque índice da câmera; veja log `inference_diagnostic` |
| Nenhuma detecção | Baixe `confidence_threshold`; verifique iluminação e ROI |
| CLP desconectado | Confira IP, cabo, firewall; teste modo simulado |
| Erro ao enviar tag | Compare nomes das tags com Sysmac Studio — ver [ROTEIRO_CLIENTE.md](../ROTEIRO_CLIENTE.md) |

---

## Documentação adicional

- [OVERVIEW.md](OVERVIEW.md) — visão executiva
- [MODELO_MASK2FORMER.md](MODELO_MASK2FORMER.md) — modelo de visão
- [REFERENCE.md](REFERENCE.md) — referência técnica
- [ROTEIRO_CLIENTE.md](../ROTEIRO_CLIENTE.md) — suporte e logs (se presente no pacote)
