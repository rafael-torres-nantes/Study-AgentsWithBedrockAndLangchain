import os
import logging
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool, tool
from typing import List, Dict, Optional, Any, Callable
from services.mcp_langchain_core import MCPLangChainCore


class MCPLangChainWorkflow:
    """
    Controlador de workflow MCP para agentes LangChain com Amazon Bedrock.
    
    Esta classe gerencia agentes inteligentes com MCP tools, orquestrando
    workflows complexos e fornecendo uma interface simplificada para
    automação de tarefas multi-step com Model Context Protocol integration.
    
    Funcionalidades principais:
    - Integração automática com MCP tools server
    - Criação e gerenciamento de tools MCP e customizadas
    - Execução de agentes com capacidade de usar ferramentas MCP
    - Workflows de múltiplas etapas com contexto preservado
    - Auto-discovery de MCP tools disponíveis
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True,
                 auto_load_mcp: bool = True):
        """
        Inicializa o controlador de workflow MCP LangChain.
        
        Args:
            model_id: ID do modelo Bedrock (usa env BEDROCK_MODEL_ID se None)
            region: Região AWS para Bedrock (padrão: us-east-1)
            temperature: Controla criatividade (0.0-1.0, padrão: 0.0)
            max_tokens: Limite máximo de tokens na resposta
            top_p: Nucleus sampling parameter (0.0-1.0)
            load_env: Carrega variáveis de ambiente automaticamente
            auto_load_mcp: Carrega automaticamente MCP tools do server
        """
        # Inicializa o core MCP LangChain
        self.core = MCPLangChainCore(
            model_id=model_id, region=region, temperature=temperature,
            max_tokens=max_tokens, top_p=top_p, load_env=load_env
        )
        
        # Lista de tools e agente
        self.tools: List[BaseTool] = []
        self.mcp_tools: List[BaseTool] = []
        self.agent = None
        self.agent_executor = None
        self.agent_template = None
        
        # Logger
        self.logger = logging.getLogger(__name__)
        
        # Auto-carrega MCP tools se solicitado
        if auto_load_mcp:
            self._auto_load_mcp_tools()
    
    @property
    def model_id(self):
        """Retorna o model_id do core."""
        return self.core.model_id
    
    @property
    def llm(self):
        """Retorna o modelo LLM do core."""
        return self.core.llm
    
    # ===============================
    # MCP TOOLS MANAGEMENT - Automatic discovery and loading
    # ===============================
    
    def _auto_load_mcp_tools(self) -> int:
        """Carrega automaticamente MCP tools do server."""
        try:
            mcp_tools = self._discover_mcp_tools()
            loaded_count = 0
            for tool in mcp_tools:
                if self.register_mcp_tool(tool):
                    loaded_count += 1
            self.logger.info(f"Auto-carregadas {loaded_count} MCP tools")
            return loaded_count
        except Exception as e:
            self.logger.warning(f"Erro ao auto-carregar MCP tools: {e}")
            return 0
    
    def _discover_mcp_tools(self) -> List[BaseTool]:
        """
        Descobre MCP tools disponíveis no server usando módulo de discovery otimizado.
        
        Returns:
            List[BaseTool]: Lista de tools descobertas (MCP + fallback se necessário)
        """
        try:
            from tools.tool_wrappers import get_tool_discovery
            
            # Usa o sistema de discovery otimizado
            discovery = get_tool_discovery()
            tools = discovery.discover_all_tools()
            
            if tools:
                self.logger.info(f"Sistema de discovery carregou {len(tools)} tools com sucesso")
            else:
                self.logger.warning("Nenhuma tool foi descoberta pelo sistema")
            
            return tools
            
        except Exception as e:
            self.logger.error(f"Erro no sistema de discovery: {e}")
            return self._fallback_manual_discovery()
    
    def register_mcp_tool(self, tool: BaseTool) -> bool:
        """Registra uma MCP tool específica."""
        try:
            if tool not in self.mcp_tools:
                self.mcp_tools.append(tool)
                return self.add_tool(tool)
            return False
        except Exception as e:
            self.logger.error(f"Erro ao registrar MCP tool: {e}")
            return False
    
    def get_mcp_tools_info(self) -> List[Dict[str, str]]:
        """Retorna informações específicas sobre MCP tools carregadas."""
        return [{"name": tool.name, "description": tool.description, "type": "MCP Tool", "source": "MCP Server"} for tool in self.mcp_tools]
    
    # ===============================
    # GERENCIAMENTO DE TOOLS - Criação, adição e remoção de ferramentas
    # ===============================
    
    def create_custom_tool(self, name: str, description: str, func: Callable) -> BaseTool:
        """
        Cria uma tool customizada a partir de uma função Python.
        Permite transformar qualquer função em uma ferramenta que o agente pode usar.
        Complementa as MCP tools com funcionalidades específicas do domínio.
        """
        @tool(name=name, description=description)
        def custom_tool(input_text: str) -> str:
            return func(input_text)
        return custom_tool
    
    def add_tool(self, tool: BaseTool) -> bool:
        """
        Adiciona uma tool à lista de ferramentas do agente.
        Automaticamente recria o agente se ele já existir para incluir a nova tool.
        Funciona tanto para MCP tools quanto tools customizadas.
        """
        try:
            if tool not in self.tools:
                self.tools.append(tool)
                if self.agent is not None:
                    self._recreate_agent()
                return True
            else:
                self.logger.warning(f"Tool {tool.name} já existe")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao adicionar tool: {e}")
            return False
    
    def add_tools(self, tools: List[BaseTool]) -> int:
        """
        Adiciona múltiplas tools de uma vez.
        Mais eficiente que adicionar uma por uma. Funciona com mix de MCP e custom tools.
        """
        added_count = 0
        for tool in tools:
            if self.add_tool(tool):
                added_count += 1
        return added_count
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove uma tool da lista (MCP ou customizada)."""
        try:
            # Remove da lista geral
            for i, tool in enumerate(self.tools):
                if tool.name == tool_name:
                    self.tools.pop(i)
                    break
            
            # Remove da lista MCP se aplicável
            for i, tool in enumerate(self.mcp_tools):
                if tool.name == tool_name:
                    self.mcp_tools.pop(i)
                    break
            
            if self.agent is not None:
                self._recreate_agent()
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao remover tool: {e}")
            return False
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Retorna informações sobre todas as tools disponíveis (MCP + customizadas)."""
        return [{"name": tool.name, "description": tool.description, "type": type(tool).__name__} for tool in self.tools]
    
    # ===============================
    # CRIAÇÃO E EXECUÇÃO DE AGENTES - Core da funcionalidade de IA com MCP
    # ===============================
    
    def create_agent_template(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Cria template de prompt otimizado para agentes com MCP tools.
        Template inclui instruções específicas para uso eficiente de MCP tools.
        """
        # Adiciona contexto sobre MCP tools disponíveis ao prompt
        mcp_context = ""
        if self.mcp_tools:
            mcp_tools_list = [f"- {tool.name}: {tool.description}" for tool in self.mcp_tools]
            mcp_context = f"\n\nMCP Tools disponíveis:\n" + "\n".join(mcp_tools_list)
        
        enhanced_prompt = system_prompt + mcp_context
        
        self.agent_template = ChatPromptTemplate.from_messages([
            ("system", enhanced_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        return self.agent_template
    
    def create_agent(self, template: Optional[ChatPromptTemplate] = None) -> bool:
        """
        Cria o agente com as tools configuradas (MCP + customizadas).
        Otimizado para execução eficiente de MCP tools.
        """
        try:
            if not self.tools:
                raise ValueError("Nenhuma tool foi adicionada")
            
            current_template = template or self.agent_template
            if current_template is None:
                raise ValueError("Template de agente não foi definido")
            
            # Cria o agente
            self.agent = create_tool_calling_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=current_template
            )
            
            # Cria o executor com configurações otimizadas para MCP
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,  # Permite múltiplas chamadas MCP
                early_stopping_method="generate"
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
        Otimizado para execução eficiente de MCP tools com context preservation.
        """
        try:
            if self.agent_executor is None:
                raise ValueError("Agente não foi criado")
            
            # Prepara input para o agente
            agent_input = {
                "input": user_input,
                "chat_history": self.core.chat_history.messages if include_history else []
            }
            
            # Executa o agente
            result = self.agent_executor.invoke(agent_input)
            
            # Adiciona ao histórico se solicitado
            if include_history:
                self.core.chat_history.add_user_message(user_input)
                self.core.chat_history.add_ai_message(result["output"])
            
            return result["output"]
        except Exception as e:
            self.logger.error(f"Erro na execução do agente: {e}")
            raise
    
    # ===============================
    # WORKFLOWS MULTI-STEP - Orquestração com MCP tools
    # ===============================
    
    def execute_workflow(self, steps: List[Dict[str, Any]], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executa um workflow de múltiplas etapas com MCP tools.
        Suporta tipos de step: 'agent' (com MCP tools), 'simple', 'template', 'mcp_direct'.
        """
        workflow_context = context or {}
        results = []
        
        try:
            for i, step in enumerate(steps):
                step_type = step.get('type', 'agent')
                step_input = step.get('input', '')
                step_config = step.get('config', {})
                
                if step_type == 'agent':
                    result = self.invoke_agent(step_input, step_config.get('include_history', True))
                elif step_type == 'simple':
                    result = self.core.invoke_simple(step_input)
                elif step_type == 'template':
                    template = step_config.get('template')
                    if template:
                        result = self.core.invoke_with_template(template, **step_config.get('params', {}))
                    else:
                        raise ValueError(f"Template não fornecido para step {i+1}")
                elif step_type == 'mcp_direct':
                    # Execução direta de MCP tool específica
                    tool_name = step_config.get('tool_name')
                    result = self._execute_mcp_tool_direct(tool_name, step_input)
                else:
                    raise ValueError(f"Tipo de step desconhecido: {step_type}")
                
                results.append({
                    'step': i+1, 'type': step_type, 'input': step_input,
                    'output': result, 'success': True
                })
                workflow_context[f'step_{i+1}_result'] = result
            
            return {
                'success': True, 'results': results, 
                'context': workflow_context, 'total_steps': len(steps),
                'mcp_tools_used': len(self.mcp_tools)
            }
            
        except Exception as e:
            self.logger.error(f"Erro no workflow: {e}")
            return {
                'success': False, 'error': str(e), 'results': results,
                'context': workflow_context, 'failed_step': len(results) + 1
            }
    
    def _execute_mcp_tool_direct(self, tool_name: str, input_data: str) -> str:
        """Executa uma MCP tool específica diretamente."""
        for tool in self.mcp_tools:
            if tool.name == tool_name:
                return tool.invoke(input_data)
        raise ValueError(f"MCP tool '{tool_name}' não encontrada")
    
    # ===============================
    # ACESSO AO CORE E HISTÓRICO - Bridge para funcionalidades básicas
    # ===============================
    
    def clear_conversation_history(self) -> bool:
        """Limpa histórico de conversação. Útil para iniciar nova sessão MCP."""
        return self.core.clear_history()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retorna histórico formatado. Útil para análise ou backup de sessão MCP."""
        return self.core.get_history()
    
    def load_conversation_history(self, history: List[Dict[str, str]]) -> bool:
        """Carrega histórico salvo. Útil para restaurar sessões MCP."""
        return self.core.load_history(history)
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Retorna informações completas sobre o estado atual do workflow MCP.
        Inclui informações específicas sobre MCP tools e integração.
        """
        core_info = self.core.get_model_info()
        core_info.update({
            'class_type': 'MCPLangChainWorkflow',
            'mcp_integration': True,
            'tools_count': len(self.tools),
            'mcp_tools_count': len(self.mcp_tools),
            'available_tools': self.get_available_tools(),
            'mcp_tools': self.get_mcp_tools_info(),
            'agent_created': self.agent is not None,
            'agent_executor_created': self.agent_executor is not None,
            'workflow_features': ['mcp_integration', 'tool_calling', 'multi_step_workflows', 'context_preservation', 'error_handling', 'custom_tools', 'auto_discovery']
        })
        return core_info
    
    def export_workflow_state(self) -> Dict[str, Any]:
        """Exporta o estado completo do workflow MCP."""
        return {
            'workflow_info': self.get_workflow_info(),
            'conversation_history': self.get_conversation_history(),
            'tools_info': self.get_available_tools(),
            'mcp_tools_info': self.get_mcp_tools_info(),
            'core_session': self.core.export_session(),
            'mcp_status': self.core.get_mcp_status(),
            'timestamp': str(os.popen('echo %date% %time%').read().strip()) if os.name == 'nt' else str(os.popen('date').read().strip())
        }
    
    def _fallback_manual_discovery(self) -> List[BaseTool]:
        """
        Fallback manual para discovery de tools em caso de falha total do sistema otimizado.
        Método básico de emergência.
        
        Returns:
            List[BaseTool]: Lista básica de tools ou lista vazia
        """
        try:
            self.logger.warning("Usando fallback manual de descoberta de tools")
            
            # Tenta importação direta básica
            try:
                from tools.mcp_tools_server import contador_caracteres, analisar_texto
                from langchain_core.tools import tool
                
                @tool
                def emergency_counter(input_text: str) -> str:
                    """Emergency character counter"""
                    parts = input_text.split(",", 1)
                    if len(parts) == 2:
                        return contador_caracteres(parts[0], parts[1])
                    return "Formato: texto,caracter"
                
                @tool  
                def emergency_analyzer(input_text: str) -> str:
                    """Emergency text analyzer"""
                    return analisar_texto(input_text)
                
                emergency_counter.name = "contador_caracteres"
                emergency_analyzer.name = "analisar_texto"
                
                self.logger.info("Fallback manual carregou 2 tools básicas")
                return [emergency_counter, emergency_analyzer]
                
            except ImportError:
                self.logger.error("Fallback manual também falhou")
                return []
                
        except Exception as e:
            self.logger.error(f"Erro crítico no fallback manual: {e}")
            return []
