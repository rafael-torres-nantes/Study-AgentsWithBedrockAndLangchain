"""
MCP Tools Server - Servidor modular de ferramentas usando Model Context Protocol
Arquitetura refatorada com separação de responsabilidades e código limpo.
"""

import logging
from typing import List, Callable, Dict, Any

# Lambda-compatible FastMCP implementation
try:
    from mcp.server.fastmcp import FastMCP
    print("Using original FastMCP implementation")
except ImportError:
    # CORREÇÃO: Alterado o import para ser absoluto
    from mcp_files.server.lambda_fastmcp import FastMCP
    print("Using Lambda-compatible FastMCP implementation")

# CORREÇÃO: Imports alterados para caminhos absolutos e corretos,
# incluindo todas as classes de ferramentas MCP disponíveis.
from tools.cep_api_tools import ConsultaEnderecoPorCEP
from tools.countries_api_tools import ConsultaInformacoesPais
from tools.text_tools import ContadorCaracteres, AnalisadorTexto, AnalisadorSentimento, ExtratorEmail
from tools.utility_tools import CalculadoraBasica, GeradorHash


# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPToolsRegistry:
    """
    Registro centralizado de todas as MCP tools disponíveis.
    Facilita adição, remoção e gerenciamento de tools.
    """
    
    def __init__(self):
        self.tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """Registra todas as tools padrão do sistema."""
        # CORREÇÃO: Adicionadas todas as classes de ferramentas MCP para registro.
        default_tools = [
            ConsultaEnderecoPorCEP(),
            ConsultaInformacoesPais(),
            ContadorCaracteres(),
            AnalisadorTexto(),
            AnalisadorSentimento(),
            ExtratorEmail(),
            CalculadoraBasica(),
            GeradorHash()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
        
        logger.info(f"Registradas {len(default_tools)} tools padrão")
    
    def register_tool(self, tool):
        """
        Registra uma nova tool no sistema.
        
        Args:
            tool: Instância de MCPToolBase
        """
        self.tools[tool.name] = tool
        logger.debug(f"Tool '{tool.name}' registrada com sucesso")
    
    def unregister_tool(self, tool_name: str):
        """
        Remove uma tool do sistema.
        
        Args:
            tool_name: Nome da tool a ser removida
        """
        if tool_name in self.tools:
            del self.tools[tool_name]
            logger.debug(f"Tool '{tool_name}' removida com sucesso")
        else:
            logger.warning(f"Tool '{tool_name}' não encontrada para remoção")
    
    def get_tool(self, tool_name: str):
        """
        Obtém uma tool específica.
        
        Args:
            tool_name: Nome da tool
            
        Returns:
            Tool ou None se não encontrada
        """
        return self.tools.get(tool_name)
    
    def get_all_tools(self) -> List:
        """
        Retorna todas as tools registradas.
        
        Returns:
            Lista de tools
        """
        return list(self.tools.values())
    
    def get_tool_names(self) -> List[str]:
        """
        Retorna nomes de todas as tools registradas.
        
        Returns:
            Lista de nomes
        """
        return list(self.tools.keys())
    
    def get_tools_info(self) -> Dict[str, str]:
        """
        Retorna informações sobre todas as tools.
        
        Returns:
            Dicionário com nome e descrição de cada tool
        """
        return {name: tool.description for name, tool in self.tools.items()}


class MCPToolsServer:
    """
    Servidor MCP que integra todas as tools de forma modular.
    """
    
    def __init__(self, server_name: str = "LangChain-Agent-Tools"):
        self.server_name = server_name
        self.registry = MCPToolsRegistry()
        self.mcp_server = FastMCP(server_name)
        self._register_mcp_tools()
    
    def _register_mcp_tools(self):
        """Registra todas as tools no servidor MCP."""
        for tool in self.registry.get_all_tools():
            # Cria wrapper para compatibilidade com FastMCP
            self._create_mcp_wrapper(tool)
        
        logger.info(f"Servidor MCP '{self.server_name}' configurado com {len(self.registry.tools)} tools")
    
    def _create_mcp_wrapper(self, tool):
        """
        Cria wrapper MCP para uma tool específica.
        
        Args:
            tool: Instância de MCPToolBase
        """
        @self.mcp_server.tool()
        def mcp_wrapper(*args, **kwargs):
            return tool(*args, **kwargs)
        
        # Define metadados da tool
        mcp_wrapper.__name__ = tool.name
        mcp_wrapper.__doc__ = tool.description
    
    def get_functions_list(self) -> List[Callable]:
        """
        Retorna lista de funções para compatibilidade com sistema existente.
        
        Returns:
            Lista de funções das tools
        """
        functions = []
        for tool in self.registry.get_all_tools():
            # Cria função compatível para cada tool
            def create_function(tool_instance):
                def tool_function(*args, **kwargs):
                    return tool_instance(*args, **kwargs)
                tool_function.__name__ = tool_instance.name
                tool_function.__doc__ = tool_instance.description
                return tool_function
            
            functions.append(create_function(tool))
        
        return functions
    
    def run_server(self, host: str = "localhost", port: int = 8000):
        """
        Inicia o servidor MCP.
        
        Args:
            host: Host do servidor
            port: Porta do servidor
        """
        import uvicorn
        logger.info(f"Iniciando servidor MCP '{self.server_name}' em {host}:{port}")
        uvicorn.run(self.mcp_server.app, host=host, port=port)


# Instância global do servidor (singleton)
_mcp_server = None


def get_mcp_server() -> MCPToolsServer:
    """
    Factory function para obter instância do servidor MCP.
    
    Returns:
        MCPToolsServer: Instância do servidor
    """
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPToolsServer()
    return _mcp_server


# Funções de compatibilidade com sistema existente
def get_mcp_tools_functions() -> List[Callable]:
    """
    Retorna lista de funções MCP para compatibilidade.
    
    Returns:
        List[Callable]: Lista de funções das tools
    """
    server = get_mcp_server()
    return server.get_functions_list()


def get_mcp_tools_names() -> List[str]:
    """
    Retorna nomes de todas as tools MCP.
    
    Returns:
        List[str]: Lista com nomes das tools
    """
    server = get_mcp_server()
    return server.registry.get_tool_names()


def get_mcp_tools():
    """
    Função de compatibilidade para wrapper LangChain.
    Esta função é mantida para não quebrar integrações existentes,
    mas o parsing é agora feito no módulo tool_wrappers.py
    
    Returns:
        List: Lista de funções MCP
    """
    logger.info("Usando get_mcp_tools_functions() via tool_wrappers.py para melhor modularidade")
    return get_mcp_tools_functions()


def run_mcp_tools_server(host: str = "localhost", port: int = 8000):
    """
    Inicia o servidor MCP de ferramentas.
    
    Args:
        host: Host do servidor
        port: Porta do servidor
    """
    server = get_mcp_server()
    server.run_server(host, port)


if __name__ == "__main__":
    # Inicia o servidor MCP quando executado diretamente
    run_mcp_tools_server()