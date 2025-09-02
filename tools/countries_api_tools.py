"""
Countries API Tools - Ferramentas para consulta de informações de países
Módulo com tool especializada em consultar APIs de países com múltiplas rotas.
"""

import requests
from typing import Dict, Any, Optional
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator


class ConsultaInformacoesPais(MCPToolBase):
    """
    Tool para consultar informações completas sobre países usando REST Countries API.
    Consulta 2 rotas diferentes da mesma API para obter dados básicos e econômicos.
    """
    
    def __init__(self):
        super().__init__(
            name="consulta_informacoes_pais",
            description="Consulta informações detalhadas de países (dados básicos + econômicos) usando REST Countries API"
        )
        self.base_url = "https://restcountries.com/v3.1"
        self.timeout = 10
        self.headers = {
            "User-Agent": "MCP-Tools-LangChain/1.0",
            "Accept": "application/json"
        }
    
    def validate_input(self, nome_pais: str, incluir_dados_economicos: bool = True) -> bool:
        """
        Valida os parâmetros de entrada.
        
        Args:
            nome_pais: Nome do país para consulta
            incluir_dados_economicos: Se deve incluir dados econômicos
            
        Returns:
            bool: True se válido
        """
        if not MCPToolValidator.validate_text(nome_pais, "nome_pais"):
            return False
        
        # Validação adicional - nome deve ter pelo menos 2 caracteres
        if len(nome_pais.strip()) < 2:
            return False
        
        return True
    
    def execute(self, nome_pais: str, incluir_dados_economicos: bool = True) -> Dict[str, Any]:
        """
        Consulta informações do país em duas rotas diferentes da mesma API.
        
        Args:
            nome_pais: Nome do país (português, inglês ou código)
            incluir_dados_economicos: Se deve buscar dados econômicos adicionais
            
        Returns:
            Dict com informações combinadas das duas rotas
        """
        try:
            # Rota 1: Dados básicos do país
            dados_basicos = self._consultar_dados_basicos(nome_pais)
            
            if not dados_basicos:
                raise ValueError(f"País '{nome_pais}' não encontrado")
            
            # Rota 2: Dados econômicos (se solicitado)
            dados_economicos = None
            if incluir_dados_economicos:
                codigo_pais = dados_basicos.get("cca2", "")
                if codigo_pais:
                    dados_economicos = self._consultar_dados_economicos(codigo_pais)
            
            # Combinar informações
            resultado_combinado = self._combinar_dados(dados_basicos, dados_economicos)
            
            return (MCPResponseBuilder("consulta_informacoes_pais")
                    .add_input_info(
                        pais_consultado=nome_pais,
                        incluiu_dados_economicos=incluir_dados_economicos,
                        codigo_pais=dados_basicos.get("cca2", "N/A")
                    )
                    .add_result(
                        dados_pais=resultado_combinado,
                        rotas_consultadas=2 if incluir_dados_economicos else 1,
                        api_utilizada="REST Countries v3.1"
                    )
                    .add_summary(f"Informações de {resultado_combinado.get('nome_oficial', nome_pais)} coletadas com sucesso")
                    .build())
                    
        except requests.RequestException as e:
            raise RuntimeError(f"Erro na requisição à API: {e}")
        except Exception as e:
            raise ValueError(f"Erro no processamento dos dados: {e}")
    
    def _consultar_dados_basicos(self, nome_pais: str) -> Optional[Dict[str, Any]]:
        """
        Consulta rota 1: dados básicos do país.
        
        Args:
            nome_pais: Nome do país
            
        Returns:
            Dict com dados básicos ou None se não encontrado
        """
        # Tenta diferentes endpoints para maior flexibilidade
        endpoints = [
            f"/name/{nome_pais}",
            f"/alpha/{nome_pais}",  # Para códigos de país
        ]
        
        for endpoint in endpoints:
            try:
                url = f"{self.base_url}{endpoint}"
                self.logger.info(f"Consultando dados básicos: {url}")
                
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    params={"fullText": "true"}  # Busca exata
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data and len(data) > 0:
                        return self._processar_dados_basicos(data[0])
                        
            except requests.RequestException as e:
                self.logger.warning(f"Falha no endpoint {endpoint}: {e}")
                continue
        
        return None
    
    def _consultar_dados_economicos(self, codigo_pais: str) -> Optional[Dict[str, Any]]:
        """
        Consulta rota 2: dados econômicos via código do país.
        
        Args:
            codigo_pais: Código ISO do país (ex: BR, US, GB)
            
        Returns:
            Dict com dados econômicos ou None se não encontrado
        """
        try:
            # Endpoint específico para dados econômicos
            url = f"{self.base_url}/alpha/{codigo_pais}"
            params = {
                "fields": "currencies,gini,gdp,economy,trade"  # Campos econômicos específicos
            }
            
            self.logger.info(f"Consultando dados econômicos: {url}")
            
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                if data and len(data) > 0:
                    return self._processar_dados_economicos(data[0])
                    
        except requests.RequestException as e:
            self.logger.warning(f"Erro ao buscar dados econômicos: {e}")
        
        return None
    
    def _processar_dados_basicos(self, dados_raw: Dict) -> Dict[str, Any]:
        """
        Processa e filtra dados básicos da rota 1.
        
        Args:
            dados_raw: Dados brutos da API
            
        Returns:
            Dict com dados processados
        """
        # Extrair informações essenciais
        processed = {
            "nome_comum": dados_raw.get("name", {}).get("common", "N/A"),
            "nome_oficial": dados_raw.get("name", {}).get("official", "N/A"),
            "codigo_iso2": dados_raw.get("cca2", "N/A"),
            "codigo_iso3": dados_raw.get("cca3", "N/A"),
            "capital": dados_raw.get("capital", ["N/A"])[0] if dados_raw.get("capital") else "N/A",
            "regiao": dados_raw.get("region", "N/A"),
            "sub_regiao": dados_raw.get("subregion", "N/A"),
            "populacao": dados_raw.get("population", 0),
            "area_km2": dados_raw.get("area", 0),
            "idiomas": list(dados_raw.get("languages", {}).values()),
            "fuso_horario": dados_raw.get("timezones", ["N/A"])[0] if dados_raw.get("timezones") else "N/A",
            "codigo_telefone": dados_raw.get("idd", {}).get("root", "") + 
                             (dados_raw.get("idd", {}).get("suffixes", [""])[0] if dados_raw.get("idd", {}).get("suffixes") else ""),
            "independente": dados_raw.get("independent", False),
            "membro_onu": dados_raw.get("unMember", False),
            "bandeira": dados_raw.get("flags", {}).get("png", ""),
            "mapa": dados_raw.get("maps", {}).get("googleMaps", "")
        }
        
        # Adicionar densidade populacional
        if processed["populacao"] > 0 and processed["area_km2"] > 0:
            processed["densidade_populacional"] = round(processed["populacao"] / processed["area_km2"], 2)
        else:
            processed["densidade_populacional"] = 0
        
        return processed
    
    def _processar_dados_economicos(self, dados_raw: Dict) -> Dict[str, Any]:
        """
        Processa dados econômicos da rota 2.
        
        Args:
            dados_raw: Dados brutos da API
            
        Returns:
            Dict com dados econômicos processados
        """
        processed = {
            "moedas": {},
            "indicadores_economicos": {}
        }
        
        # Processar moedas
        currencies = dados_raw.get("currencies", {})
        for code, currency_info in currencies.items():
            processed["moedas"][code] = {
                "nome": currency_info.get("name", "N/A"),
                "simbolo": currency_info.get("symbol", "N/A")
            }
        
        # Processar indicadores econômicos (quando disponíveis)
        gini = dados_raw.get("gini", {})
        if gini:
            # Pega o índice GINI mais recente
            latest_year = max(gini.keys()) if gini.keys() else None
            if latest_year:
                processed["indicadores_economicos"]["gini"] = {
                    "valor": gini[latest_year],
                    "ano": latest_year,
                    "descricao": "Índice GINI (desigualdade de renda)"
                }
        
        # Adicionar informações extras se disponíveis
        if dados_raw.get("gdp"):
            processed["indicadores_economicos"]["pib"] = dados_raw["gdp"]
        
        return processed
    
    def _combinar_dados(self, dados_basicos: Dict[str, Any], 
                       dados_economicos: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Combina dados das duas rotas em uma estrutura unificada.
        
        Args:
            dados_basicos: Dados da rota 1
            dados_economicos: Dados da rota 2 (opcional)
            
        Returns:
            Dict com dados combinados
        """
        resultado = {
            "informacoes_basicas": dados_basicos,
            "informacoes_economicas": dados_economicos if dados_economicos else {},
            "resumo_executivo": self._gerar_resumo_executivo(dados_basicos, dados_economicos)
        }
        
        return resultado
    
    def _gerar_resumo_executivo(self, dados_basicos: Dict, 
                               dados_economicos: Optional[Dict]) -> Dict[str, Any]:
        """
        Gera resumo executivo com informações principais.
        
        Args:
            dados_basicos: Dados básicos do país
            dados_economicos: Dados econômicos (opcional)
            
        Returns:
            Dict com resumo executivo
        """
        resumo = {
            "pais": dados_basicos.get("nome_oficial", "N/A"),
            "codigo": dados_basicos.get("codigo_iso2", "N/A"),
            "capital": dados_basicos.get("capital", "N/A"),
            "populacao_milhoes": round(dados_basicos.get("populacao", 0) / 1_000_000, 2),
            "area_mil_km2": round(dados_basicos.get("area_km2", 0) / 1_000, 2),
            "densidade_hab_km2": dados_basicos.get("densidade_populacional", 0),
            "regiao": f"{dados_basicos.get('regiao', 'N/A')} - {dados_basicos.get('sub_regiao', 'N/A')}",
            "idiomas_principais": dados_basicos.get("idiomas", [])[:3],  # Máximo 3 idiomas
            "independente": dados_basicos.get("independente", False),
            "membro_onu": dados_basicos.get("membro_onu", False)
        }
        
        # Adicionar dados econômicos se disponíveis
        if dados_economicos and dados_economicos.get("moedas"):
            moedas = list(dados_economicos["moedas"].keys())
            resumo["moedas"] = moedas[:2]  # Máximo 2 moedas
        
        if dados_economicos and dados_economicos.get("indicadores_economicos", {}).get("gini"):
            gini_info = dados_economicos["indicadores_economicos"]["gini"]
            resumo["desigualdade_gini"] = f"{gini_info['valor']} ({gini_info['ano']})"
        
        return resumo
