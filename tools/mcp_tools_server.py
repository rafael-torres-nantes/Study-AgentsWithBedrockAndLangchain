"""
MCP Tools Server - Servidor de ferramentas usando Model Context Protocol
"""
import json
import re
import os
import logging
import hashlib
from typing import Dict, Any, List, Optional
from mcp.server.fastmcp import FastMCP

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializa o servidor MCP para ferramentas
mcp_tools = FastMCP("LangChain-Agent-Tools")

@mcp_tools.tool()
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
        logger.error(f"Erro na contagem de caracteres: {e}")
        return json.dumps({
            "erro": "Erro ao processar contagem",
            "detalhes": str(e),
            "texto_recebido": texto,
            "caracter_recebido": caracter
        }, ensure_ascii=False, indent=2)

@mcp_tools.tool()
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
            
        elif tipo_analise in ["maiuscula", "maiúscula"]:
            resultado = {
                "tipo_resposta": "conversao_maiuscula",
                "texto_original": texto,
                "texto_convertido": texto.upper(),
                "resumo": f"Texto convertido para maiúscula"
            }
            
        elif tipo_analise in ["minuscula", "minúscula", "converter_minusculas"]:
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
                "tipos_suportados": ["contar_palavras", "maiuscula", "minuscula", "caracteres_total", "converter_minusculas"]
            }
            
        return json.dumps(resultado, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Erro na análise de texto: {e}")
        return json.dumps({
            "erro": "Erro na análise",
            "detalhes": str(e),
            "texto_recebido": texto,
            "tipo_analise": tipo_analise
        }, ensure_ascii=False, indent=2)

@mcp_tools.tool()
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
        logger.error(f"Erro no cálculo: {e}")
        return json.dumps({
            "erro": "Erro no cálculo",
            "detalhes": str(e),
            "operacao": operacao,
            "numero1": numero1,
            "numero2": numero2
        }, ensure_ascii=False, indent=2)

@mcp_tools.tool()
def analisar_sentimento(texto: str) -> str:
    """
    Analisa o sentimento básico de um texto.
    
    Args:
        texto: O texto a ser analisado
    
    Returns:
        str: Resultado da análise de sentimento em JSON
    """
    try:
        if not texto:
            return json.dumps({
                "erro": "Texto não fornecido"
            }, ensure_ascii=False, indent=2)
        
        # Análise básica de sentimento por palavras-chave
        palavras_positivas = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'feliz', 'alegre', 'amor', 'sucesso', 'positivo']
        palavras_negativas = ['ruim', 'péssimo', 'terrível', 'horrível', 'triste', 'raiva', 'ódio', 'fracasso', 'negativo']
        
        texto_lower = texto.lower()
        score_positivo = sum(1 for palavra in palavras_positivas if palavra in texto_lower)
        score_negativo = sum(1 for palavra in palavras_negativas if palavra in texto_lower)
        
        if score_positivo > score_negativo:
            sentimento = "positivo"
        elif score_negativo > score_positivo:
            sentimento = "negativo"
        else:
            sentimento = "neutro"
        
        resultado = {
            "tipo_resposta": "analise_sentimento",
            "texto_analisado": texto,
            "sentimento": sentimento,
            "score_positivo": score_positivo,
            "score_negativo": score_negativo,
            "resumo": f"O texto tem sentimento {sentimento} (positivo: {score_positivo}, negativo: {score_negativo})"
        }
        
        return json.dumps(resultado, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Erro na análise de sentimento: {e}")
        return json.dumps({
            "erro": "Erro na análise de sentimento",
            "detalhes": str(e),
            "texto_recebido": texto
        }, ensure_ascii=False, indent=2)

@mcp_tools.tool()
def extrair_emails(texto: str) -> str:
    """
    Extrai endereços de email de um texto.
    
    Args:
        texto: O texto onde buscar emails
    
    Returns:
        str: Lista de emails encontrados em JSON
    """
    try:
        if not texto:
            return json.dumps({
                "erro": "Texto não fornecido"
            }, ensure_ascii=False, indent=2)
        
        # Regex para encontrar emails
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(pattern, texto)
        
        resultado = {
            "tipo_resposta": "extracao_emails",
            "texto_analisado": texto,
            "emails_encontrados": emails,
            "total_emails": len(emails),
            "resumo": f"Foram encontrados {len(emails)} email(s) no texto"
        }
        
        return json.dumps(resultado, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Erro na extração de emails: {e}")
        return json.dumps({
            "erro": "Erro na extração de emails",
            "detalhes": str(e),
            "texto_recebido": texto
        }, ensure_ascii=False, indent=2)

@mcp_tools.tool()
def gerar_hash(texto: str, algoritmo: str = "md5") -> str:
    """
    Gera hash de um texto usando diferentes algoritmos.
    
    Args:
        texto: O texto para gerar hash
        algoritmo: Algoritmo de hash (md5, sha1, sha256)
    
    Returns:
        str: Hash gerado em JSON
    """
    try:
        if not texto:
            return json.dumps({
                "erro": "Texto não fornecido"
            }, ensure_ascii=False, indent=2)
        
        if algoritmo == "md5":
            hash_result = hashlib.md5(texto.encode()).hexdigest()
        elif algoritmo == "sha1":
            hash_result = hashlib.sha1(texto.encode()).hexdigest()
        elif algoritmo == "sha256":
            hash_result = hashlib.sha256(texto.encode()).hexdigest()
        else:
            return json.dumps({
                "erro": f"Algoritmo '{algoritmo}' não suportado",
                "algoritmos_suportados": ["md5", "sha1", "sha256"]
            }, ensure_ascii=False, indent=2)
        
        resultado = {
            "tipo_resposta": "geracao_hash",
            "texto_original": texto,
            "algoritmo": algoritmo,
            "hash": hash_result,
            "resumo": f"Hash {algoritmo.upper()} gerado com sucesso"
        }
        
        return json.dumps(resultado, ensure_ascii=False, indent=2)
        
    except Exception as e:
        logger.error(f"Erro na geração de hash: {e}")
        return json.dumps({
            "erro": "Erro na geração de hash",
            "detalhes": str(e),
            "texto_recebido": texto,
            "algoritmo": algoritmo
        }, ensure_ascii=False, indent=2)

# Função para obter todas as tools MCP
def get_mcp_tools_functions():
    """
    Retorna todas as tools registradas no servidor MCP.
    
    Returns:
        List: Lista de funções das tools MCP
    """
    return [
        contador_caracteres,
        analisar_texto,
        calculadora_basica,
        analisar_sentimento,
        extrair_emails,
        gerar_hash
    ]

# Função para obter nomes das tools
def get_mcp_tools_names():
    """
    Retorna os nomes de todas as tools MCP.
    
    Returns:
        List[str]: Lista com nomes das tools
    """
    return [
        "contador_caracteres",
        "analisar_texto", 
        "calculadora_basica",
        "analisar_sentimento",
        "extrair_emails",
        "gerar_hash"
    ]

# Função para iniciar o servidor MCP
def run_mcp_tools_server(host: str = "localhost", port: int = 8000):
    """
    Inicia o servidor MCP de ferramentas.
    
    Args:
        host: Host do servidor
        port: Porta do servidor
    """
    import uvicorn
    logger.info(f"Iniciando servidor MCP Tools em {host}:{port}")
    uvicorn.run(mcp_tools.app, host=host, port=port)

if __name__ == "__main__":
    # Inicia o servidor MCP quando executado diretamente
    run_mcp_tools_server()
