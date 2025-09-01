"""
Tool para análise de texto - contagem de caracteres, palavras, etc.
"""
from langchain_core.tools import tool
import re
import json

@tool
def contador_caracteres(texto: str, caracter: str) -> str:
    """
    Conta quantas vezes um caracter específico aparece em um texto.
    
    Args:
        texto: O texto onde buscar
        caracter: O caracter a ser contado
    
    Returns:
        str: Resultado formatado em JSON com a contagem
    """
    try:
        if not texto or not caracter:
            return json.dumps({
                "erro": "Texto e caracter são obrigatórios",
                "texto_recebido": texto,
                "caracter_recebido": caracter
            }, ensure_ascii=False, indent=2)
        
        # Conta occurrências (case sensitive e insensitive)
        count_exact = texto.count(caracter)
        count_upper = texto.count(caracter.upper()) 
        count_lower = texto.count(caracter.lower())
        total_case_insensitive = count_upper + count_lower
        
        resultado = {
            "tipo_resposta": "contagem_caracteres",
            "palavra_analisada": texto,
            "caracter_procurado": caracter,
            "resultados": {
                "exato": count_exact,
                "maiusculo": count_upper,
                "minusculo": count_lower,
                "total_case_insensitive": total_case_insensitive
            },
            "resumo": f"O caractere '{caracter}' aparece {count_exact} vez(es) de forma exata no texto '{texto}'"
        }
        
        return json.dumps(resultado, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "erro": "Erro ao processar contagem",
            "detalhes": str(e),
            "texto_recebido": texto,
            "caracter_recebido": caracter
        }, ensure_ascii=False, indent=2)

@tool
def analisar_texto(texto: str, tipo_analise: str = "contar_palavras") -> str:
    """
    Analisa um texto fornecido de acordo com o tipo especificado.
    
    Args:
        texto: O texto a ser analisado
        tipo_analise: Tipo de análise ('contar_palavras', 'maiuscula', 'minuscula', 'caracteres_total')
    
    Returns:
        str: Resultado da análise em JSON
    """
    try:
        if not texto:
            return json.dumps({
                "erro": "Texto não fornecido"
            }, ensure_ascii=False, indent=2)
        
        if tipo_analise == "contar_palavras":
            palavras = len(texto.split())
            resultado = {
                "tipo_resposta": "contagem_palavras",
                "texto_analisado": texto,
                "total_palavras": palavras,
                "resumo": f"O texto '{texto}' tem {palavras} palavra(s)"
            }
            
        elif tipo_analise == "maiuscula":
            resultado = {
                "tipo_resposta": "conversao_maiuscula",
                "texto_original": texto,
                "texto_convertido": texto.upper(),
                "resumo": f"Texto convertido para maiúscula"
            }
            
        elif tipo_analise == "minuscula":
            resultado = {
                "tipo_resposta": "conversao_minuscula", 
                "texto_original": texto,
                "texto_convertido": texto.lower(),
                "resumo": f"Texto convertido para minúscula"
            }
            
        elif tipo_analise == "caracteres_total":
            total_chars = len(texto)
            chars_sem_espaco = len(texto.replace(" ", ""))
            resultado = {
                "tipo_resposta": "contagem_caracteres_total",
                "texto_analisado": texto,
                "total_caracteres": total_chars,
                "caracteres_sem_espaco": chars_sem_espaco,
                "espacos": total_chars - chars_sem_espaco,
                "resumo": f"O texto tem {total_chars} caracteres total ({chars_sem_espaco} sem espaços)"
            }
            
        else:
            resultado = {
                "erro": f"Tipo de análise '{tipo_analise}' não suportado",
                "tipos_suportados": ["contar_palavras", "maiuscula", "minuscula", "caracteres_total"]
            }
            
        return json.dumps(resultado, ensure_ascii=False, indent=2)
            
    except Exception as e:
        return json.dumps({
            "erro": "Erro na análise",
            "detalhes": str(e),
            "texto_recebido": texto,
            "tipo_analise": tipo_analise
        }, ensure_ascii=False, indent=2)

@tool
def calculadora_basica(operacao: str, numero1: float, numero2: float) -> str:
    """
    Realiza operações matemáticas básicas.
    
    Args:
        operacao: Tipo de operação (+, -, *, /)
        numero1: Primeiro número
        numero2: Segundo número
    
    Returns:
        str: Resultado da operação em JSON
    """
    try:
        if operacao == "+":
            resultado = numero1 + numero2
        elif operacao == "-":
            resultado = numero1 - numero2
        elif operacao == "*":
            resultado = numero1 * numero2
        elif operacao == "/":
            if numero2 == 0:
                return json.dumps({
                    "erro": "Divisão por zero não é permitida",
                    "operacao": operacao,
                    "numero1": numero1,
                    "numero2": numero2
                }, ensure_ascii=False, indent=2)
            resultado = numero1 / numero2
        else:
            return json.dumps({
                "erro": f"Operação '{operacao}' não suportada",
                "operacoes_suportadas": ["+", "-", "*", "/"]
            }, ensure_ascii=False, indent=2)
        
        resposta = {
            "tipo_resposta": "calculo_matematico",
            "operacao": operacao,
            "numero1": numero1,
            "numero2": numero2,
            "resultado": resultado,
            "resumo": f"{numero1} {operacao} {numero2} = {resultado}"
        }
        
        return json.dumps(resposta, ensure_ascii=False, indent=2)
        
    except Exception as e:
        return json.dumps({
            "erro": "Erro no cálculo",
            "detalhes": str(e),
            "operacao": operacao,
            "numero1": numero1,
            "numero2": numero2
        }, ensure_ascii=False, indent=2)
