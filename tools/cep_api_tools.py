"""
Brazilian CEP API Tools - Ferramentas para consulta de CEP brasileiro
Módulo com tool especializada em consultar múltiplas APIs de CEP para obter dados completos.
"""

import requests
from typing import Dict, Any, Optional
from mcp_files.core.mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator


class ConsultaEnderecoPorCEP(MCPToolBase):
    """
    Tool para consultar informações completas de CEP brasileiro.
    Consulta 2 APIs diferentes para obter dados oficiais + coordenadas geográficas.
    """
    
    def __init__(self):
        super().__init__(
            name="consulta_endereco_por_cep",
            description="Consulta endereço completo por CEP brasileiro usando múltiplas APIs (ViaCEP + CEP Aberto)"
        )
        self.apis = {
            "viacep": "https://viacep.com.br/ws",
            "cepaberto": "https://www.cepaberto.com/api/v3/cep"
        }
        self.timeout = 8
        self.headers = {
            "User-Agent": "MCP-Tools-LangChain/1.0",
            "Accept": "application/json"
        }
    
    def validate_input(self, cep: str, usar_multiplas_apis: bool = True) -> bool:
        """
        Valida formato do CEP brasileiro.
        
        Args:
            cep: CEP para consulta
            usar_multiplas_apis: Se deve usar múltiplas APIs
            
        Returns:
            bool: True se CEP é válido
        """
        if not MCPToolValidator.validate_text(cep, "cep"):
            return False
        
        # Remove formatação e valida
        cep_limpo = cep.replace("-", "").replace(".", "").replace(" ", "")
        
        # Deve ter exatamente 8 dígitos
        if not (len(cep_limpo) == 8 and cep_limpo.isdigit()):
            return False
        
        return True
    
    def execute(self, cep: str, usar_multiplas_apis: bool = True) -> Dict[str, Any]:
        """
        Consulta CEP em múltiplas APIs para obter informações completas.
        
        Args:
            cep: CEP brasileiro (com ou sem formatação)
            usar_multiplas_apis: Se deve consultar múltiplas APIs
            
        Returns:
            Dict com informações combinadas das APIs
        """
        try:
            # Limpar e formatar CEP
            cep_limpo = cep.replace("-", "").replace(".", "").replace(" ", "")
            cep_formatado = f"{cep_limpo[:5]}-{cep_limpo[5:]}"
            
            resultados_apis = {}
            
            # API 1: ViaCEP (sempre consulta - dados oficiais dos Correios)
            resultado_viacep = self._consultar_viacep(cep_limpo)
            if resultado_viacep:
                resultados_apis["viacep"] = resultado_viacep
            
            # API 2: CEP Aberto (se solicitado e ViaCEP funcionou)
            if usar_multiplas_apis and resultado_viacep:
                resultado_cepaberto = self._consultar_cepaberto(cep_limpo)
                if resultado_cepaberto:
                    resultados_apis["cepaberto"] = resultado_cepaberto
            
            if not resultados_apis:
                raise ValueError(f"CEP {cep_formatado} não encontrado em nenhuma API")
            
            # Combinar resultados
            dados_combinados = self._combinar_dados_cep(resultados_apis, cep_formatado)
            
            return (MCPResponseBuilder("consulta_endereco_por_cep")
                    .add_input_info(
                        cep_original=cep,
                        cep_formatado=cep_formatado,
                        apis_utilizadas=list(resultados_apis.keys())
                    )
                    .add_result(
                        endereco=dados_combinados,
                        total_apis_consultadas=len(resultados_apis),
                        apis_responderam=list(resultados_apis.keys())
                    )
                    .add_summary(f"CEP {cep_formatado} encontrado: {dados_combinados.get('endereco_completo', 'N/A')}")
                    .build())
                    
        except requests.RequestException as e:
            raise RuntimeError(f"Erro na consulta às APIs de CEP: {e}")
        except Exception as e:
            raise ValueError(f"Erro no processamento do CEP: {e}")
    
    def _consultar_viacep(self, cep: str) -> Optional[Dict[str, Any]]:
        """
        Consulta API 1: ViaCEP (dados oficiais dos Correios).
        
        Args:
            cep: CEP limpo (8 dígitos)
            
        Returns:
            Dict com dados do ViaCEP
        """
        try:
            url = f"{self.apis['viacep']}/{cep}/json/"
            self.logger.info(f"Consultando ViaCEP: {url}")
            
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                # ViaCEP retorna erro quando CEP não existe
                if data.get("erro"):
                    return None
                
                return {
                    "fonte": "ViaCEP",
                    "cep": data.get("cep", ""),
                    "logradouro": data.get("logradouro", ""),
                    "complemento": data.get("complemento", ""),
                    "bairro": data.get("bairro", ""),
                    "cidade": data.get("localidade", ""),
                    "uf": data.get("uf", ""),
                    "ibge": data.get("ibge", ""),
                    "gia": data.get("gia", ""),
                    "ddd": data.get("ddd", ""),
                    "siafi": data.get("siafi", "")
                }
                
        except requests.RequestException as e:
            self.logger.warning(f"Erro no ViaCEP: {e}")
        
        return None
    
    def _consultar_cepaberto(self, cep: str) -> Optional[Dict[str, Any]]:
        """
        Consulta API 2: CEP Aberto (coordenadas geográficas extras).
        
        Args:
            cep: CEP limpo (8 dígitos)
            
        Returns:
            Dict com dados do CEP Aberto
        """
        try:
            url = f"{self.apis['cepaberto']}?cep={cep}"
            self.logger.info(f"Consultando CEP Aberto: {url}")
            
            # CEP Aberto pode precisar de token, mas tem endpoint público limitado
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            
            if response.status_code == 200:
                data = response.json()
                
                return {
                    "fonte": "CEP Aberto",
                    "cep": data.get("cep", ""),
                    "logradouro": data.get("address", ""),
                    "bairro": data.get("district", ""),
                    "cidade": data.get("city", {}).get("name", "") if data.get("city") else "",
                    "uf": data.get("state", {}).get("code", "") if data.get("state") else "",
                    "latitude": data.get("latitude", ""),
                    "longitude": data.get("longitude", ""),
                    "altitude": data.get("altitude", "")
                }
                
        except requests.RequestException as e:
            self.logger.warning(f"Erro no CEP Aberto: {e}")
        
        return None
    
    def _combinar_dados_cep(self, resultados_apis: Dict[str, Dict], 
                           cep_formatado: str) -> Dict[str, Any]:
        """
        Combina dados das diferentes APIs de CEP.
        
        Args:
            resultados_apis: Dados de diferentes APIs
            cep_formatado: CEP formatado
            
        Returns:
            Dict com dados combinados
        """
        # Usar ViaCEP como base (mais confiável para dados brasileiros)
        dados_base = resultados_apis.get("viacep", {})
        dados_extras = resultados_apis.get("cepaberto", {})
        
        combinado = {
            "cep": cep_formatado,
            "logradouro": dados_base.get("logradouro", ""),
            "complemento": dados_base.get("complemento", ""),
            "bairro": dados_base.get("bairro", ""),
            "cidade": dados_base.get("cidade", ""),
            "uf": dados_base.get("uf", ""),
            "ddd": dados_base.get("ddd", ""),
            "endereco_completo": "",
            "coordenadas": {},
            "codigos_oficiais": {},
            "apis_consultadas": list(resultados_apis.keys())
        }
        
        # Montar endereço completo
        partes_endereco = [
            combinado["logradouro"],
            combinado["bairro"],
            combinado["cidade"],
            combinado["uf"]
        ]
        combinado["endereco_completo"] = ", ".join([p for p in partes_endereco if p])
        
        # Adicionar coordenadas se disponíveis
        if dados_extras.get("latitude") and dados_extras.get("longitude"):
            combinado["coordenadas"] = {
                "latitude": dados_extras["latitude"],
                "longitude": dados_extras["longitude"],
                "altitude": dados_extras.get("altitude", "")
            }
        
        # Códigos oficiais
        if dados_base.get("ibge"):
            combinado["codigos_oficiais"]["ibge"] = dados_base["ibge"]
        if dados_base.get("siafi"):
            combinado["codigos_oficiais"]["siafi"] = dados_base["siafi"]
        
        return combinado