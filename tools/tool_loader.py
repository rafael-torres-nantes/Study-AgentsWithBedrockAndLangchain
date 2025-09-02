"""
Carregador de tools - importa todas as ferramentas disponíveis na pasta tools
Inclui suporte para tools MCP (Model Context Protocol)
"""
from typing import List, Callable
from tools.mcp_tools_server import get_mcp_tools_functions

def get_all_tools() -> List[Callable]:
    """
    Carrega todas as tools disponíveis na pasta tools/
    Inclui tanto tools tradicionais quanto tools MCP
    
    Returns:
        List[Callable]: Lista de funções de tools
    """
    tools = []
    
    try:
        # Importa tools do arquivo text_analysis_tool (versão tradicional)
        from .text_analysis_tool import contador_caracteres, analisar_texto, calculadora_basica
        tools.extend([contador_caracteres, analisar_texto, calculadora_basica])
        
        print(f"[DEBUG] {len(tools)} tools tradicionais carregadas")
        
        # Importa tools MCP do novo servidor
        try:
            mcp_tools = get_mcp_tools_functions()
            
            # Nota: As tools MCP são carregadas de forma diferente pelos agentes MCP
            print(f"[DEBUG] {len(mcp_tools)} tools MCP disponíveis")
        except ImportError as e:
            print(f"[WARNING] Tools MCP não disponíveis: {e}")
        
        print(f"[DEBUG] Total de {len(tools)} tools carregadas com sucesso")
        return tools
        
    except Exception as e:
        print(f"[ERROR] Erro ao carregar tools: {e}")
        return []

def get_mcp_tools() -> List[Callable]:
    """
    Carrega especificamente as tools MCP
    
    Returns:
        List[Callable]: Lista de funções de tools MCP
    """
    try:
        mcp_tools = get_mcp_tools_functions()
        print(f"[DEBUG] {len(mcp_tools)} tools MCP carregadas")
        return mcp_tools
   
    except Exception as e:
        print(f"[ERROR] Erro ao carregar tools MCP: {e}")
        return []

def list_available_tools() -> List[str]:
    """
    Lista os nomes de todas as tools disponíveis (tradicionais)
    
    Returns:
        List[str]: Lista com nomes das tools
    """
    tools = get_all_tools()
    return [tool.name if hasattr(tool, 'name') else tool.__name__ for tool in tools]

def list_mcp_tools() -> List[str]:
    """
    Lista os nomes de todas as tools MCP disponíveis
    
    Returns:
        List[str]: Lista com nomes das tools MCP
    """
    try:
        from .mcp_tools_server import get_mcp_tools_names
        return get_mcp_tools_names()
    except Exception as e:
        print(f"[ERROR] Erro ao listar tools MCP: {e}")
        return []
