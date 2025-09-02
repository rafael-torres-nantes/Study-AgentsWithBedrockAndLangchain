"""
Utility Tools - Ferramentas utilitárias
Módulo com tools para cálculos, hash e outras utilidades.
"""

import hashlib
from typing import Dict, Any
from .mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator


class CalculadoraBasica(MCPToolBase):
    """
    Tool para operações matemáticas básicas.
    """
    
    def __init__(self):
        super().__init__(
            name="calculadora_basica",
            description="Realiza operações matemáticas básicas"
        )
        self.operacoes_validas = ["+", "-", "*", "/"]
    
    def validate_input(self, operacao: str, numero1: float, numero2: float) -> bool:
        """Valida operação e números."""
        return (
            MCPToolValidator.validate_operation(operacao, self.operacoes_validas) and
            MCPToolValidator.validate_number(numero1, "numero1") and
            MCPToolValidator.validate_number(numero2, "numero2")
        )
    
    def execute(self, operacao: str, numero1: float, numero2: float) -> Dict[str, Any]:
        """
        Executa operação matemática.
        
        Args:
            operacao: Tipo de operação (+, -, *, /)
            numero1: Primeiro número
            numero2: Segundo número
            
        Returns:
            Dict com resultado do cálculo
        """
        # Validação especial para divisão por zero
        if operacao == "/" and numero2 == 0:
            raise ValueError("Divisão por zero não é permitida")
        
        # Executa operação
        if operacao == "+":
            resultado = numero1 + numero2
        elif operacao == "-":
            resultado = numero1 - numero2
        elif operacao == "*":
            resultado = numero1 * numero2
        elif operacao == "/":
            resultado = numero1 / numero2
        else:
            raise ValueError(f"Operação '{operacao}' não suportada")
        
        return (MCPResponseBuilder("calculo_matematico")
                .add_input_info(operacao=operacao, numero1=numero1, numero2=numero2)
                .add_result(resultado=resultado)
                .add_summary(f"{numero1} {operacao} {numero2} = {resultado}")
                .build())


class GeradorHash(MCPToolBase):
    """
    Tool para gerar hash de texto usando diferentes algoritmos.
    """
    
    def __init__(self):
        super().__init__(
            name="gerar_hash",
            description="Gera hash de um texto usando diferentes algoritmos"
        )
        self.algoritmos_validos = ["md5", "sha1", "sha256"]
    
    def validate_input(self, texto: str, algoritmo: str = "md5") -> bool:
        """Valida texto e algoritmo."""
        return (
            MCPToolValidator.validate_text(texto, "texto") and
            MCPToolValidator.validate_algorithm(algoritmo, self.algoritmos_validos)
        )
    
    def execute(self, texto: str, algoritmo: str = "md5") -> Dict[str, Any]:
        """
        Gera hash do texto usando algoritmo especificado.
        
        Args:
            texto: Texto para gerar hash
            algoritmo: Algoritmo de hash (md5, sha1, sha256)
            
        Returns:
            Dict com hash gerado
        """
        # Gera hash baseado no algoritmo
        if algoritmo == "md5":
            hash_result = hashlib.md5(texto.encode()).hexdigest()
        elif algoritmo == "sha1":
            hash_result = hashlib.sha1(texto.encode()).hexdigest()
        elif algoritmo == "sha256":
            hash_result = hashlib.sha256(texto.encode()).hexdigest()
        else:
            raise ValueError(f"Algoritmo '{algoritmo}' não suportado")
        
        return (MCPResponseBuilder("geracao_hash")
                .add_input_info(texto_original=texto, algoritmo=algoritmo)
                .add_result(hash=hash_result)
                .add_summary(f"Hash {algoritmo.upper()} gerado com sucesso")
                .build())
