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
                # Se é uma instância de tool (tem método execute)
                if hasattr(original_func, 'execute'):
                    func_name = original_func.name if hasattr(original_func, 'name') else str(original_func.__class__.__name__)
                    return ToolWrapper._execute_traditional_tool(original_func, func_name, input_text)
                else:
                    # É uma função simples
                    return original_func(input_text)
            except Exception as e:
                logger.error(f"Erro na execução da tool {original_func.__name__ if hasattr(original_func, '__name__') else str(original_func)}: {e}")
                return f"Erro na execução da tool: {str(e)}"
        
        # Define nome e descrição do tool
        if hasattr(original_func, 'name'):
            wrapped_traditional_tool.name = original_func.name
        elif hasattr(original_func, '__name__'):
            wrapped_traditional_tool.name = original_func.__name__
        else:
            wrapped_traditional_tool.name = str(original_func.__class__.__name__)
        
        if hasattr(original_func, 'description'):
            wrapped_traditional_tool.description = original_func.description
        elif hasattr(original_func, '__doc__'):
            wrapped_traditional_tool.description = original_func.__doc__ or f"Tool: {wrapped_traditional_tool.name}"
        else:
            wrapped_traditional_tool.description = f"Tool: {wrapped_traditional_tool.name}"
            
        return wrapped_traditional_tool
    
    @staticmethod
    def _execute_traditional_tool(tool_instance, tool_name: str, input_text: str) -> str:
        """
        Executa tool tradicional com parsing específico.
        
        Args:
            tool_instance: Instância da tool
            tool_name: Nome da tool
            input_text: Input do usuário
            
        Returns:
            str: Resultado da execução
        """
        import json
        
        try:
            # Parsers específicos para tools tradicionais
            if "cep" in tool_name.lower():
                # Para CEP: simplesmente passa o texto como CEP
                result = tool_instance.execute(cep=input_text.strip())
            elif "product_search" in tool_name.lower():
                # Para busca de produtos
                if input_text.strip().startswith('{'):
                    params = json.loads(input_text)
                    result = tool_instance.execute(**params)
                else:
                    result = tool_instance.execute(query=input_text.strip())
            elif "product_details" in tool_name.lower():
                # Para detalhes de produto
                result = tool_instance.execute(product_id=input_text.strip())
            elif "category_list" in tool_name.lower():
                # Para lista de categorias
                result = tool_instance.execute()
            elif "unified_agent" in tool_name.lower():
                # Para unified agent tool - usar limite baixo para evitar token overflow
                result = tool_instance.execute(query=input_text.strip())
                # Se o resultado for muito grande, resumir
                if isinstance(result, dict) and len(str(result)) > 3000:
                    # Criar versão resumida
                    summary = {
                        "success": result.get("success", False),
                        "query": result.get("query", ""),
                        "products_found": len(result.get("final_products", [])),
                        "sample_products": result.get("final_products", [])[:3],  # Apenas 3 produtos
                        "summary": result.get("summary", {})
                    }
                    result = summary
            else:
                # Fallback genérico
                result = tool_instance.execute(input_text)
            
            return json.dumps(result, indent=2, ensure_ascii=False)
            
        except Exception as e:
            return f"Erro ao executar {tool_name}: {str(e)}"
    
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
            "consulta_endereco_por_cep": ToolWrapper._parse_consulta_cep,
            "product_search_tool": ToolWrapper._parse_product_search,
            "product_details_tool": ToolWrapper._parse_product_details,
            "category_list_tool": ToolWrapper._parse_category_list,
            "bestseller_products_tool": ToolWrapper._parse_bestseller_products,
            "unified_agent_tool": ToolWrapper._parse_bestseller_products,  # Usar mesmo parser
            "unified_product_search_tool": ToolWrapper._parse_unified_product_search,  # Nova ferramenta
        }
        
        # Usa parser específico se disponível, senão executa diretamente
        if func_name in parsers:
            return parsers[func_name](func, input_text)
        else:
            return func(input_text)
    
    @staticmethod
    def _parse_consulta_cep(func: Callable, input_text: str) -> str:
        """Parser para consulta_endereco_por_cep: cep"""
        import json
        try:
            # Para funções MCP, chama diretamente
            result = func(cep=input_text.strip())
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao consultar CEP: {str(e)}"
    
    @staticmethod
    def _parse_bestseller_products(func: Callable, input_text: str) -> str:
        """Parser inteligente para unified_agent_tool: análise automática de linguagem natural"""
        import json
        import re
        
        try:
            # Para unified_agent_tool, sempre usar execute com query
            result = func(query=input_text.strip())
            
            # Se o resultado já é uma string JSON, retorna diretamente
            if isinstance(result, str):
                return result
            else:
                # Para dicionários grandes, fazer resumo
                if isinstance(result, dict) and len(str(result)) > 3000:
                    summary = {
                        "success": result.get("success", False),
                        "query": result.get("query", ""),
                        "search_type": result.get("search_type", ""),
                        "products_found": len(result.get("final_products", [])),
                        "sample_products": result.get("final_products", [])[:5],  # Apenas 5 produtos
                        "summary": result.get("summary", {})
                    }
                    result = summary
                
                return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao buscar produtos: {str(e)}"
    
    @staticmethod
    def _parse_product_search(func: Callable, input_text: str) -> str:
        """Parser para product_search_tool: query[,category,price_min,price_max,sort_by,sort_order]"""
        import json
        try:
            # Tenta parsing JSON se o input parecer um JSON
            if input_text.strip().startswith('{'):
                params = json.loads(input_text)
                result = func(**params)
            else:
                # Parsing simples para texto
                result = func(query=input_text.strip())
            
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao buscar produtos: {str(e)}"
    
    @staticmethod
    def _parse_product_details(func: Callable, input_text: str) -> str:
        """Parser para product_details_tool: product_id"""
        import json
        try:
            result = func(product_id=input_text.strip())
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao obter detalhes do produto: {str(e)}"
    
    @staticmethod
    def _parse_category_list(func: Callable, input_text: str) -> str:
        """Parser para category_list_tool: sem parâmetros"""
        import json
        try:
            result = func()
            if isinstance(result, str):
                return result
            return json.dumps(result, indent=2, ensure_ascii=False)
        except Exception as e:
            return f"Erro ao listar categorias: {str(e)}"
    
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

    @staticmethod
    def _parse_unified_product_search(func: Callable, input_text: str) -> str:
        """Parser para unified_product_search_tool: busca inteligente de produtos"""
        try:
            # Para a ferramenta de busca de produtos, sempre usar execute com query
            return func.execute(query=input_text)
        except Exception as e:
            logger.error(f"Erro no parser unified_product_search: {e}")
            return f"Erro na busca de produtos: {str(e)}"


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
            # Import com caminho absoluto
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from mcp_files.server.mcp_tools_server import get_mcp_tools_functions
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
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
            from mcp_files.core.tool_loader import get_all_tools
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
