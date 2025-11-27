# Face of Armok - Gerador de Retratos para Dwarf Fortress

## 📋 Descrição

Face of Armok é um mod que gera retratos fotorrealistas dos seus anões (e outras criaturas) do Dwarf Fortress usando inteligência artificial. O mod captura todas as características físicas da unidade selecionada - desde altura e cor dos olhos até equipamentos e penteados - e cria uma imagem realista.

## ⚙️ Requisitos

- *Dwarf Fortress* com suporte a DFHack
- *Python 3.x*
- *ComfyUI* rodando localmente (porta 7860)
- *Plugins DFHack necessários:*
  - json (para processar dados)
  - luasocket (para comunicação HTTP)

## 📦 Instalação

1. Coloque o script Lua na pasta de scripts do DFHack
2. Instale o servidor Python e suas dependências
3. Configure o ComfyUI com os modelos necessários:
   - Checkpoint: juggernautXL_ragnarokBy.safetensors
   - Upscaler: 4x_NMKD-Siax_200k.pth
   - Detector de faces: bbox/face_yolov8m.pt

## 🚀 Como Usar

1. *Inicie o servidor Python:*
   bash
   python servidor.py
   
   O servidor será iniciado na porta 3000.

2. *No Dwarf Fortress:*
   - Selecione uma unidade (anão, elfo, humano, etc.)
   - Execute o script Lua através do DFHack
   - O script coletará todos os dados da aparência
   - Enviará para o servidor Python
   - O ComfyUI gerará a imagem

3. *Aguarde o processamento:*
   - A imagem será gerada pelo ComfyUI
   - Você pode visualizar o progresso no ComfyUI
   - A imagem final será salva automaticamente

## 🎨 O Que o Mod Captura

- *Características Raciais:* Altura, constituição física (anões baixos e robustos, elfos altos e esbeltos, etc.)
- *Cabelo e Barba:* Comprimento, estilo (tranças, rabo de cavalo, etc.)
- *Características Físicas:* Tamanho de partes do corpo, traços faciais
- *Cores:* Olhos, cabelo, pele
- *Equipamentos:* Armaduras, roupas, capacetes (até 4 itens mais visíveis)
- *Sexo:* Masculino ou feminino

## 🔧 Configuração

### Servidor Python (porta 3000)
Edite API_URL no script Lua se necessário:
lua
local API_URL = "http://localhost:3000/api/dwarf"


### ComfyUI (porta 7860)
Verifique se o ComfyUI está rodando em:

http://127.0.0.1:7860


## 📝 Notas Técnicas

- O sistema remove automaticamente duplicatas e informações conflitantes
- Simplifica nomes de materiais para melhor geração de imagens
- Prioriza equipamentos visíveis (capacetes, armaduras do torso, pernas)
- Gera prompts otimizados para qualidade fotorrealista
- Usa upscaling 4x para melhorar detalhes

## 🐛 Resolução de Problemas

*Erro de conexão:*
- Verifique se o servidor Python está rodando
- Confirme que o ComfyUI está ativo na porta 7860

*Imagem não gerada:*
- Verifique os logs do Python no console
- Confirme que os modelos do ComfyUI estão carregados corretamente

*Características estranhas:*
- O sistema depende dos dados do Dwarf Fortress
- Algumas combinações podem gerar resultados inesperados

## 📄 Licença

Este mod é fornecido como está, para uso pessoal e educacional.

## 🙏 Créditos

- Desenvolvido para a comunidade Dwarf Fortress
- Usa ComfyUI para geração de imagens
- Baseado em modelos Stable Diffusion XL
