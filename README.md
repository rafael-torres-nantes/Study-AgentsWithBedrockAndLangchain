Collecting workspace information# Assistente Virtual Inteligente - LangChain + AWS Bedrock + MCP

## 👨‍💻 Projeto desenvolvido por: 
[Rafael Torres Nantes](https://github.com/rafael-torres-nantes)

## Índice

* 📚 Contextualização do projeto
* 🛠️ Tecnologias/Ferramentas utilizadas
* 🖥️ Funcionamento do sistema
   * 🧩 Arquitetura Tradicional
   * 🔄 Arquitetura MCP (Model Context Protocol)
   * 🎯 Comparação entre Arquiteturas
   * 🚀 Por que usar MCP para Escalabilidade?
* 🔀 Arquitetura da aplicação
* 📁 Estrutura do projeto
* 📌 Como executar o projeto
* � Formato JSON para Requests
* �🕵️ Dificuldades Encontradas

## 📚 Contextualização do projeto

O projeto consiste em um **assistente virtual inteligente** que utiliza **AWS Bedrock** com modelos de IA generativa (Amazon Nova Pro) integrado ao framework **LangChain** para criar agentes conversacionais com capacidade de usar ferramentas especializadas. O sistema oferece duas arquiteturas distintas: uma tradicional e outra baseada em **MCP (Model Context Protocol)** para demonstrar diferentes abordagens de implementação de agentes IA.

O assistente é capaz de:
- **Análise de texto** (contagem de caracteres, palavras, conversões)
- **Cálculos matemáticos** básicos e avançados
- **Análise de sentimento** e extração de informações
- **Conversação natural** com preservação de contexto
- **Síntese de voz** usando Amazon Polly
- **Gerenciamento de ferramentas** automático via MCP

## 🛠️ Tecnologias/Ferramentas utilizadas

[<img src="https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white">](https://www.python.org/)
[<img src="https://img.shields.io/badge/AWS-Bedrock-FF9900?logo=amazonaws&logoColor=white">](https://aws.amazon.com/bedrock/)
[<img src="https://img.shields.io/badge/LangChain-005C84?logo=python&logoColor=white">](https://langchain.com/)
[<img src="https://img.shields.io/badge/Amazon-Nova_Pro-FF9900?logo=amazonaws&logoColor=white">](https://aws.amazon.com/bedrock/)
[<img src="https://img.shields.io/badge/Amazon-Polly-FF9900?logo=amazonaws&logoColor=white">](https://aws.amazon.com/polly/)
[<img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white">](https://fastapi.tiangolo.com/)
[<img src="https://img.shields.io/badge/MCP-Model_Context_Protocol-4A90E2?logo=python&logoColor=white">](https://modelcontextprotocol.io/)
[<img src="https://img.shields.io/badge/Boto3-0073BB?logo=amazonaws&logoColor=white">](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)
[<img src="https://img.shields.io/badge/Visual_Studio_Code-007ACC?logo=visual-studio-code&logoColor=white">](https://code.visualstudio.com/)
[<img src="https://img.shields.io/badge/GitHub-181717?logo=github&logoColor=white">](https://github.com/)

## 🖥️ Funcionamento do sistema

### 🧩 Arquitetura Tradicional

A arquitetura tradicional utiliza `LangChainWorkflow` (controller) + `LangChainCore` (services):

* **Controller**: `LangChainWorkflow` gerencia agentes, tools e workflows multi-step
* **Core Services**: `LangChainCore` fornece funcionalidades básicas de inferência e conversação
* **Tools**: `text_analysis_tool.py` contém ferramentas tradicionais de análise
* **Workflow**: Criação manual de agentes com ferramentas específicas

**Exemplo de uso**:
```python
# Inicialização tradicional
bedrock_service = LangChainWorkflow()
available_tools = get_all_tools()
tools_added = bedrock_service.add_tools(available_tools)
bedrock_service.create_agent_template(prompt_template)
```

### 🔄 Arquitetura MCP (Model Context Protocol)

A arquitetura MCP utiliza `MCPLangChainWorkflow` (controller) + `MCPLangChainCore` (services):

* **MCP Controller**: `MCPLangChainWorkflow` com auto-descoberta de ferramentas MCP
* **MCP Core**: `MCPLangChainCore` otimizado para integração MCP
* **MCP Tools Server**: `mcp_tools_server.py` servidor dedicado de ferramentas
* **Auto-discovery**: Carregamento automático de ferramentas via protocolo MCP

**Exemplo de uso**:
```python
# Inicialização MCP (mais simples)
bedrock_mcp_service = MCPLangChainWorkflow(auto_load_mcp=True)
# MCP tools carregadas automaticamente
bedrock_mcp_service.create_agent_template(prompt_template)
```

### 🎯 Comparação entre Arquiteturas

| Aspecto | Tradicional | MCP |
|---------|-------------|-----|
| **Descoberta de Tools** | Manual | Automática |
| **Gerenciamento** | `LangChainWorkflow` | `MCPLangChainWorkflow` |
| **Core Services** | `LangChainCore` | `MCPLangChainCore` |
| **Escalabilidade** | Limitada | Alta |
| **Complexidade** | Maior | Menor |
| **Handler** | lambda_function.py | lambda_function_mcp.py |

### 🚀 Por que usar MCP para Escalabilidade?

O **Model Context Protocol (MCP)** oferece vantagens significativas em termos de escalabilidade e manutenibilidade:

#### 📈 Vantagens de Escalabilidade:

1. **Auto-descoberta Dinâmica**: 
   - **Tradicional**: Cada nova ferramenta precisa ser manualmente registrada no código
   - **MCP**: Ferramentas são descobertas automaticamente via protocolo padronizado
   
2. **Desacoplamento de Componentes**:
   - Ferramentas podem ser desenvolvidas, testadas e deployed independentemente
   - Servidores MCP podem rodar em processos/containers separados
   - Facilita arquiteturas de microserviços

3. **Gestão de Recursos**:
   - Ferramentas MCP podem ser distribuídas em múltiplos servidores
   - Load balancing automático entre servidores MCP
   - Isolamento de falhas por ferramenta

#### 🔧 Implicações Técnicas:

**Para Desenvolvedores:**
```python
# Tradicional: Registro manual
tools = [
    TextAnalysisTool(),
    CalculatorTool(),
    WeatherTool()  # Precisa modificar código principal
]

# MCP: Auto-descoberta
mcp_client = MCPClient()
tools = mcp_client.discover_tools()  # Carrega dinamicamente
```

**Para DevOps:**
- **Deployment Independente**: Cada MCP server pode ter seu próprio ciclo de deploy
- **Versionamento Granular**: Versões de ferramentas independentes do core
- **Monitoramento Isolado**: Métricas separadas por servidor MCP

**Para Arquitetura:**
```
Traditional:                    MCP:
┌─────────────┐                ┌─────────────┐
│   Lambda    │                │   Lambda    │
│ ┌─────────┐ │                │ ┌─────────┐ │
│ │  Core   │ │                │ │  Core   │ │
│ │ +Tools  │ │                │ │ +MCP    │ │
│ │ (Tight) │ │                │ │Client   │ │
│ └─────────┘ │                │ └─────────┘ │
└─────────────┘                └─────┬───────┘
                                     │
                                ┌────▼────┐
                                │   MCP   │
                                │ Tools   │
                                │Servers  │
                                └─────────┘
```

#### ⚠️ Considerações e Trade-offs:

**Benefícios:**
- ✅ **Escalabilidade horizontal** de ferramentas
- ✅ **Manutenção simplificada** com componentes isolados
- ✅ **Flexibilidade de deployment** independente
- ✅ **Standardização** via protocolo MCP
- ✅ **Tolerância a falhas** por isolamento

**Desafios:**
- ⚠️ **Latência adicional** de comunicação entre processos
- ⚠️ **Complexidade de infraestrutura** inicial
- ⚠️ **Debugging distribuído** mais complexo
- ⚠️ **Overhead de protocolo** MCP

#### 📊 Casos de Uso Recomendados:

**Use MCP quando:**
- Sistema com **+10 ferramentas** diferentes
- Equipes **múltiplas** desenvolvendo ferramentas
- Necessidade de **atualizações frequentes** de tools
- Arquitetura de **microserviços** existente
- Requisitos de **alta disponibilidade**

**Use Tradicional quando:**
- Sistema **simples** com poucas tools (<5)
- **Equipe única** mantendo tudo
- **Baixa latência** é crítica
- **Simplicidade** é prioridade

## 🔀 Arquitetura da aplicação

O sistema utiliza uma arquitetura baseada em **agentes inteligentes** com duas implementações distintas:

```
┌─────────────────┐    ┌──────────────────┐
│   User Query    │    │   User Query     │
└─────────┬───────┘    └─────────┬────────┘
          │                      │
     ┌────▼────┐              ┌──▼──┐
     │ Lambda  │              │ MCP │
     │Function │              │Lambda│
     └────┬────┘              └──┬──┘
          │                      │
   ┌──────▼──────┐        ┌──────▼──────┐
   │LangChain    │        │MCPLangChain │
   │Workflow     │        │Workflow     │
   └──────┬──────┘        └──────┬──────┘
          │                      │
   ┌──────▼──────┐        ┌──────▼──────┐
   │LangChain    │        │MCPLangChain │
   │Core         │        │Core         │
   └──────┬──────┘        └──────┬──────┘
          │                      │
   ┌──────▼──────┐        ┌──────▼──────┐
   │AWS Bedrock  │        │AWS Bedrock  │
   │Nova Pro     │        │Nova Pro     │
   └─────────────┘        └─────────────┘
```

### Componentes Principais:

1. **AWS Lambda Functions**: lambda_function.py e lambda_function_mcp.py
2. **Controllers**: `LangChainWorkflow` e `MCPLangChainWorkflow`
3. **Core Services**: `LangChainCore` e `MCPLangChainCore`
4. **Tools**: `text_analysis_tool.py` e `mcp_tools_server.py`
5. **TTS Service**: `polly_services.py`
6. **Response Processing**: `response_processor.py`

## 📁 Estrutura do projeto

```
LangChain-Bedrock/
├── 📄 lambda_function.py              # Handler tradicional
├── 📄 lambda_function_mcp.py          # Handler MCP
├── 📄 requirements.txt                # Dependências Python
├── 📄 README.md                       # Documentação
├── 📄 .env.example                    # Exemplo de configuração
├── 📄 .gitignore                      # Arquivos ignorados pelo Git
├── 📁 controller/
│   ├── 📄 langchain_workflow.py       # Controller tradicional
│   └── 📄 mcp_langchain_workflow.py   # Controller MCP
├── 📁 docs/                           # 📚 Documentação detalhada
│   ├── 📄 create_tools.md             # Guia para criar novas tools
│   └── 📄 templates-examples.md       # Templates e exemplos práticos
├── 📁 services/
│   ├── 📄 langchain_core.py           # Core services tradicional
│   ├── 📄 mcp_langchain_core.py       # Core services MCP
│   └── 📄 polly_services.py           # Síntese de voz
├── 📁 models/
│   └── 📄 amazon_nova_pro.py          # Configuração do modelo Nova Pro
├── 📁 tools/
│   ├── 📄 text_analysis_tool.py       # Ferramentas tradicionais
│   ├── 📄 mcp_tools_server.py         # Servidor MCP (modular)
│   ├── 📄 mcp_base.py                 # Classes base MCP
│   ├── 📄 text_tools.py               # Tools de texto
│   ├── 📄 utility_tools.py            # Tools utilitárias
│   ├── 📄 tool_wrappers.py            # Wrappers para integração
│   └── 📄 tool_loader.py              # Carregador de ferramentas
├── 📁 templates/
│   ├── 📄 prompt_template.py          # Templates de prompt principais
│   └── 📄 template_test_tools.py      # Templates para testes
├── 📁 utils/
│   └── 📄 response_processor.py       # Processamento de respostas
└── 📁 tmp/                            # Arquivos de áudio temporários
    ├── 🎵 tts_audio_*.mp3
    └── ...
```

## 📌 Como executar o projeto

### 1. **Clone o repositório:**
```bash
git clone <repository-url>
cd LangChain-Bedrock
```

### 2. **Configure as dependências:**
```bash
pip install -r requirements.txt
```

### 3. **Configure as variáveis de ambiente:**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais AWS
```

Exemplo do `.env`:
```env
AWS_ACCESS_KEY_ID="your_access_key_here"
AWS_SECRET_ACCESS_KEY="your_secret_key_here"
AWS_REGION="us-east-2"
BEDROCK_MODEL_ID="amazon.nova-pro-v1:0"
```

### 4. **Teste localmente - Arquitetura Tradicional:**
```bash
python lambda_function.py
```

### 5. **Teste localmente - Arquitetura MCP:**
```bash
python lambda_function_mcp.py
```

### 6. **Execute o servidor MCP de ferramentas (opcional):**
```bash
python tools/mcp_tools_server.py
```

### 7. **Deploy no AWS Lambda:**

#### Para arquitetura tradicional:
```bash
zip -r lambda-traditional.zip . -x "*.git*" "*.env" "__pycache__/*" "tmp/*"
```

#### Para arquitetura MCP:
```bash
zip -r lambda-mcp.zip . -x "*.git*" "*.env" "__pycache__/*" "tmp/*"
```

**Configurações do Lambda:**
- Runtime: Python 3.9+
- Handler: `lambda_function.lambda_handler` ou `lambda_function_mcp.mcp_handler`
- Timeout: 60 segundos
- Memory: 1024 MB

**IAM Role necessária:**
```json
{
    "Effect": "Allow",
    "Action": [
        "bedrock:InvokeModel",
        "polly:SynthesizeSpeech"
    ],
    "Resource": "*"
}
```

### 8. **Exemplo de uso da API:**

```json
{
    "query": "Count how many times the letter 'e' appears in the word 'elephant'",
    "voice_id": "Joanna",
    "output_format": "mp3",
    "speed": "medium",
    "use_neural": true,
    "history": []
}
```

**Resposta:**
```json
{
    "statusCode": 200,
    "body": {
        "message": "Query processed successfully",
        "response": {"resposta": "The letter 'e' appears 2 times in the word 'elephant'"},
        "model_used": "amazon.nova-pro-v1:0",
        "tools_used": ["contador_caracteres"],
        "audio_file": "tts_audio_1756807342372.mp3",
        "architecture": "LangChainWorkflow + LangChainCore"
    }
}
```

## � Formato JSON para Requests

### 🔄 Request Básico (Sem Histórico)
```json
{
  "query": "Sua pergunta aqui",
  "history": []
}
```

### 💬 Request com Histórico de Conversação
```json
{
  "query": "Nova pergunta baseada no contexto anterior",
  "history": [
    {
      "role": "user",
      "content": "Pergunta anterior do usuário"
    },
    {
      "role": "assistant", 
      "content": "Resposta anterior do assistente"
    }
  ],
  "voice_id": "Joanna",
  "output_format": "mp3",
  "speed": "medium",
  "use_neural": false
}
```

### 📝 Exemplo Prático: Conversa em Múltiplas Etapas

#### 1️⃣ Primeira Mensagem (sem histórico):
```json
{
  "query": "Olá! Como você está?",
  "history": []
}
```

#### 2️⃣ Segunda Mensagem (com histórico da primeira):
```json
{
  "query": "Você pode me ajudar com análise de texto?",
  "history": [
    {
      "role": "user",
      "content": "Olá! Como você está?"
    },
    {
      "role": "assistant", 
      "content": "Olá! Eu sou uma assistente virtual..."
    }
  ]
}
```

#### 3️⃣ Terceira Mensagem (com histórico completo):
```json
{
  "query": "Conte as palavras na frase 'O gato subiu no telhado'",
  "history": [
    {
      "role": "user",
      "content": "Olá! Como você está?"
    },
    {
      "role": "assistant",
      "content": "Olá! Eu sou uma assistente virtual..."
    },
    {
      "role": "user", 
      "content": "Você pode me ajudar com análise de texto?"
    },
    {
      "role": "assistant",
      "content": "Claro! Posso ajudar com diferentes tipos..."
    }
  ]
}
```

### 🎛️ Parâmetros Disponíveis

| Parâmetro | Tipo | Obrigatório | Padrão | Descrição |
|-----------|------|-------------|---------|-----------|
| `query` | string | ✅ Sim | - | Pergunta/comando para o assistente |
| `history` | array | ❌ Não | `[]` | Histórico da conversa (mensagens anteriores) |
| `voice_id` | string | ❌ Não | `"Joanna"` | Voz para síntese de fala (TTS) |
| `output_format` | string | ❌ Não | `"mp3"` | Formato do áudio: `mp3`, `wav`, `ogg_vorbis` |
| `speed` | string | ❌ Não | `"medium"` | Velocidade: `x-slow`, `slow`, `medium`, `fast`, `x-fast` |
| `use_neural` | boolean | ❌ Não | `true` | Usar engine neural (melhor qualidade) |

### 📤 Formato da Resposta

```json
{
  "statusCode": 200,
  "body": {
    "message": "Query processed successfully",
    "response": {
      "output_response": "A resposta clara e direta do modelo"
    },
    "model_used": "us.amazon.nova-pro-v1:0",
    "mcp_tools_used": ["contador_caracteres", "analisar_texto"],
    "total_tools": 8,
    "history": [
      {
        "role": "user",
        "content": "Sua pergunta"
      },
      {
        "role": "assistant", 
        "content": "A resposta do assistente"
      }
    ],
    "history_length": 2,
    "audio_file": "tts_audio_1756979295673.mp3",
    "audio_duration": 2.5
  }
}
```

### 🧪 Como Testar com Histórico

Use o arquivo `test_with_history.py` incluído no projeto:

```bash
python test_with_history.py
```

Este arquivo demonstra:
- ✅ Conversa progressiva com histórico acumulativo
- ✅ Request único com histórico pré-definido  
- ✅ Preservação de contexto entre mensagens
- ✅ Uso correto das ferramentas MCP

### 🎯 Dicas Importantes

- 🔄 **Contexto**: O histórico preserva o contexto da conversa
- 🛠️ **Ferramentas**: O assistente escolhe automaticamente as ferramentas certas
- 🎵 **TTS**: Cada resposta gera um arquivo de áudio
- 🧠 **Memória**: O modelo "lembra" de conversas anteriores através do histórico
- ⚡ **Performance**: Históricos muito longos podem impactar a performance

## �🕵️ Dificuldades Encontradas

Durante o desenvolvimento do projeto, algumas dificuldades foram enfrentadas:

- **Integração MCP**: Implementação do Model Context Protocol para auto-descoberta de ferramentas exigiu estudo aprofundado da especificação MCP
- **Gerenciamento de Tools**: Criação de um sistema flexível que suporte tanto ferramentas tradicionais quanto MCP tools
- **Processamento de Respostas**: Desenvolvimento do `ResponseProcessor` para lidar com diferentes formatos de resposta do Bedrock
- **Síntese de Voz**: Integração com Amazon Polly via `TTSPollyService` para conversão texto-para-fala em tempo real
- **Comparação de Arquiteturas**: Manutenção de duas implementações paralelas (tradicional vs MCP) para demonstrar benefícios de cada abordagem

---

## 📚 Documentação Adicional

Para desenvolvedores que desejam **criar novas tools** ou estender o sistema:

### 🛠️ Guias para Desenvolvedores

- **[📖 Guia Completo para Criar Tools](./docs/README.md)** - Tutorial detalhado com exemplos
- **[🔧 Templates e Exemplos](./docs/templates-examples.md)** - Templates prontos e casos práticos

### 🎯 O que você encontrará na documentação:

- **🏗️ Arquitetura Overview**: Como o sistema modular funciona
- **🚀 Quick Start**: Crie sua primeira tool em minutos
- **💡 Exemplos Práticos**: Tools de análise de URLs, processamento de dados, QR codes
- **📝 Templates Prontos**: Código base para diferentes tipos de tools
- **🧪 Scripts de Teste**: Ferramentas para validar suas tools
- **📚 Boas Práticas**: Convenções e padrões recomendados

### 🔧 Para adicionar uma nova tool:

1. Escolha o módulo apropriado ou crie um novo
2. Herde de `MCPToolBase` 
3. Implemente `execute()` com sua lógica
4. Registre no `mcp_tools_server.py`
5. Teste usando os scripts fornecidos

**A arquitetura modular torna muito fácil expandir as funcionalidades do assistente!** 🚀
- **Configuração AWS**: Gerenciamento de credenciais e permissões para múltiplos serviços AWS (Bedrock, Polly, Lambda)

**Soluções implementadas:**
- Sistema de auto-descoberta MCP via `get_mcp_tools_functions()`
- Processamento robusto de encoding UTF-8 via `ResponseProcessor`
- Arquitetura modular permitindo fácil extensão de funcionalidades
- Testes automatizados em ambas as arquiteturas para garantir compatibilidade