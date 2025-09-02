import os
from dotenv import load_dotenv
from langchain_aws import ChatBedrock
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from typing import List, Dict, Optional, Any
import logging


class LangChainCore:
    """
    Classe unificada para inferência e conversação usando LangChain com Amazon Bedrock.
    
    Combina funcionalidades de inferência básica e gerenciamento de conversação
    em uma única classe simplificada para facilitar o uso.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe LangChain core.
        
        Args:
            model_id (str, optional): ID do modelo Bedrock
            region (str): Região AWS
            temperature (float): Temperatura para geração de texto
            max_tokens (int, optional): Número máximo de tokens na resposta
            top_p (float, optional): Parâmetro top-p para nucleus sampling
            load_env (bool): Se deve carregar variáveis de ambiente
        """
        self.region = region
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        
        # Carrega variáveis de ambiente
        if load_env:
            load_dotenv()
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Define o model_id
        self.model_id = model_id or os.getenv('BEDROCK_MODEL_ID')
        if not self.model_id:
            raise ValueError("Model ID deve ser fornecido ou definido na variável BEDROCK_MODEL_ID")
        
        # Inicializa o modelo e histórico
        self.llm = self._initialize_model()
        self.chat_history = ChatMessageHistory()
        self.conversation_template = None
        
        # Define região AWS
        os.environ['AWS_REGION'] = self.region
    
    def _initialize_model(self) -> ChatBedrock:
        """Inicializa o modelo ChatBedrock com as configurações especificadas."""
        model_kwargs = {'temperature': self.temperature}
        
        if self.max_tokens is not None:
            model_kwargs['max_tokens'] = self.max_tokens
        if self.top_p is not None:
            model_kwargs['top_p'] = self.top_p
        
        return ChatBedrock(
            model_id=self.model_id, 
            model_kwargs=model_kwargs, 
            region_name=self.region
        )
    
    # ===============================
    # MÉTODOS DE INFERÊNCIA SIMPLES
    # ===============================
    
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
    
    def create_prompt_template(self, system_prompt: str, include_user_input: bool = True) -> ChatPromptTemplate:
        """
        Cria um template de prompt básico.
        
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
    
    def invoke_with_template(self, template: ChatPromptTemplate, **kwargs) -> str:
        """
        Executa inferência usando um template de prompt.
        
        Args:
            template (ChatPromptTemplate): Template de prompt
            **kwargs: Variáveis para substituição no template
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            messages = template.format_messages(**kwargs)
            result = self.llm.invoke(messages)
            return result.content
        except Exception as e:
            self.logger.error(f"Erro na inferência com template: {e}")
            raise
    
    # ===============================
    # MÉTODOS DE CONVERSAÇÃO
    # ===============================
    
    def create_conversation_template(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Cria um template de prompt para conversação com histórico.
        
        Args:
            system_prompt (str): Prompt do sistema
            
        Returns:
            ChatPromptTemplate: Template configurado para conversação
        """
        self.conversation_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{user_input}")
        ])
        return self.conversation_template
    
    def invoke_with_history(self, user_input: str, template: Optional[ChatPromptTemplate] = None) -> str:
        """
        Invoca o modelo mantendo histórico de conversação.
        
        Args:
            user_input (str): Mensagem do usuário
            template (ChatPromptTemplate, optional): Template personalizado
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            current_template = template or self.conversation_template
            if current_template is None:
                raise ValueError("Template de conversação não foi definido")
            
            # Prepara mensagens com histórico
            messages = current_template.format_messages(
                history=self.chat_history.messages,
                user_input=user_input
            )
            
            # Invoca o modelo
            result = self.llm.invoke(messages)
            
            # Adiciona ao histórico
            self.chat_history.add_user_message(user_input)
            self.chat_history.add_ai_message(result.content)
            
            return result.content
        except Exception as e:
            self.logger.error(f"Erro na invocação com histórico: {e}")
            raise
    
    # ===============================
    # MÉTODOS DE GERENCIAMENTO DE HISTÓRICO
    # ===============================
    
    def clear_history(self) -> bool:
        """Limpa o histórico de conversação."""
        try:
            self.chat_history.clear()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao limpar histórico: {e}")
            return False
    
    def get_history(self) -> List[Dict[str, str]]:
        """Retorna o histórico de conversação formatado."""
        history = []
        for message in self.chat_history.messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                history.append({"role": "system", "content": message.content})
        return history
    
    def load_history(self, history: List[Dict[str, str]]) -> bool:
        """Carrega um histórico de conversação."""
        try:
            self.chat_history.clear()
            for msg in history:
                if msg["role"] == "user":
                    self.chat_history.add_user_message(msg["content"])
                elif msg["role"] == "assistant":
                    self.chat_history.add_ai_message(msg["content"])
                elif msg["role"] == "system":
                    self.chat_history.messages.append(SystemMessage(content=msg["content"]))
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico: {e}")
            return False
    
    def add_system_message(self, content: str) -> bool:
        """Adiciona uma mensagem do sistema ao histórico."""
        try:
            self.chat_history.messages.append(SystemMessage(content=content))
            return True
        except Exception as e:
            self.logger.error(f"Erro ao adicionar mensagem do sistema: {e}")
            return False
    
    def get_last_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """Retorna as últimas N mensagens do histórico."""
        full_history = self.get_history()
        return full_history[-n:] if len(full_history) > n else full_history
    
    def get_history_length(self) -> int:
        """Retorna o número de mensagens no histórico."""
        return len(self.chat_history.messages)
    
    # ===============================
    # MÉTODOS DE CONFIGURAÇÃO E INFO
    # ===============================
    
    def update_model_parameters(self, temperature: Optional[float] = None, 
                              max_tokens: Optional[int] = None, 
                              top_p: Optional[float] = None):
        """Atualiza os parâmetros do modelo e reinicializa."""
        if temperature is not None:
            self.temperature = temperature
        if max_tokens is not None:
            self.max_tokens = max_tokens
        if top_p is not None:
            self.top_p = top_p
        
        # Reinicializa o modelo
        self.llm = self._initialize_model()
    
    def get_model_info(self) -> Dict[str, Any]:
        """Retorna informações sobre o modelo e configuração atual."""
        return {
            'model_id': self.model_id,
            'region': self.region,
            'temperature': self.temperature,
            'max_tokens': self.max_tokens,
            'top_p': self.top_p,
            'framework': 'LangChain',
            'service': 'Amazon Bedrock',
            'class_type': 'LangChainCore',
            'history_length': self.get_history_length(),
            'has_conversation_template': self.conversation_template is not None,
            'features': [
                'simple_inference',
                'conversation_management',
                'history_management',
                'template_support'
            ]
        }
    
    def export_session(self) -> Dict[str, Any]:
        """Exporta a sessão completa para backup/análise."""
        return {
            'model_info': self.get_model_info(),
            'history': self.get_history(),
            'timestamp': str(os.popen('echo %date% %time%').read().strip()) if os.name == 'nt' else str(os.popen('date').read().strip())
        }
