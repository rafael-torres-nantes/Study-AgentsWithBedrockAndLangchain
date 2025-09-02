"""
MCP Tools - Base Classes and Utilities
Módulo com classes base e utilitários para tools MCP.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

# Configuração do logger
logger = logging.getLogger(__name__)


class MCPToolBase(ABC):
    """
    Classe base abstrata para todas as MCP tools.
    Define interface comum e funcionalidades compartilhadas.
    """
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.logger = logging.getLogger(f"mcp_tool.{name}")
    
    @abstractmethod
    def execute(self, *args, **kwargs) -> Dict[str, Any]:
        """
        Executa a funcionalidade principal da tool.
        Deve ser implementado por cada tool específica.
        
        Returns:
            Dict[str, Any]: Resultado da execução
        """
        pass
    
    def validate_input(self, **kwargs) -> bool:
        """
        Valida os parâmetros de entrada.
        Pode ser sobrescrito por tools específicas.
        
        Returns:
            bool: True se válido, False caso contrário
        """
        return True
    
    def format_response(self, result: Dict[str, Any]) -> str:
        """
        Formata a resposta no padrão JSON MCP.
        
        Args:
            result: Dicionário com resultado da execução
            
        Returns:
            str: JSON formatado
        """
        try:
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"Erro ao formatar resposta: {e}")
            return json.dumps({
                "erro": "Erro na formatação da resposta",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def handle_error(self, error: Exception, context: Optional[Dict] = None) -> str:
        """
        Trata erros de forma padronizada.
        
        Args:
            error: Exceção capturada
            context: Contexto adicional do erro
            
        Returns:
            str: JSON com informações do erro
        """
        self.logger.error(f"Erro na tool {self.name}: {error}")
        
        error_response = {
            "erro": f"Erro na execução da tool {self.name}",
            "detalhes": str(error),
            "tool": self.name
        }
        
        if context:
            error_response.update(context)
        
        return self.format_response(error_response)
    
    def __call__(self, *args, **kwargs) -> str:
        """
        Permite que a tool seja chamada diretamente.
        Implementa o fluxo completo: validação → execução → formatação.
        """
        try:
            # Validação de entrada
            if not self.validate_input(*args, **kwargs):
                return self.handle_error(
                    ValueError("Parâmetros de entrada inválidos"),
                    {"parametros_recebidos": {"args": args, "kwargs": kwargs}}
                )
            
            # Execução da tool
            result = self.execute(*args, **kwargs)
            
            # Formatação da resposta
            return self.format_response(result)
            
        except Exception as e:
            return self.handle_error(e, {"parametros": {"args": args, "kwargs": kwargs}})


class MCPResponseBuilder:
    """
    Builder para construir respostas padronizadas das MCP tools.
    """
    
    def __init__(self, response_type: str):
        self.response = {
            "tipo_resposta": response_type
        }
    
    def add_input_info(self, **kwargs) -> 'MCPResponseBuilder':
        """Adiciona informações sobre a entrada processada."""
        for key, value in kwargs.items():
            self.response[f"{key}"] = value
        return self
    
    def add_result(self, **kwargs) -> 'MCPResponseBuilder':
        """Adiciona resultados da operação."""
        for key, value in kwargs.items():
            self.response[key] = value
        return self
    
    def add_summary(self, summary: str) -> 'MCPResponseBuilder':
        """Adiciona resumo da operação."""
        self.response["resumo"] = summary
        return self
    
    def build(self) -> Dict[str, Any]:
        """Constrói o dicionário final da resposta."""
        return self.response


class MCPToolValidator:
    """
    Validador centralizado para parâmetros das MCP tools.
    """
    
    @staticmethod
    def validate_text(text: str, field_name: str = "texto") -> bool:
        """Valida se o texto não está vazio."""
        return bool(text and text.strip())
    
    @staticmethod
    def validate_number(value: Any, field_name: str = "número") -> bool:
        """Valida se o valor é um número válido."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_operation(operation: str, valid_operations: list) -> bool:
        """Valida se a operação está na lista de operações válidas."""
        return operation in valid_operations
    
    @staticmethod
    def validate_algorithm(algorithm: str, valid_algorithms: list) -> bool:
        """Valida se o algoritmo está na lista de algoritmos válidos."""
        return algorithm in valid_algorithms
