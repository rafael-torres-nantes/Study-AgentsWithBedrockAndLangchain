"""
Agente LangChain refatorado para usar MCP (Model Context Protocol)
"""
import os
import logging
from typing import List, Dict, Optional, Any, Callable
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool, tool
from services.mcp_langchain_conversation import MCPLangChainConversation


class MCPLangChainAgent:
    """
    Classe para criação e execução de agentes com MCP tools usando LangChain e Amazon Bedrock.
    
    Esta classe integra o padrão MCP (Model Context Protocol) para criar agentes mais modulares
    e organizados, permitindo melhor reutilização de código e manutenção.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe de agente MCP do Bedrock.
        
        Args:
            model_id (str, optional): ID do modelo Bedrock. Se None, usa variável de ambiente.
            region (str): Região AWS. Padrão: 'us-east-1'
            temperature (float): Temperatura para geração de texto. Padrão: 0.0
            max_tokens (int, optional): Número máximo de tokens na resposta
            top_p (float, optional): Parâmetro top-p para nucleus sampling
            load_env (bool): Se deve carregar variáveis de ambiente. Padrão: True
        """
        # Inicializa a classe de conversação MCP
        self.conversation = MCPLangChainConversation(
            model_id=model_id, 
            region=region, 
            temperature=temperature,
            max_tokens=max_tokens, 
            top_p=top_p, 
            load_env=load_env
        )
        
        # Lista de tools disponíveis (inclui MCP tools + tools customizadas)
        self.tools: List[BaseTool] = []
        
        # Agente e executor
        self.agent = None
        self.agent_executor = None
        
        # Logger para a classe
        self.logger = logging.getLogger(__name__)
        
        # Template padrão para agente
        self.agent_template = None
        
        # Carrega automaticamente as tools MCP
        self._load_mcp_tools()
    
    def _load_mcp_tools(self):
        """Carrega automaticamente as tools MCP na lista de tools do agente."""
        try:
            mcp_tools = self.conversation.get_mcp_tools()
            self.tools.extend(mcp_tools)
            self.logger.info(f"Carregadas {len(mcp_tools)} tools MCP")
        except Exception as e:
            self.logger.error(f"Erro ao carregar tools MCP: {e}")
    
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
        Cria um template de prompt para o agente com suporte a MCP tools.
        
        Args:
            system_prompt (str): Prompt do sistema para o agente
            
        Returns:
            ChatPromptTemplate: Template configurado para agente
        """
        # Adiciona informações sobre as tools MCP disponíveis ao prompt
        mcp_tools_info = self.conversation.get_mcp_tool_info()
        
        enhanced_system_prompt = f"""{system_prompt}

        Você tem acesso às seguintes ferramentas MCP (Model Context Protocol):
        {mcp_tools_info['tools_disponiveis']}

        Total de ferramentas disponíveis: {mcp_tools_info['total_tools']}
        Framework: {mcp_tools_info['framework']}

        Use essas ferramentas quando necessário para ajudar o usuário."""
        
        self.agent_template = ChatPromptTemplate.from_messages([
            ("system", enhanced_system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        return self.agent_template
    
    def register_mcp_tool(self, name: str, description: str, func: Callable) -> bool:
        """
        Registra uma nova tool MCP customizada.
        
        Args:
            name (str): Nome da tool
            description (str): Descrição da tool
            func (Callable): Função que implementa a tool
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            from langchain_core.tools import StructuredTool
            
            # Registra na conversação MCP
            self.conversation.register_mcp_tool(name, func)
            
            # Cria uma tool LangChain correspondente
            mcp_custom_tool = StructuredTool.from_function(
                func=func,
                name=name,
                description=description
            )
            
            # Adiciona à lista de tools do agente
            self.add_tool(mcp_custom_tool)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao registrar tool MCP customizada: {e}")
            return False
    
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
        Cria o agente com as tools configuradas (incluindo MCP tools).
        
        Args:
            template (ChatPromptTemplate, optional): Template personalizado. Se None, usa o padrão.
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        try:
            if not self.tools:
                raise ValueError("Nenhuma tool foi adicionada. As tools MCP deveriam ter sido carregadas automaticamente.")
            
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
    
    def invoke_mcp_tool_directly(self, tool_name: str, *args, **kwargs) -> str:
        """
        Executa uma tool MCP diretamente, sem usar o agente.
        
        Args:
            tool_name (str): Nome da tool MCP
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            str: Resultado da tool
        """
        return self.conversation.invoke_mcp_tool(tool_name, *args, **kwargs)
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """
        Retorna informações sobre todas as tools disponíveis (incluindo MCP).
        
        Returns:
            List[Dict]: Lista com informações das tools
        """
        tools_info = []
        for tool in self.tools:
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "type": type(tool).__name__,
                "is_mcp": tool.name in self.conversation.list_mcp_tools()
            })
        return tools_info
    
    def get_mcp_tools_info(self) -> Dict[str, Any]:
        """
        Retorna informações específicas sobre as tools MCP.
        
        Returns:
            Dict[str, Any]: Informações das tools MCP
        """
        return self.conversation.get_mcp_tool_info()
    
    def list_mcp_tools(self) -> List[str]:
        """
        Lista apenas as tools MCP disponíveis.
        
        Returns:
            List[str]: Lista com nomes das tools MCP
        """
        return self.conversation.list_mcp_tools()
    
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
        Retorna informações sobre o agente MCP atual.
        
        Returns:
            Dict[str, Any]: Informações do agente
        """
        conversation_info = self.conversation.get_conversation_info()
        conversation_info.update({
            'class_type': 'MCPLangChainAgent',
            'total_tools': len(self.tools),
            'mcp_tools_count': len(self.conversation.list_mcp_tools()),
            'available_tools': self.get_available_tools(),
            'mcp_tools_info': self.get_mcp_tools_info(),
            'agent_created': self.agent is not None,
            'agent_executor_created': self.agent_executor is not None,
            'agent_features': [
                'mcp_tool_calling',
                'multi_step_reasoning',
                'context_preservation',
                'error_handling',
                'modular_tools'
            ]
        })
        return conversation_info
    
    def export_agent_state(self) -> Dict[str, Any]:
        """
        Exporta o estado completo do agente MCP para backup/análise.
        
        Returns:
            Dict[str, Any]: Estado do agente
        """
        return {
            'agent_info': self.get_agent_info(),
            'conversation_history': self.get_conversation_history(),
            'tools_info': self.get_available_tools(),
            'mcp_tools_info': self.get_mcp_tools_info(),
            'timestamp': str(os.popen('date').read().strip()) if os.name != 'nt' else str(os.popen('echo %date% %time%').read().strip())
        }
    
    def create_mcp_tool_from_function(self, name: str, description: str, func: Callable) -> bool:
        """
        Cria e registra uma tool MCP a partir de uma função Python.
        
        Args:
            name (str): Nome da tool
            description (str): Descrição da tool
            func (Callable): Função que implementa a tool
            
        Returns:
            bool: True se a operação foi bem-sucedida
        """
        def mcp_wrapper(*args, **kwargs):
            """Wrapper para funções MCP que garantem retorno em JSON."""
            try:
                result = func(*args, **kwargs)
                if isinstance(result, str):
                    return result
                else:
                    import json
                    return json.dumps({
                        "tipo_resposta": "funcao_customizada",
                        "resultado": result,
                        "resumo": f"Resultado da função {name}"
                    }, ensure_ascii=False, indent=2)
            except Exception as e:
                import json
                return json.dumps({
                    "erro": f"Erro na execução da função {name}",
                    "detalhes": str(e)
                }, ensure_ascii=False, indent=2)
        
        return self.register_mcp_tool(name, description, mcp_wrapper)
