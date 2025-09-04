"""
Lambda-compatible FastMCP implementation
Implementação simplificada do FastMCP para ambientes Lambda AWS
que não suportam uvicorn/servidor completo.
"""

import logging
from typing import List, Callable, Dict, Any
from functools import wraps

logger = logging.getLogger(__name__)


class FastMCP:
    """
    Implementação simplificada do FastMCP para ambientes Lambda.
    
    Esta classe mantém a compatibilidade com a interface FastMCP original,
    mas remove dependências de servidor web que não funcionam em Lambda.
    """
    
    def __init__(self, server_name: str = "Lambda-MCP-Server"):
        """
        Inicializa o servidor MCP simplificado para Lambda.
        
        Args:
            server_name: Nome do servidor MCP
        """
        self.server_name = server_name
        self.tools = {}
        self.app = None  # Compatibilidade - não usado em Lambda
        logger.info(f"FastMCP Lambda-compatible server '{server_name}' initialized")
    
    def tool(self, name: str = None, description: str = None):
        """
        Decorator para registrar tools MCP.
        
        Args:
            name: Nome da tool (opcional, usa nome da função se não fornecido)
            description: Descrição da tool (opcional, usa docstring se não fornecida)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or func.__doc__ or f"MCP tool: {tool_name}"
            
            # Wrapper que mantém compatibilidade MCP
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    result = func(*args, **kwargs)
                    logger.debug(f"MCP tool '{tool_name}' executed successfully")
                    return result
                except Exception as e:
                    error_msg = f"Error in MCP tool '{tool_name}': {str(e)}"
                    logger.error(error_msg)
                    return error_msg
            
            # Registra a tool
            self.tools[tool_name] = {
                'function': wrapper,
                'name': tool_name,
                'description': tool_description,
                'original_function': func
            }
            
            logger.debug(f"MCP tool '{tool_name}' registered successfully")
            return wrapper
        
        return decorator
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """
        Retorna todas as tools registradas.
        
        Returns:
            Dict com informações das tools
        """
        return self.tools.copy()
    
    def get_tool_functions(self) -> List[Callable]:
        """
        Retorna lista de funções das tools para compatibilidade.
        
        Returns:
            Lista de funções das tools
        """
        return [tool_info['function'] for tool_info in self.tools.values()]