# 🛠️ Guia para Criar Novas MCP Tools

Este guia mostra como adicionar novas ferramentas ao sistema MCP Tools usando a arquitetura modular.

## 📋 Índice

- [🏗️ Arquitetura Overview](#-arquitetura-overview)
- [🚀 Quick Start - Criando sua Primeira Tool](#-quick-start---criando-sua-primeira-tool)
- [📝 Estrutura de uma Tool](#-estrutura-de-uma-tool)
- [💡 Exemplos Práticos](#-exemplos-práticos)
- [🔧 Registrando a Tool](#-registrando-a-tool)
- [🧪 Testando sua Tool](#-testando-sua-tool)
- [📚 Boas Práticas](#-boas-práticas)

---

## 🏗️ Arquitetura Overview

O sistema usa uma arquitetura modular baseada em classes que herdam de `MCPToolBase`:

```
tools/
├── mcp_base.py           # Classes base e utilitários
├── text_tools.py         # Tools de análise de texto
├── utility_tools.py      # Tools de utilidades/matemática
├── mcp_tools_server.py   # Servidor e registry principal
└── [seu_novo_modulo].py  # Sua nova categoria de tools
```

### 🏛️ Classes Principais

- **`MCPToolBase`**: Classe abstrata base para todas as tools
- **`MCPResponseBuilder`**: Builder para respostas padronizadas 
- **`MCPToolValidator`**: Validadores comuns para parâmetros
- **`MCPToolsRegistry`**: Gerenciamento centralizado de tools

---

## 🚀 Quick Start - Criando sua Primeira Tool

### 1️⃣ Escolha onde adicionar sua tool:

**Opção A: Módulo existente**
- `text_tools.py` - Análise de texto, NLP, etc.
- `utility_tools.py` - Matemática, conversões, etc.

**Opção B: Novo módulo**
- Crie `web_tools.py`, `file_tools.py`, `ai_tools.py`, etc.

### 2️⃣ Template básico:

```python
from typing import Dict, Any
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator

class MinhaNovaTool(MCPToolBase):
    """
    Descrição da sua tool.
    """
    
    def __init__(self):
        super().__init__(
            name="minha_nova_tool",
            description="O que esta tool faz"
        )
    
    def validate_input(self, parametro1: str, parametro2: int = 0) -> bool:
        """Valida parâmetros de entrada."""
        return MCPToolValidator.validate_text(parametro1)
    
    def execute(self, parametro1: str, parametro2: int = 0) -> Dict[str, Any]:
        """
        Lógica principal da tool.
        
        Args:
            parametro1: Descrição do parâmetro
            parametro2: Parâmetro opcional
            
        Returns:
            Dict com resultado da operação
        """
        # Sua lógica aqui
        resultado = f"Processado: {parametro1}"
        
        return (MCPResponseBuilder("minha_operacao")
                .add_input_info(entrada=parametro1, valor=parametro2)
                .add_result(resultado=resultado)
                .add_summary(f"Operação realizada com sucesso")
                .build())
```

### 3️⃣ Registre a tool:

Em `mcp_tools_server.py`, adicione sua tool na lista:

```python
def _register_default_tools(self):
    default_tools = [
        # ... tools existentes ...
        MinhaNovaToolEm(),  # ← Adicione aqui
    ]
```

---

## 📝 Estrutura de uma Tool

### 🏗️ Métodos Obrigatórios

```python
class ExemploTool(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="nome_da_tool",  # Nome único (snake_case)
            description="Descrição clara do que faz"
        )
    
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """Lógica principal - OBRIGATÓRIO implementar"""
        pass
```

### 🔧 Métodos Opcionais

```python
def validate_input(self, *args, **kwargs) -> bool:
    """Validação customizada de parâmetros"""
    return True

def format_response(self, result: Dict[str, Any]) -> str:
    """Formatação customizada da resposta"""
    return super().format_response(result)
```

### 📊 Padrão de Resposta

Use `MCPResponseBuilder` para respostas consistentes:

```python
return (MCPResponseBuilder("tipo_operacao")
        .add_input_info(parametro1=valor1, parametro2=valor2)
        .add_result(resultado=resultado_principal, detalhes=info_extra)
        .add_summary("Resumo em uma linha")
        .build())
```

---

## 💡 Exemplos Práticos

### 📊 Exemplo 1: Tool de Análise de URLs

```python
import requests
from urllib.parse import urlparse
from typing import Dict, Any
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator

class AnalisadorURL(MCPToolBase):
    """
    Tool para analisar informações básicas de uma URL.
    """
    
    def __init__(self):
        super().__init__(
            name="analisador_url",
            description="Analisa uma URL e retorna informações básicas como domínio, protocolo e status"
        )
    
    def validate_input(self, url: str) -> bool:
        """Valida se a URL tem formato válido."""
        if not MCPToolValidator.validate_text(url, "url"):
            return False
        
        try:
            parsed = urlparse(url)
            return bool(parsed.scheme and parsed.netloc)
        except Exception:
            return False
    
    def execute(self, url: str) -> Dict[str, Any]:
        """
        Analisa a URL fornecida.
        
        Args:
            url: URL para análise
            
        Returns:
            Dict com informações da URL
        """
        parsed_url = urlparse(url)
        
        # Informações básicas da URL
        url_info = {
            "protocolo": parsed_url.scheme,
            "dominio": parsed_url.netloc,
            "caminho": parsed_url.path,
            "parametros": parsed_url.query,
            "fragmento": parsed_url.fragment
        }
        
        # Tenta verificar status HTTP
        try:
            response = requests.head(url, timeout=5, allow_redirects=True)
            status_info = {
                "status_code": response.status_code,
                "status_ok": response.status_code < 400,
                "content_type": response.headers.get('content-type', 'N/A'),
                "server": response.headers.get('server', 'N/A')
            }
        except Exception as e:
            status_info = {
                "status_code": None,
                "status_ok": False,
                "erro": str(e)
            }
        
        return (MCPResponseBuilder("analise_url")
                .add_input_info(url_analisada=url)
                .add_result(
                    informacoes_url=url_info,
                    status_http=status_info
                )
                .add_summary(f"URL {parsed_url.netloc} analisada - Status: {status_info.get('status_code', 'Erro')}")
                .build())
```

### 🧮 Exemplo 2: Tool de Operações com Listas

```python
from typing import Dict, Any, List, Union
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator

class ProcessadorLista(MCPToolBase):
    """
    Tool para operações matemáticas com listas de números.
    """
    
    def __init__(self):
        super().__init__(
            name="processador_lista",
            description="Realiza operações matemáticas em listas: soma, média, máximo, mínimo, etc."
        )
    
    def validate_input(self, numeros: str, operacao: str = "soma") -> bool:
        """Valida entrada de números e operação."""
        if not MCPToolValidator.validate_text(numeros, "numeros"):
            return False
        
        operacoes_validas = ["soma", "media", "maximo", "minimo", "mediana", "moda"]
        return MCPToolValidator.validate_operation(operacao, operacoes_validas)
    
    def _parse_numbers(self, numeros_str: str) -> List[float]:
        """Converte string de números em lista."""
        try:
            # Suporta separação por vírgula, espaço ou ponto-e-vírgula
            import re
            numeros = re.split(r'[,;\s]+', numeros_str.strip())
            return [float(n.strip()) for n in numeros if n.strip()]
        except Exception:
            return []
    
    def execute(self, numeros: str, operacao: str = "soma") -> Dict[str, Any]:
        """
        Processa lista de números conforme operação solicitada.
        
        Args:
            numeros: String com números separados por vírgula/espaço
            operacao: Tipo de operação (soma, media, maximo, minimo, mediana, moda)
            
        Returns:
            Dict com resultado da operação
        """
        lista_numeros = self._parse_numbers(numeros)
        
        if not lista_numeros:
            raise ValueError("Nenhum número válido foi encontrado na entrada")
        
        # Realiza a operação solicitada
        if operacao == "soma":
            resultado = sum(lista_numeros)
        elif operacao == "media":
            resultado = sum(lista_numeros) / len(lista_numeros)
        elif operacao == "maximo":
            resultado = max(lista_numeros)
        elif operacao == "minimo":
            resultado = min(lista_numeros)
        elif operacao == "mediana":
            sorted_nums = sorted(lista_numeros)
            n = len(sorted_nums)
            resultado = (sorted_nums[n//2] + sorted_nums[(n-1)//2]) / 2
        elif operacao == "moda":
            from collections import Counter
            counts = Counter(lista_numeros)
            resultado = counts.most_common(1)[0][0]
        
        return (MCPResponseBuilder("processamento_lista")
                .add_input_info(
                    numeros_originais=numeros,
                    operacao_solicitada=operacao,
                    total_numeros=len(lista_numeros)
                )
                .add_result(
                    lista_processada=lista_numeros,
                    resultado=round(resultado, 4),
                    operacao=operacao
                )
                .add_summary(f"{operacao.capitalize()} de {len(lista_numeros)} números: {round(resultado, 4)}")
                .build())
```

### 🌐 Exemplo 3: Tool de Geração de QR Code

```python
import base64
from io import BytesIO
from typing import Dict, Any
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator

class GeradorQRCode(MCPToolBase):
    """
    Tool para gerar QR Codes a partir de texto.
    """
    
    def __init__(self):
        super().__init__(
            name="gerador_qrcode",
            description="Gera QR Code a partir de texto e retorna em base64"
        )
    
    def validate_input(self, texto: str, tamanho: int = 10) -> bool:
        """Valida texto e tamanho do QR."""
        return (
            MCPToolValidator.validate_text(texto, "texto") and
            isinstance(tamanho, int) and 1 <= tamanho <= 20
        )
    
    def execute(self, texto: str, tamanho: int = 10) -> Dict[str, Any]:
        """
        Gera QR Code do texto fornecido.
        
        Args:
            texto: Texto para converter em QR Code
            tamanho: Tamanho do QR (1-20, padrão 10)
            
        Returns:
            Dict com QR Code em base64
        """
        try:
            import qrcode
            from PIL import Image
            
            # Configura o QR Code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=tamanho,
                border=4,
            )
            
            qr.add_data(texto)
            qr.make(fit=True)
            
            # Gera a imagem
            img = qr.make_image(fill_color="black", back_color="white")
            
            # Converte para base64
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return (MCPResponseBuilder("geracao_qrcode")
                    .add_input_info(
                        texto_original=texto,
                        tamanho_box=tamanho,
                        caracteres=len(texto)
                    )
                    .add_result(
                        qrcode_base64=img_base64,
                        formato="PNG",
                        encoding="base64"
                    )
                    .add_summary(f"QR Code gerado para texto de {len(texto)} caracteres")
                    .build())
                    
        except ImportError:
            raise ImportError("Bibliotecas qrcode e Pillow são necessárias: pip install qrcode[pil]")
```

---

## 🔧 Registrando a Tool

### 1️⃣ Em módulo existente:

Se adicionou em `text_tools.py` ou `utility_tools.py`, apenas registre:

```python
# mcp_tools_server.py
def _register_default_tools(self):
    default_tools = [
        ContadorCaracteres(),
        AnalisadorTexto(),
        # ... outras tools ...
        AnalisadorURL(),        # ← Nova tool
        ProcessadorLista(),     # ← Nova tool
    ]
```

### 2️⃣ Em novo módulo:

Se criou `web_tools.py`, adicione o import:

```python
# mcp_tools_server.py - no topo do arquivo
from .web_tools import AnalisadorURL, GeradorQRCode

# E registre na lista
def _register_default_tools(self):
    default_tools = [
        # ... tools existentes ...
        AnalisadorURL(),
        GeradorQRCode(),
    ]
```

---

## 🧪 Testando sua Tool

### 🔬 Teste Individual

```python
# Teste direto da tool
from tools.web_tools import AnalisadorURL

tool = AnalisadorURL()
resultado = tool("https://www.google.com")
print(resultado)
```

### 🏗️ Teste via Registry

```python
# Teste via servidor MCP
from tools.mcp_tools_server import get_mcp_server

server = get_mcp_server()
tool = server.registry.get_tool('analisador_url')
resultado = tool("https://www.google.com")
print(resultado)
```

### 🧪 Teste Completo do Workflow

```python
# Teste integração completa
from controller.mcp_langchain_workflow import MCPLangChainWorkflow

workflow = MCPLangChainWorkflow()
tools = workflow._discover_mcp_tools()

# Verifica se sua tool foi carregada
tool_names = [t.name for t in tools]
print(f"Tools carregadas: {tool_names}")
print(f"Minha tool está presente: {'analisador_url' in tool_names}")
```

---

## 📚 Boas Práticas

### ✅ Nomenclatura

- **Nome da tool**: `snake_case`, descritivo
- **Nome da classe**: `PascalCase`
- **Parâmetros**: nomes claros e intuitivos

```python
# ✅ Bom
class ConversorTemperatura(MCPToolBase):
    def __init__(self):
        super().__init__(
            name="conversor_temperatura",
            description="Converte temperaturas entre Celsius, Fahrenheit e Kelvin"
        )

# ❌ Evitar
class TempConv(MCPToolBase):
    def __init__(self):
        super().__init__(name="temp", description="Converte temp")
```

### 🛡️ Validação Robusta

```python
def validate_input(self, entrada: str, opcao: str = "padrao") -> bool:
    """Sempre valide entradas para evitar erros."""
    if not MCPToolValidator.validate_text(entrada):
        return False
    
    opcoes_validas = ["padrao", "avancado", "simples"]
    if opcao not in opcoes_validas:
        return False
    
    # Validações específicas da sua tool
    if len(entrada) > 1000:  # Exemplo: limite de tamanho
        return False
    
    return True
```

### 📝 Documentação Clara

```python
def execute(self, texto: str, formato: str = "json") -> Dict[str, Any]:
    """
    Descrição clara do que a função faz.
    
    Args:
        texto: Descrição do parâmetro com exemplo se necessário
        formato: Formato de saída (json, xml, csv). Padrão: json
        
    Returns:
        Dict com estrutura bem definida:
        - resultado: Resultado principal da operação
        - metadados: Informações extras sobre o processamento
        
    Raises:
        ValueError: Quando texto está vazio
        TypeError: Quando formato não é suportado
    """
```

### 🏗️ Use MCPResponseBuilder

```python
# ✅ Consistente e estruturado
return (MCPResponseBuilder("operacao_realizada")
        .add_input_info(entrada=texto, opcoes=parametros)
        .add_result(resultado=resultado_principal, detalhes=info_extra)
        .add_summary("Operação concluída com sucesso")
        .build())

# ❌ Evitar retorno manual
return {
    "result": resultado,
    "info": "alguma coisa"  # Inconsistente
}
```

### 🔄 Tratamento de Erros

```python
def execute(self, dados: str) -> Dict[str, Any]:
    try:
        # Sua lógica principal
        resultado = processar_dados(dados)
        
        return (MCPResponseBuilder("processamento")
                .add_result(resultado=resultado)
                .build())
                
    except ValueError as e:
        # Erros de validação específicos
        raise ValueError(f"Dados inválidos: {e}")
    except Exception as e:
        # Outros erros
        self.logger.error(f"Erro inesperado: {e}")
        raise RuntimeError(f"Falha no processamento: {e}")
```

### 📊 Performance

```python
def execute(self, dados_grandes: str) -> Dict[str, Any]:
    # Para operações pesadas, adicione logs de progresso
    self.logger.info(f"Iniciando processamento de {len(dados_grandes)} caracteres")
    
    # Considere limites de processamento
    if len(dados_grandes) > 100000:
        raise ValueError("Entrada muito grande, máximo 100KB")
    
    # Use geradores para dados grandes
    for i, chunk in enumerate(processar_em_chunks(dados_grandes)):
        if i % 100 == 0:
            self.logger.debug(f"Processados {i} chunks")
    
    return resultado
```

---

## 🎯 Checklist Final

Antes de considerar sua tool pronta:

- [ ] **Nome único e descritivo**
- [ ] **Herda de `MCPToolBase`**
- [ ] **Implementa `execute()` obrigatório**
- [ ] **Validação robusta em `validate_input()`**
- [ ] **Usa `MCPResponseBuilder` para respostas**
- [ ] **Documentação clara com docstrings**
- [ ] **Tratamento de erros adequado**
- [ ] **Testada individualmente**
- [ ] **Registrada no servidor MCP**
- [ ] **Testada via workflow completo**

---

## 🚀 Exemplos Avançados

Para tools mais complexas, consulte:
- `text_tools.py` - Exemplos de análise de texto
- `utility_tools.py` - Exemplos de operações matemáticas
- `mcp_base.py` - Classes base e utilitários

**Happy coding! 🎉**
