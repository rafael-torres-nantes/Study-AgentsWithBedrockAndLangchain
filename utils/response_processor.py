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
        Converte resposta para string
        
        Args:
            response: Resposta em qualquer formato
            
        Returns:
            str: Resposta convertida para string
        """
        if isinstance(response, str):
            return response
        elif isinstance(response, bytes):
            return response.decode('utf-8', errors='replace')
        elif isinstance(response, (list, dict)):
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
                try:
                    response_json = json.loads(json_part, strict=False)
                    # Força encoding UTF-8 no JSON
                    response_json = json.loads(
                        json.dumps(response_json, ensure_ascii=False, indent=2), 
                        strict=False
                    )
                    return response_json
                except json.JSONDecodeError as je:
                    print(f'[DEBUG] Erro JSON: {je}')
                    return {
                        "message": response_str, 
                        "type": "agent_response",
                        "encoding_note": f"JSON inválido: {str(je)}"
                    }
            else:
                return {"message": response_str, "type": "agent_response"}
        else:
            return {"message": response_str, "type": "agent_response"}


def process_response(response: Union[str, bytes, list, dict]) -> Dict[str, Any]:
    """
    Função de conveniência para processar resposta do Bedrock
    
    Args:
        response: Resposta do Bedrock
        
    Returns:
        Dict[str, Any]: Resposta processada
    """
    return ResponseProcessor.process_bedrock_response(response)
