"""
Tool Wrappers - Módulo para conversão de funções em LangChain BaseTool
Gerencia wrappers para MCP tools e tools tradicionais com parsing inteligente de parâmetros.
"""

import logging
from typing import List, Callable
from langchain_core.tools import BaseTool, tool

logger = logging.getLogger(__name__)


class ToolWrapper:
    """
    Classe responsável por criar wrappers LangChain compatíveis para diferentes tipos de tools.
    """
    
    @staticmethod
    def create_mcp_wrapper(original_func: Callable) -> BaseTool:
        """
        Cria wrapper LangChain para função MCP com parsing inteligente de parâmetros.
        
        Args:
            original_func: Função MCP original
            
        Returns:
            BaseTool: Tool LangChain compatível
        """
        @tool
        def wrapped_tool(input_text: str) -> str:
            """MCP tool wrapper with intelligent parameter parsing"""
            try:
                func_name = original_func.__name__
                return ToolWrapper._execute_mcp_function(original_func, func_name, input_text)
            except Exception as e:
                logger.error(f"Erro na execução da tool {original_func.__name__}: {e}")
                return f"Erro na execução da tool {original_func.__name__}: {str(e)}"
        
        # Define nome e descrição do tool
        wrapped_tool.name = original_func.__name__
        wrapped_tool.description = original_func.__doc__ or f"MCP tool: {original_func.__name__}"
        return wrapped_tool
    
    @staticmethod
    def create_traditional_wrapper(original_func: Callable) -> BaseTool:
        """
        Cria wrapper LangChain para função tradicional.
        
        Args:
            original_func: Função tradicional original
            
        Returns:
            BaseTool: Tool LangChain compatível
        """
        @tool
        def wrapped_traditional_tool(input_text: str) -> str:
            """Traditional tool wrapper"""
            try:
                return original_func(input_text)
            except Exception as e:
                logger.error(f"Erro na execução da tool {original_func.__name__}: {e}")
                return f"Erro na execução da tool {original_func.__name__}: {str(e)}"
        
        wrapped_traditional_tool.name = original_func.__name__
        wrapped_traditional_tool.description = original_func.__doc__ or f"Tool: {original_func.__name__}"
        return wrapped_traditional_tool
    
    @staticmethod
    def _execute_mcp_function(func: Callable, func_name: str, input_text: str) -> str:
        """
        Executa função MCP com parsing inteligente de parâmetros baseado no nome da função.
        
        Args:
            func: Função MCP a ser executada
            func_name: Nome da função para determinar parsing
            input_text: Input do usuário para parsing
            
        Returns:
            str: Resultado da execução da função
        """
        # Mapeamento de funções e seus parsers específicos
        parsers = {
            "contador_caracteres": ToolWrapper._parse_contador_caracteres,
            "calculadora_basica": ToolWrapper._parse_calculadora_basica,
            "analisar_texto": ToolWrapper._parse_analisar_texto,
            "gerar_hash": ToolWrapper._parse_gerar_hash,
        }
        
        # Usa parser específico se disponível, senão executa diretamente
        if func_name in parsers:
            return parsers[func_name](func, input_text)
        else:
            return func(input_text)
    
    @staticmethod
    def _parse_contador_caracteres(func: Callable, input_text: str) -> str:
        """Parser para contador_caracteres: texto,caracter"""
        parts = input_text.split(",", 1)
        if len(parts) == 2:
            return func(parts[0].strip(), parts[1].strip())
        else:
            return func(input_text, "")
    
    @staticmethod
    def _parse_calculadora_basica(func: Callable, input_text: str) -> str:
        """Parser para calculadora_basica: operacao,numero1,numero2"""
        parts = input_text.split(",")
        if len(parts) == 3:
            try:
                return func(parts[0].strip(), float(parts[1].strip()), float(parts[2].strip()))
            except ValueError:
                return "Erro: Números inválidos. Formato: operacao,numero1,numero2"
        else:
            return "Formato: operacao,numero1,numero2 (ex: *,25,8)"
    
    @staticmethod
    def _parse_analisar_texto(func: Callable, input_text: str) -> str:
        """Parser para analisar_texto: texto[,tipo_analise]"""
        parts = input_text.split(",", 1)
        if len(parts) == 2:
            return func(parts[0].strip(), parts[1].strip())
        else:
            return func(input_text)
    
    @staticmethod
    def _parse_gerar_hash(func: Callable, input_text: str) -> str:
        """Parser para gerar_hash: texto[,algoritmo]"""
        parts = input_text.split(",", 1)
        if len(parts) == 2:
            return func(parts[0].strip(), parts[1].strip())
        else:
            return func(input_text)


class ToolDiscovery:
    """
    Classe responsável por descoberta e carregamento de tools MCP e tradicionais.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def discover_mcp_tools(self) -> List[BaseTool]:
        """
        Descobre e carrega MCP tools do servidor dedicado.
        
        Returns:
            List[BaseTool]: Lista de MCP tools convertidas para LangChain
        """
        try:
            from tools.mcp_tools_server import get_mcp_tools_functions
            mcp_functions = get_mcp_tools_functions()
            
            mcp_tools = []
            for func in mcp_functions:
                wrapped = ToolWrapper.create_mcp_wrapper(func)
                mcp_tools.append(wrapped)
            
            self.logger.info(f"Carregadas {len(mcp_tools)} MCP tools do servidor")
            return mcp_tools
            
        except ImportError as e:
            self.logger.warning(f"MCP server não disponível: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao carregar MCP tools: {e}")
            raise
    
    def discover_traditional_tools(self) -> List[BaseTool]:
        """
        Descobre e carrega tools tradicionais como fallback.
        
        Returns:
            List[BaseTool]: Lista de tools tradicionais convertidas para LangChain
        """
        try:
            from tools.tool_loader import get_all_tools
            traditional_functions = get_all_tools()
            
            traditional_tools = []
            for func in traditional_functions:
                wrapped = ToolWrapper.create_traditional_wrapper(func)
                traditional_tools.append(wrapped)
            
            self.logger.info(f"Carregadas {len(traditional_tools)} tools tradicionais")
            return traditional_tools
            
        except ImportError as e:
            self.logger.warning(f"Tools tradicionais não disponíveis: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Erro ao carregar tools tradicionais: {e}")
            raise
    
    def discover_all_tools(self) -> List[BaseTool]:
        """
        Descobre tools com fallback automático: MCP primeiro, tradicional se falhar.
        
        Returns:
            List[BaseTool]: Lista de tools descobertas
        """
        # Tenta MCP tools primeiro
        try:
            return self.discover_mcp_tools()
        except Exception:
            self.logger.info("MCP server não encontrado, usando tools tradicionais como fallback")
            
            # Fallback para tools tradicionais
            try:
                return self.discover_traditional_tools()
            except Exception:
                self.logger.warning("Nenhuma tool encontrada")
                return []


def get_tool_discovery() -> ToolDiscovery:
    """
    Factory function para obter instância de ToolDiscovery.
    
    Returns:
        ToolDiscovery: Instância configurada
    """
    return ToolDiscovery()
