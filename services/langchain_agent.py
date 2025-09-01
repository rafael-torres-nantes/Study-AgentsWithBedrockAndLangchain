import os
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool
from typing import List, Dict, Optional, Any, Callable
import logging
from .langchain_conversation import LangChainConversation


class LangChainAgent:
    """
    Classe para criação e execução de agentes com tools usando LangChain e Amazon Bedrock.
    
    Esta classe permite criar agentes inteligentes que podem usar ferramentas (tools)
    para executar tarefas específicas, combinando conversação contextual com
    capacidades de execução de ações.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe de agente do Bedrock.
        
        Args:
            model_id (str, optional): ID do modelo Bedrock. Se None, usa variável de ambiente.
            region (str): Região AWS. Padrão: 'us-east-1'
            temperature (float): Temperatura para geração de texto. Padrão: 0.0
            max_tokens (int, optional): Número máximo de tokens na resposta
            top_p (float, optional): Parâmetro top-p para nucleus sampling
            load_env (bool): Se deve carregar variáveis de ambiente. Padrão: True
        """
        # Inicializa a classe de conversação (que herda de inferência)
        self.conversation = LangChainConversation(model_id=model_id, region=region, temperature=temperature,
            max_tokens=max_tokens, top_p=top_p, load_env=load_env)
        
        # Lista de tools disponíveis
        self.tools: List[BaseTool] = []
        
        # Agente e executor
        self.agent = None
        self.agent_executor = None
        
        # Logger para a classe
        self.logger = logging.getLogger(__name__)
        
        # Template padrão para agente
        self.agent_template = None
    
    @property
    def model_id(self):
        """Retorna o model_id da classe de conversação."""
        return self.conversation.model_id
    
    @property
    def llm(self):
        """Retorna o modelo LLM da classe de conversação."""
        return self.conversation.llm
    
    def create_agent_template(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Cria um template de prompt para o agente com suporte a tools.
        
        Args:
            system_prompt (str): Prompt do sistema para o agente
            
        Returns:
            ChatPromptTemplate: Template configurado para agente
        """
        self.agent_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return self.agent_template
    
    def add_tool(self, tool: BaseTool) -> bool:
        """
        Adiciona uma tool à lista de ferramentas do agente.
        
        Args:
            tool (BaseTool): Ferramenta a ser adicionada
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            if tool not in self.tools:
                self.tools.append(tool)
                # Se já existe um agente, precisa recriar com as novas tools
                if self.agent is not None:
                    self._recreate_agent()
                return True
            else:
                self.logger.warning(f"Tool {tool.name} já existe na lista")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao adicionar tool: {e}")
            return False
    
    def add_tools(self, tools: List[BaseTool]) -> int:
        """
        Adiciona múltiplas tools à lista de ferramentas do agente.
        
        Args:
            tools (List[BaseTool]): Lista de ferramentas a serem adicionadas
            
        Returns:
            int: Número de tools adicionadas com sucesso
        """
        added_count = 0
        for tool in tools:
            if self.add_tool(tool):
                added_count += 1
        return added_count
    
    def remove_tool(self, tool_name: str) -> bool:
        """
        Remove uma tool da lista de ferramentas do agente.
        
        Args:
            tool_name (str): Nome da ferramenta a ser removida
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            for i, tool in enumerate(self.tools):
                if tool.name == tool_name:
                    self.tools.pop(i)
                    # Se já existe um agente, precisa recriar com as tools atualizadas
                    if self.agent is not None:
                        self._recreate_agent()
                    return True
            self.logger.warning(f"Tool {tool_name} não encontrada")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao remover tool: {e}")
            return False
    
    def create_agent(self, template: Optional[ChatPromptTemplate] = None) -> bool:
        """
        Cria o agente com as tools configuradas.
        
        Args:
            template (ChatPromptTemplate, optional): Template personalizado. Se None, usa o padrão.
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            if not self.tools:
                raise ValueError("Nenhuma tool foi adicionada. Adicione pelo menos uma tool antes de criar o agente.")
            
            # Usa template fornecido ou o padrão da classe
            current_template = template or self.agent_template
            
            if current_template is None:
                raise ValueError("Nenhum template de agente foi definido. Use create_agent_template() primeiro.")
            
            # Cria o agente
            self.agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=current_template
            )
            
            # Cria o executor do agente
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar agente: {e}")
            return False
    
    def _recreate_agent(self):
        """Recria o agente com as tools atualizadas."""
        if self.agent_template is not None:
            self.create_agent()
    
    def invoke_agent(self, user_input: str, include_history: bool = True) -> str:
        """
        Executa o agente com a entrada do usuário.
        
        Args:
            user_input (str): Entrada do usuário
            include_history (bool): Se deve incluir histórico da conversação
            
        Returns:
            str: Resposta do agente
        """
        try:
            if self.agent_executor is None:
                raise ValueError("Agente não foi criado. Use create_agent() primeiro.")
            
            # Prepara o input para o agente
            agent_input = {
                "input": user_input,
                "chat_history": self.conversation.chat_history.messages if include_history else []
            }
            
            # Executa o agente
            result = self.agent_executor.invoke(agent_input)
            
            # Adiciona ao histórico da conversação se solicitado
            if include_history:
                self.conversation.chat_history.add_user_message(user_input)
                self.conversation.chat_history.add_ai_message(result["output"])
            
            return result["output"]
            
        except Exception as e:
            self.logger.error(f"Erro na execução do agente: {e}")
            raise
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Retorna informações sobre as tools disponíveis.
        
        Returns:
            List[Dict]: Lista com informações das tools
        """
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "type": type(tool).__name__
            })
        return tools_info
    
    def clear_conversation_history(self) -> bool:
        """
        Limpa o histórico de conversação do agente.
        
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        return self.conversation.clear_history()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """
        Retorna o histórico de conversação do agente.
        
        Returns:
            List[Dict]: Histórico formatado
        """
        return self.conversation.get_history()
    
    def load_conversation_history(self, history: List[Dict[str, str]]) -> bool:
        """
        Carrega um histórico de conversação para o agente.
        
        Args:
            history (List[Dict]): Histórico a ser carregado
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        return self.conversation.load_history(history)
    
    def get_agent_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre o agente atual.
        
        Returns:
            Dict[str, Any]: Informações do agente
        """
        conversation_info = self.conversation.get_conversation_info()
        conversation_info.update({
            'class_type': 'LangChainAgent',
            'tools_count': len(self.tools),
            'available_tools': self.get_available_tools(),
            'agent_created': self.agent is not None,
            'agent_executor_created': self.agent_executor is not None,
            'agent_features': [
                'tool_calling',
                'multi_step_reasoning',
                'context_preservation',
                'error_handling'
            ]
        })
        return conversation_info
    
    def create_custom_tool(self, name: str, description: str, func: Callable) -> BaseTool:
        """
        Cria uma tool customizada a partir de uma função.
        
        Args:
            name (str): Nome da ferramenta
            description (str): Descrição da ferramenta
            func (Callable): Função que implementa a ferramenta
            
        Returns:
            BaseTool: Ferramenta criada
        """
        from langchain_core.tools import tool
        
        # Cria a tool usando o decorador
        @tool(name=name, description=description)
        def custom_tool(input_text: str) -> str:
            """Tool customizada criada dinamicamente."""
            return func(input_text)
        
        return custom_tool
    
    def export_agent_state(self) -> Dict[str, Any]:
        """
        Exporta o estado completo do agente para backup/análise.
        
        Returns:
            Dict[str, Any]: Estado do agente
        """
        return {
            'agent_info': self.get_agent_info(),
            'conversation_history': self.get_conversation_history(),
            'tools_info': self.get_available_tools(),
            'timestamp': str(os.popen('date').read().strip()) if os.name != 'nt' else str(os.popen('echo %date% %time%').read().strip())
        }
