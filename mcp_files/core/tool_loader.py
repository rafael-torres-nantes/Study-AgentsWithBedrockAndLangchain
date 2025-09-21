"""
Carregador de tools - importa todas as ferramentas disponíveis na pasta tools
Versão atualizada com UnifiedAgentTool e apenas tools existentes
"""
import sys
import os
from typing import List, Callable

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def get_all_tools() -> List[Callable]:
    """
    Carrega todas as tools disponíveis na pasta tools/
    Inclui tanto tools tradicionais quanto tools MCP
    
    Returns:
        List[Callable]: Lista de funções de tools
    """
    tools = []
    
    try:
        # Importa tool de CEP
        from tools.cep_api_tools import consulta_endereco_por_cep
        tools.append(consulta_endereco_por_cep)
        print(f"[DEBUG] CEP tool carregada: {consulta_endereco_por_cep.name}")
        
        # Importa tool de detalhes de produto (existente)
        try:
            from tools.ishopmeta_product_details import product_details_tool
            tools.append(product_details_tool)
            print(f"[DEBUG] Product details tool carregada: {product_details_tool.name}")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar product_details_tool: {e}")
        
        # Importa vendor information tool (existente)
        try:
            from tools.ishopmeta_vendor_information import vendor_information_tool
            tools.append(vendor_information_tool)
            print(f"[DEBUG] Vendor information tool carregada: {vendor_information_tool.name}")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar vendor_information_tool: {e}")
        
        # Importa system settings tool (existente)
        try:
            from tools.ishopmeta_system_settings import system_settings_tool
            tools.append(system_settings_tool)
            print(f"[DEBUG] System settings tool carregada: {system_settings_tool.name}")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar system_settings_tool: {e}")
        
        # Nova ferramenta unificada (substitui bestseller e category mapper)
        try:
            from tools.unified_agent_tool import UnifiedAgentTool
            unified_tool = UnifiedAgentTool()
            # Adapter para usar como tool tradicional
            class UnifiedToolAdapter:
                def __init__(self, unified_agent):
                    self.unified_agent = unified_agent
                    self.name = "unified_agent_tool"
                    self.description = "Ferramenta unificada para consultar CSVs e buscar produtos via iShopMeta API"
                
                def execute(self, query: str = None, **kwargs):
                    if query:
                        return self.unified_agent.process_agent_query(query)
                    else:
                        return {"error": "Query é obrigatória"}
            
            tools.append(UnifiedToolAdapter(unified_tool))
            print(f"[DEBUG] Unified Agent Tool carregada: unified_agent_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar unified_agent_tool: {e}")
        
        # Nova ferramenta de busca de produtos com API correta
        try:
            from tools.unified_product_search import UnifiedProductSearchTool
            product_search_tool = UnifiedProductSearchTool()
            # Adapter para usar como tool tradicional
            class ProductSearchAdapter:
                def __init__(self, product_search):
                    self.product_search = product_search
                    self.name = "unified_product_search_tool"
                    self.description = "Ferramenta para buscar produtos usando a API correta com filtros inteligentes"
                
                def execute(self, query: str = None, limit: int = 20, **kwargs):
                    if query:
                        return self.product_search.search_products(query, limit)
                    else:
                        return {"error": "Query é obrigatória"}
            
            tools.append(ProductSearchAdapter(product_search_tool))
            print(f"[DEBUG] Unified Product Search Tool carregada: unified_product_search_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar unified_product_search_tool: {e}")
        
        # Ferramenta de busca por marca
        try:
            from tools.brand_search_tool import BrandSearchTool
            brand_search = BrandSearchTool()
            # Adapter para usar como tool tradicional
            class BrandSearchAdapter:
                def __init__(self, brand_search):
                    self.brand_search = brand_search
                    self.name = "brand_search_tool"
                    self.description = "Ferramenta para buscar produtos por marca específica"
                
                def execute(self, brand_name: str = None, limit: int = 20, **kwargs):
                    if brand_name:
                        return self.brand_search.execute(brand_name, limit=limit)
                    else:
                        return {"error": "Brand name é obrigatório"}
            
            tools.append(BrandSearchAdapter(brand_search))
            print(f"[DEBUG] Brand Search Tool carregada: brand_search_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar brand_search_tool: {e}")
        
        # Ferramenta de busca por categoria
        try:
            from tools.category_search_tool import CategorySearchTool
            category_search = CategorySearchTool()
            # Adapter para usar como tool tradicional
            class CategorySearchAdapter:
                def __init__(self, category_search):
                    self.category_search = category_search
                    self.name = "category_search_tool"
                    self.description = "Ferramenta para buscar produtos por categoria específica"
                
                def execute(self, category_name: str = None, limit: int = 20, **kwargs):
                    if category_name:
                        return self.category_search.execute(category_name, limit=limit)
                    else:
                        return {"error": "Category name é obrigatório"}
            
            tools.append(CategorySearchAdapter(category_search))
            print(f"[DEBUG] Category Search Tool carregada: category_search_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar category_search_tool: {e}")
        
        # Ferramenta de busca por departamento
        try:
            from tools.department_search_tool import DepartmentSearchTool
            department_search = DepartmentSearchTool()
            # Adapter para usar como tool tradicional
            class DepartmentSearchAdapter:
                def __init__(self, department_search):
                    self.department_search = department_search
                    self.name = "department_search_tool"
                    self.description = "Ferramenta para buscar produtos por departamento específico"
                
                def execute(self, department_name: str = None, limit: int = 20, **kwargs):
                    if department_name:
                        return self.department_search.execute(department_name, limit=limit)
                    else:
                        return {"error": "Department name é obrigatório"}
            
            tools.append(DepartmentSearchAdapter(department_search))
            print(f"[DEBUG] Department Search Tool carregada: department_search_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar department_search_tool: {e}")
        
        # Ferramenta de bestsellers
        try:
            from tools.ishopmeta_bestseller import BestSellerTool
            bestseller = BestSellerTool()
            # Adapter para usar como tool tradicional
            class BestsellerAdapter:
                def __init__(self, bestseller):
                    self.bestseller = bestseller
                    self.name = "bestseller_tool"
                    self.description = "Ferramenta para buscar produtos mais vendidos da plataforma"
                
                def execute(self, query: str = "", limit: int = 20, **kwargs):
                    return self.bestseller.execute(query, limit=limit, **kwargs)
            
            tools.append(BestsellerAdapter(bestseller))
            print(f"[DEBUG] Bestseller Tool carregada: bestseller_tool")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar bestseller_tool: {e}")
        
        print(f"[DEBUG] {len(tools)} tools tradicionais carregadas com sucesso")
        
        # Importa tools MCP do servidor (se disponível)
        try:
            from mcp_files.server.mcp_tools_server import get_mcp_tools_functions
            mcp_tools = get_mcp_tools_functions()
            print(f"[DEBUG] {len(mcp_tools)} tools MCP disponíveis")
        except ImportError as e:
            print(f"[WARNING] Tools MCP não disponíveis: {e}")
        except Exception as e:
            print(f"[WARNING] Erro ao carregar tools MCP: {e}")
        
        print(f"[DEBUG] Total de {len(tools)} tools carregadas com sucesso")
        return tools
        
    except Exception as e:
        print(f"[ERROR] Erro ao carregar tools: {e}")
        import traceback
        traceback.print_exc()
        return []

def get_mcp_tools() -> List[Callable]:
    """
    Carrega especificamente as tools MCP
    
    Returns:
        List[Callable]: Lista de funções de tools MCP
    """
    try:
        from mcp_files.server.mcp_tools_server import get_mcp_tools_functions
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
        from mcp_files.server.mcp_tools_server import get_mcp_tools_names
        return get_mcp_tools_names()
    except Exception as e:
        print(f"[ERROR] Erro ao listar tools MCP: {e}")
        return []

def get_tool_info() -> List[dict]:
    """
    Retorna informações detalhadas sobre todas as tools carregadas
    
    Returns:
        List[dict]: Lista com informações das tools
    """
    tools = get_all_tools()
    tool_info = []
    
    for tool in tools:
        info = {
            'name': tool.name if hasattr(tool, 'name') else tool.__name__,
            'description': tool.description if hasattr(tool, 'description') else 'Sem descrição',
            'type': 'Traditional Tool',
            'class': tool.__class__.__name__ if hasattr(tool, '__class__') else 'Function'
        }
        tool_info.append(info)
    
    return tool_info
