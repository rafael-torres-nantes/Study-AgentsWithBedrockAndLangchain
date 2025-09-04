"""
Utilitários para processamento de resposta do Bedrock
"""
import json
from typing import Union, Dict, Any


class ResponseProcessor:
    """
    Classe responsável por processar e formatar respostas do Bedrock
    """
    
    @staticmethod
    def process_bedrock_response(response: Union[str, bytes, list, dict]) -> Dict[str, Any]:
        """
        Processa resposta do Bedrock com tratamento robusto de encoding e JSON
        
        Args:
            response: Resposta do Bedrock em qualquer formato
            
        Returns:
            Dict[str, Any]: Resposta processada e formatada
        """
        try:
            # Converte resposta para string se necessário
            response_str = ResponseProcessor._convert_to_string(response)
            
            # Aplica tratamento de encoding UTF-8
            response_str = ResponseProcessor._fix_encoding(response_str)
            
            # Decodifica caracteres unicode escapados
            response_str = ResponseProcessor._decode_unicode_escapes(response_str)
            
            # Processa JSON se presente
            response_json = ResponseProcessor._extract_json(response_str)
            
            print('[DEBUG] Resposta processada com sucesso')
            return response_json
        
        except Exception as e:
            print(f'[DEBUG] Erro no processamento da resposta: {e}')
            return {
                "message": str(response), 
                "type": "agent_response",
                "processing_error": str(e)
            }
    
    @staticmethod
    def _convert_to_string(response: Union[str, bytes, list, dict]) -> str:
        """
        Converte resposta para string, com tratamento especial para Amazon Nova Pro
        
        Args:
            response: Resposta em qualquer formato
            
        Returns:
            str: Resposta convertida para string
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, bytes):
            return response.decode('utf-8', errors='replace')
        
        elif isinstance(response, list):
            # Se é uma lista de dicts do Bedrock, processa cada item
            if response and isinstance(response[0], dict):
                # Tratamento especial para Amazon Nova Pro format
                if 'text' in response[0]:
                    return response[0].get('text', str(response))
                
                # Se tem type e text (formato nova pro)
                elif 'type' in response[0] and response[0].get('type') == 'text':
                    return response[0].get('text', str(response))
            return str(response)
        
        elif isinstance(response, dict):
            # Se é um dict, tenta extrair o texto ou converte para string
            if 'text' in response:
                return response['text']
            return str(response)
        else:
            return str(response)
    
    @staticmethod
    def _fix_encoding(response_str: str) -> str:
        """
        Aplica correções de encoding UTF-8
        
        Args:
            response_str: String da resposta
            
        Returns:
            str: String com encoding corrigido
        """
        try:
            # Tenta garantir que é UTF-8 válido
            if isinstance(response_str, bytes):
                response_str = response_str.decode('utf-8', errors='replace')
            else:
                # Se já é string, recodifica para garantir UTF-8
                response_str = response_str.encode('utf-8', errors='replace').decode('utf-8')
        except Exception:
            pass  # Mantém original se houver erro
        
        return response_str
    
    @staticmethod
    def _decode_unicode_escapes(response_str: str) -> str:
        """
        Decodifica caracteres unicode escapados
        
        Args:
            response_str: String com possíveis escapes unicode
            
        Returns:
            str: String com unicode decodificado
        """
        if '\\u' in response_str:
            try:
                response_str = response_str.encode('latin-1').decode('unicode_escape')
            except Exception:
                pass  # Mantém original se falhar
        
        return response_str
    
    @staticmethod
    def _extract_json(response_str: str) -> Dict[str, Any]:
        """
        Extrai e processa JSON da resposta
        
        Args:
            response_str: String da resposta
            
        Returns:
            Dict[str, Any]: JSON processado ou resposta como mensagem
        """
        # Processa JSON se presente
        if '{' in response_str and '}' in response_str:
            start = response_str.find('{')
            end = response_str.rfind('}') + 1
            if start >= 0 and end > start:
                json_part = response_str[start:end]
                
                # Limpa caracteres inválidos que podem causar erro de parsing
                json_part = ResponseProcessor._clean_json_string(json_part)
                
                try:
                    response_json = json.loads(json_part, strict=False)
                    return response_json
                except json.JSONDecodeError as je:
                    print(f'[DEBUG] Erro JSON: {je}')
                    print(f'[DEBUG] JSON problemático: {json_part[:200]}...')
                    return {
                        "message": response_str, 
                        "type": "agent_response",
                        "encoding_note": f"JSON inválido: {str(je)}"
                    }
            else:
                return {"message": response_str, "type": "agent_response"}
        else:
            return {"message": response_str, "type": "agent_response"}
    
    @staticmethod
    def _clean_json_string(json_str: str) -> str:
        """
        Limpa string JSON removendo caracteres problemáticos
        
        Args:
            json_str: String JSON para limpar
            
        Returns:
            str: String JSON limpa
        """
        import re
        
        # Remove caracteres de controle que podem quebrar o JSON
        json_str = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', json_str)
        
        # Corrige escapes inválidos de aspas simples dentro de strings JSON
        # Substitui \' por ' (aspas simples não precisam ser escapadas em JSON)
        json_str = json_str.replace("\\'", "'")
        
        # Corrige escapes de aspas duplas em strings 
        # \\" deve ser \" em JSON válido
        json_str = json_str.replace('\\"', '"')
        
        # Remove outros escapes inválidos (mantém apenas os válidos: \", \\, \/, \b, \f, \n, \r, \t, \uXXXX)
        json_str = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'', json_str)
        
        return json_str.strip()


def process_response(response: Union[str, bytes, list, dict]) -> Dict[str, Any]:
    """
    Função de conveniência para processar resposta do Bedrock
    
    Args:
        response: Resposta do Bedrock
        
    Returns:
        Dict[str, Any]: Resposta processada
    """
    return ResponseProcessor.process_bedrock_response(response)


def extract_clean_response(response_json: Union[str, dict]) -> Dict[str, Any]:
    """
    Extrai uma resposta limpa e formatada do JSON de resposta do modelo.
    
    Args:
        response_json (dict): JSON de resposta processado
        
    Returns:
        dict: Resposta formatada de forma limpa
    """
    try:
        # Tenta extrair a resposta do campo 'resposta' 
        if isinstance(response_json, dict) and 'resposta' in response_json:
            return {
                "output_response": response_json['resposta']
            }
        # Tenta extrair de 'message' se 'resposta' não existir
        elif isinstance(response_json, dict) and 'message' in response_json:
            return {
                "output_response": response_json['message']
            }
        # Se for string diretamente
        elif isinstance(response_json, str):
            return {
                "output_response": response_json
            }
        # Fallback para estrutura complexa
        else:
            return {
                "output_response": str(response_json),
                "note": "Complex response structure converted to string"
            }
    except Exception as e:
        return {
            "output_response": "Error processing response",
            "error": str(e)
        }
