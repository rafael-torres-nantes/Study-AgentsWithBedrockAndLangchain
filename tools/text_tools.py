"""
Text Analysis Tools - Ferramentas de análise de texto
Módulo com tools especializadas em análise e processamento de texto.
"""

import re
from typing import Dict, Any
from mcp_files.core.mcp_base import MCPToolBase, MCPResponseBuilder, MCPToolValidator


class ContadorCaracteres(MCPToolBase):
    """
    Tool para contar occurrências de caracteres específicos em texto.
    """
    
    def __init__(self):
        super().__init__(
            name="contador_caracteres",
            description="Conta quantas vezes um caracter específico aparece em um texto"
        )
    
    def validate_input(self, texto: str, caracter: str) -> bool:
        """Valida se texto e caracter foram fornecidos."""
        return (
            MCPToolValidator.validate_text(texto, "texto") and
            MCPToolValidator.validate_text(caracter, "caracter")
        )
    
    def execute(self, texto: str, caracter: str) -> Dict[str, Any]:
        """
        Conta occurrências do caracter no texto.
        
        Args:
            texto: Texto onde buscar
            caracter: Caracter a ser contado
            
        Returns:
            Dict com resultados da contagem
        """
        # Conta occurrências (case sensitive e insensitive)
        count_exact = texto.count(caracter)
        count_upper = texto.count(caracter.upper()) 
        count_lower = texto.count(caracter.lower())
        total_case_insensitive = count_upper + count_lower
        
        return (MCPResponseBuilder("contagem_caracteres")
                .add_input_info(palavra_analisada=texto, caracter_procurado=caracter)
                .add_result(resultados={
                    "exato": count_exact,
                    "maiusculo": count_upper,
                    "minusculo": count_lower,
                    "total_case_insensitive": total_case_insensitive
                })
                .add_summary(f"O caractere '{caracter}' aparece {count_exact} vez(es) de forma exata no texto '{texto}'")
                .build())


class AnalisadorTexto(MCPToolBase):
    """
    Tool para análise de texto com diferentes tipos de operações.
    """
    
    def __init__(self):
        super().__init__(
            name="analisar_texto",
            description="Analisa um texto com diferentes tipos de operações"
        )
        self.tipos_validos = [
            "contar_palavras", "maiuscula", "maiúscula", 
            "minuscula", "minúscula", "converter_minusculas", "caracteres_total"
        ]
    
    def validate_input(self, texto: str, tipo_analise: str = "contar_palavras") -> bool:
        """Valida texto e tipo de análise."""
        return (
            MCPToolValidator.validate_text(texto, "texto") and
            tipo_analise in self.tipos_validos
        )
    
    def execute(self, texto: str, tipo_analise: str = "contar_palavras") -> Dict[str, Any]:
        """
        Executa análise do texto baseada no tipo especificado.
        
        Args:
            texto: Texto a ser analisado
            tipo_analise: Tipo de análise a ser realizada
            
        Returns:
            Dict com resultado da análise
        """
        if tipo_analise == "contar_palavras":
            return self._contar_palavras(texto)
        elif tipo_analise in ["maiuscula", "maiúscula"]:
            return self._converter_maiuscula(texto)
        elif tipo_analise in ["minuscula", "minúscula", "converter_minusculas"]:
            return self._converter_minuscula(texto)
        elif tipo_analise == "caracteres_total":
            return self._contar_caracteres_total(texto)
        else:
            raise ValueError(f"Tipo de análise '{tipo_analise}' não suportado")
    
    def _contar_palavras(self, texto: str) -> Dict[str, Any]:
        """Conta número de palavras no texto."""
        palavras = len(texto.split())
        return (MCPResponseBuilder("contagem_palavras")
                .add_input_info(texto_analisado=texto)
                .add_result(total_palavras=palavras)
                .add_summary(f"O texto '{texto}' tem {palavras} palavra(s)")
                .build())
    
    def _converter_maiuscula(self, texto: str) -> Dict[str, Any]:
        """Converte texto para maiúscula."""
        return (MCPResponseBuilder("conversao_maiuscula")
                .add_input_info(texto_original=texto)
                .add_result(texto_convertido=texto.upper())
                .add_summary("Texto convertido para maiúscula")
                .build())
    
    def _converter_minuscula(self, texto: str) -> Dict[str, Any]:
        """Converte texto para minúscula."""
        return (MCPResponseBuilder("conversao_minuscula")
                .add_input_info(texto_original=texto)
                .add_result(texto_convertido=texto.lower())
                .add_summary("Texto convertido para minúscula")
                .build())
    
    def _contar_caracteres_total(self, texto: str) -> Dict[str, Any]:
        """Conta caracteres totais no texto."""
        total_chars = len(texto)
        chars_sem_espaco = len(texto.replace(" ", ""))
        espacos = total_chars - chars_sem_espaco
        
        return (MCPResponseBuilder("contagem_caracteres_total")
                .add_input_info(texto_analisado=texto)
                .add_result(
                    total_caracteres=total_chars,
                    caracteres_sem_espaco=chars_sem_espaco,
                    espacos=espacos
                )
                .add_summary(f"O texto tem {total_chars} caracteres total ({chars_sem_espaco} sem espaços)")
                .build())


class AnalisadorSentimento(MCPToolBase):
    """
    Tool para análise básica de sentimento em texto.
    """
    
    def __init__(self):
        super().__init__(
            name="analisar_sentimento",
            description="Analisa o sentimento básico de um texto"
        )
        self.palavras_positivas = [
            'bom', 'ótimo', 'excelente', 'maravilhoso', 'feliz', 
            'alegre', 'amor', 'sucesso', 'positivo'
        ]
        self.palavras_negativas = [
            'ruim', 'péssimo', 'terrível', 'horrível', 'triste', 
            'raiva', 'ódio', 'fracasso', 'negativo'
        ]
    
    def validate_input(self, texto: str) -> bool:
        """Valida se o texto foi fornecido."""
        return MCPToolValidator.validate_text(texto, "texto")
    
    def execute(self, texto: str) -> Dict[str, Any]:
        """
        Analisa sentimento do texto baseado em palavras-chave.
        
        Args:
            texto: Texto a ser analisado
            
        Returns:
            Dict com análise de sentimento
        """
        texto_lower = texto.lower()
        score_positivo = sum(1 for palavra in self.palavras_positivas if palavra in texto_lower)
        score_negativo = sum(1 for palavra in self.palavras_negativas if palavra in texto_lower)
        
        if score_positivo > score_negativo:
            sentimento = "positivo"
        elif score_negativo > score_positivo:
            sentimento = "negativo"
        else:
            sentimento = "neutro"
        
        return (MCPResponseBuilder("analise_sentimento")
                .add_input_info(texto_analisado=texto)
                .add_result(
                    sentimento=sentimento,
                    score_positivo=score_positivo,
                    score_negativo=score_negativo
                )
                .add_summary(f"O texto tem sentimento {sentimento} (positivo: {score_positivo}, negativo: {score_negativo})")
                .build())


class ExtratorEmail(MCPToolBase):
    """
    Tool para extrair endereços de email de texto.
    """
    
    def __init__(self):
        super().__init__(
            name="extrair_emails",
            description="Extrai endereços de email de um texto"
        )
        self.email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    
    def validate_input(self, texto: str) -> bool:
        """Valida se o texto foi fornecido."""
        return MCPToolValidator.validate_text(texto, "texto")
    
    def execute(self, texto: str) -> Dict[str, Any]:
        """
        Extrai emails do texto usando regex.
        
        Args:
            texto: Texto onde buscar emails
            
        Returns:
            Dict com emails encontrados
        """
        emails = re.findall(self.email_pattern, texto)
        
        return (MCPResponseBuilder("extracao_emails")
                .add_input_info(texto_analisado=texto)
                .add_result(
                    emails_encontrados=emails,
                    total_emails=len(emails)
                )
                .add_summary(f"Foram encontrados {len(emails)} email(s) no texto")
                .build())
