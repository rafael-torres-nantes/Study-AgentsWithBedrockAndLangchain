import os
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import List, Dict, Optional, Any
import logging
from .langchain_inference import LangChainInference


class LangChainConversation:
    """
    Classe para gerenciamento de conversação e histórico usando LangChain com Amazon Bedrock.
    
    Esta classe estende as funcionalidades básicas de inferência para incluir
    gerenciamento de histórico de conversação, permitindo conversas contínuas
    e contextualizadas com o modelo de IA.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe de conversação do Bedrock.
        
        Args:
            model_id (str, optional): ID do modelo Bedrock. Se None, usa variável de ambiente.
            region (str): Região AWS. Padrão: 'us-east-1'
            temperature (float): Temperatura para geração de texto. Padrão: 0.0
            max_tokens (int, optional): Número máximo de tokens na resposta
            top_p (float, optional): Parâmetro top-p para nucleus sampling
            load_env (bool): Se deve carregar variáveis de ambiente. Padrão: True
        """
        # Inicializa a classe base de inferência
        self.inference = LangChainInference(
            model_id=model_id,
            region=region,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            load_env=load_env
        )
        
        # Inicializa o histórico de mensagens usando LangChain
        self.chat_history = ChatMessageHistory()
        
        # Logger para a classe
        self.logger = logging.getLogger(__name__)
        
        # Template padrão para conversação
        self.conversation_template = None
    
    @property
    def model_id(self):
        """Retorna o model_id da classe de inferência."""
        return self.inference.model_id
    
    @property
    def llm(self):
        """Retorna o modelo LLM da classe de inferência."""
        return self.inference.llm
    
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
        Invoca o modelo usando o template de conversação e mantendo histórico.
        
        Args:
            user_input (str): Mensagem do usuário
            template (ChatPromptTemplate, optional): Template personalizado. Se None, usa o padrão.
            
        Returns:
            str: Resposta gerada pelo modelo
        """
        try:
            # Usa template fornecido ou o padrão da classe
            current_template = template or self.conversation_template
            
            if current_template is None:
                raise ValueError("Nenhum template de conversação foi definido. Use create_conversation_template() primeiro.")
            
            # Prepara as mensagens com histórico
            messages = current_template.format_messages(
                history=self.chat_history.messages,
                user_input=user_input
            )
            
            # Invoca o modelo
            result = self.llm.invoke(messages)
            
            # Adiciona as mensagens ao histórico
            self.chat_history.add_user_message(user_input)
            self.chat_history.add_ai_message(result.content)
            
            return result.content
            
        except Exception as e:
            self.logger.error(f"Erro na invocação com histórico: {e}")
            raise
    
    def clear_history(self) -> bool:
        """
        Limpa o histórico de conversação.
        
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            self.chat_history.clear()
            return True
        except Exception as e:
            self.logger.error(f"Erro ao limpar histórico: {e}")
            return False
    
    def get_history(self) -> List[Dict[str, str]]:
        """
        Retorna o histórico de conversação formatado.
        
        Returns:
            List[Dict]: Lista com o histórico formatado
        """
        history = []
        
        # Itera sobre as mensagens no histórico e formata
        for message in self.chat_history.messages:
            # Formata conforme o papel da mensagem
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            # Adiciona mensagem do assistente
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
            # Adiciona mensagem do sistema (se houver)
            elif isinstance(message, SystemMessage):
                history.append({"role": "system", "content": message.content})
        
        return history
    
    def load_history(self, history: List[Dict[str, str]]) -> bool:
        """
        Carrega um histórico de conversação.
        
        Args:
            history (List[Dict]): Lista com mensagens no formato {"role": "user/assistant/system", "content": "..."}
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            # Limpa o histórico atual
            self.chat_history.clear()
            
            # Adiciona mensagens do histórico fornecido
            for msg in history:
                # Adiciona mensagem conforme o papel
                if msg["role"] == "user":
                    self.chat_history.add_user_message(msg["content"])
                # Adiciona mensagem do assistente
                elif msg["role"] == "assistant":
                    self.chat_history.add_ai_message(msg["content"])
                # Adiciona mensagem do sistema
                elif msg["role"] == "system":
                    # Para mensagens do sistema, cria um SystemMessage diretamente
                    self.chat_history.messages.append(SystemMessage(content=msg["content"]))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico: {e}")
            return False
    
    def get_history_length(self) -> int:
        """
        Retorna o número de mensagens no histórico.
        
        Returns:
            int: Número de mensagens no histórico
        """
        return len(self.chat_history.messages)
    
    def add_system_message(self, content: str) -> bool:
        """
        Adiciona uma mensagem do sistema ao histórico.
        
        Args:
            content (str): Conteúdo da mensagem do sistema
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            self.chat_history.messages.append(SystemMessage(content=content))
            return True
        except Exception as e:
            self.logger.error(f"Erro ao adicionar mensagem do sistema: {e}")
            return False
    
    def get_last_messages(self, n: int = 5) -> List[Dict[str, str]]:
        """
        Retorna as últimas N mensagens do histórico.
        
        Args:
            n (int): Número de mensagens a retornar
            
        Returns:
            List[Dict]: Lista com as últimas mensagens
        """
        full_history = self.get_history()
        return full_history[-n:] if len(full_history) > n else full_history
    
    def get_conversation_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre a conversação atual.
        
        Returns:
            Dict[str, Any]: Informações da conversação
        """
        model_info = self.inference.get_model_info()
        model_info.update({
            'class_type': 'LangChainConversation',
            'history_length': self.get_history_length(),
            'has_conversation_template': self.conversation_template is not None,
            'conversation_features': [
                'history_management',
                'multi_turn_conversation',
                'context_preservation'
            ]
        })
        return model_info
    
    def export_conversation(self) -> Dict[str, Any]:
        """
        Exporta a conversação completa para backup/análise.
        
        Returns:
            Dict[str, Any]: Dados da conversação
        """
        return {
            'model_info': self.get_conversation_info(),
            'history': self.get_history(),
            'timestamp': str(os.popen('date').read().strip()) if os.name != 'nt' else str(os.popen('echo %date% %time%').read().strip())
        }
