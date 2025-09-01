import json
import os
from typing import Optional, Dict, Any

class AmazonNovaPro:
    """
    Classe para configurar e gerenciar o modelo Amazon Nova Pro no Bedrock.
    
    Esta classe encapsula as configurações específicas do modelo Nova Pro,
    incluindo formatação do prompt e parâmetros de inferência.
    """
    
    def __init__(self, prompt_text: str, additional_config: Optional[Dict[str, Any]] = None):
        """
        Inicializa a classe AmazonNovaPro.
        
        Args:
            prompt_text (str): O texto do prompt para o modelo
            additional_config (dict, optional): Configurações adicionais para o modelo
        """
        self.prompt_text = prompt_text
        self.additional_config = additional_config or {}
        
        # ID do modelo Amazon Nova Pro
        self.model_id = "amazon.nova-pro-v1:0"
        
        # Configurações padrão do modelo
        self.default_config = {
            "max_tokens": int(os.getenv('MAX_TOKENS', 2048)),
            "temperature": float(os.getenv('TEMPERATURE', 0.7)),
            "top_p": float(os.getenv('TOP_P', 0.9)),
            "stop_sequences": []
        }
        
        # Mescla configurações padrão com configurações adicionais
        self.config = {**self.default_config, **self.additional_config}
        
    def get_model_id(self) -> str:
        """
        Retorna o ID do modelo Amazon Nova Pro.
        
        Returns:
            str: ID do modelo
        """
        return self.model_id
    
    def get_request_body(self) -> Dict[str, Any]:
        """
        Gera o corpo da requisição formatado para o modelo Amazon Nova Pro.
        
        Returns:
            dict: Corpo da requisição formatado para o Bedrock
        """
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": self.prompt_text
                        }
                    ]
                }
            ],
            "inferenceConfig": {
                "max_new_tokens": self.config["max_tokens"],
                "temperature": self.config["temperature"],
                "top_p": self.config["top_p"],
                "stopSequences": self.config["stop_sequences"]
            }
        }
        
        return request_body
    
    def update_prompt(self, new_prompt: str) -> None:
        """
        Atualiza o texto do prompt.
        
        Args:
            new_prompt (str): Novo texto do prompt
        """
        self.prompt_text = new_prompt
    
    def update_config(self, new_config: Dict[str, Any]) -> None:
        """
        Atualiza as configurações do modelo.
        
        Args:
            new_config (dict): Novas configurações
        """
        self.config.update(new_config)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Retorna as configurações atuais do modelo.
        
        Returns:
            dict: Configurações do modelo
        """
        return self.config.copy()
    
    def __str__(self) -> str:
        """
        Representação em string da classe.
        
        Returns:
            str: Informações da classe
        """
        return f"AmazonNovaPro(model_id='{self.model_id}', config={self.config})"
    
    def __repr__(self) -> str:
        """
        Representação para debug da classe.
        
        Returns:
            str: Representação debug
        """
        return self.__str__()