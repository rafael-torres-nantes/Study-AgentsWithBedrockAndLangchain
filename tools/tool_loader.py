"""
Carregador de tools - importa todas as ferramentas disponíveis na pasta tools
"""
from typing import List, Callable

def get_all_tools() -> List[Callable]:
    """
    Carrega todas as tools disponíveis na pasta tools/
    
    Returns:
        List[Callable]: Lista de funções de tools
    """
    tools = []
    
    try:
        # Importa tools do arquivo text_analysis_tool
        from .text_analysis_tool import contador_caracteres, analisar_texto, calculadora_basica
        tools.extend([contador_caracteres, analisar_texto, calculadora_basica])
        
        print(f"[DEBUG] {len(tools)} tools carregadas com sucesso")
        return tools
        
    except Exception as e:
        print(f"[ERROR] Erro ao carregar tools: {e}")
        return []

def list_available_tools() -> List[str]:
    """
    Lista os nomes de todas as tools disponíveis
    
    Returns:
        List[str]: Lista com nomes das tools
    """
    tools = get_all_tools()
    return [tool.name if hasattr(tool, 'name') else tool.__name__ for tool in tools]
