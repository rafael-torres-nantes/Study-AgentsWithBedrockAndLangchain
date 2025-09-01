import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate
from typing import Optional, Dict, Any
import logging


class LangChainInference:
    """
    Classe para inferência básica usando LangChain com Amazon Bedrock.
    
    Esta classe fornece funcionalidades básicas de inferência com modelos
    de IA do Amazon Bedrock através do LangChain, incluindo configuração
    de modelos e execução de prompts simples.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe de inferência do Bedrock.
        
        Args:
            model_id (str, optional): ID do modelo Bedrock. Se None, usa variável de ambiente.
            region (str): Região AWS. Padrão: 'us-east-1'
            temperature (float): Temperatura para geração de texto. Padrão: 0.0
            max_tokens (int, optional): Número máximo de tokens na resposta
            top_p (float, optional): Parâmetro top-p para nucleus sampling
            load_env (bool): Se deve carregar variáveis de ambiente. Padrão: True
        """
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        
        # Carrega variáveis de ambiente se solicitado
        if load_env:
            load_dotenv()

        # Criação do logger para a classe
        self.logger = logging.getLogger(__name__)
        
        # Define o model_id
        self.model_id = model_id or os.getenv('BEDROCK_MODEL_ID')
        if not self.model_id:
            raise ValueError("Model ID deve ser fornecido ou definido na variável BEDROCK_MODEL_ID")
        
        # Inicializa o modelo LangChain
        self.llm = self._initialize_model()
        
        # Define a região AWS
        os.environ['AWS_REGION'] = self.region
    
    def _initialize_model(self) -> ChatBedrock:
        """
        Inicializa o modelo ChatBedrock com as configurações especificadas.
        
        Returns:
            ChatBedrock: Instância configurada do modelo
        """
        model_kwargs = {'temperature': self.temperature}
        
        # Adiciona parâmetros MAX_TOKENS se especificados
        if self.max_tokens is not None:
            model_kwargs['max_tokens'] = self.max_tokens
       
        # Adiciona parâmetros TOP_P se especificados
        if self.top_p is not None:
            model_kwargs['top_p'] = self.top_p
        
        return ChatBedrock(model_id=self.model_id, model_kwargs=model_kwargs, region_name=self.region)
    
    def create_prompt_template(self, system_prompt: str, include_user_input: bool = True) -> ChatPromptTemplate:
        """
        Cria um template de prompt para o modelo.
        
        Args:
            system_prompt (str): Prompt do sistema
            include_user_input (bool): Se deve incluir campo para entrada do usuário
            
        Returns:
            ChatPromptTemplate: Template de prompt configurado
        """
        messages = [("system", system_prompt)]
        
        if include_user_input:
            messages.append(("human", "{user_input}"))
            
        return ChatPromptTemplate.from_messages(messages)
    
    def invoke_simple(self, prompt: str) -> str:
        """
        Executa uma inferência simples com o modelo.
        
        Args:
            prompt (str): Prompt/pergunta para o modelo
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            result = self.llm.invoke(prompt)
            return result.content
            
        except Exception as e:
            self.logger.error(f"Erro na inferência simples: {e}")
            raise
    
    def invoke_with_template(self, template: ChatPromptTemplate, **kwargs) -> str:
        """
        Executa uma inferência usando um template de prompt.
        
        Args:
            template (ChatPromptTemplate): Template de prompt
            **kwargs: Variáveis para substituição no template
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            # Formata as mensagens usando o template
            messages = template.format_messages(**kwargs)
            
            # Invoca o modelo
            result = self.llm.invoke(messages)
            return result.content
            
        except Exception as e:
            self.logger.error(f"Erro na inferência com template: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o modelo e configuração atual.
        
        Returns:
            Dict[str, Any]: Informações do modelo
        """
        return {
            'model_id': self.model_id,
            'region': self.region,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'framework': 'LangChain',
            'service': 'Amazon Bedrock',
            'class_type': 'LangChainInference'
        }
    
    def update_model_parameters(self, temperature: Optional[float] = None, 
                              max_tokens: Optional[int] = None, 
                              top_p: Optional[float] = None):
        """
        Atualiza os parâmetros do modelo e reinicializa.
        
        Args:
            temperature (float, optional): Nova temperatura
            max_tokens (int, optional): Novo limite de tokens
            top_p (float, optional): Novo valor de top_p
        """
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if top_p is not None:
            self.top_p = top_p
            
        # Reinicializa o modelo com os novos parâmetros
        self.llm = self._initialize_model()
