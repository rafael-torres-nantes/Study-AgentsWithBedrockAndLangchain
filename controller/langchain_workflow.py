import os
import logging
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool, tool
from typing import List, Dict, Optional, Any, Callable
from services.langchain_core import LangChainCore


class LangChainWorkflow:
    """
    Controlador de workflow para agentes LangChain com Amazon Bedrock.
    
    Esta classe gerencia agentes inteligentes com tools, orquestrando
    workflows complexos e fornecendo uma interface simplificada para
    automação de tarefas multi-step.
    
    Funcionalidades principais:
    - Criação e gerenciamento de tools customizadas
    - Execução de agentes com capacidade de usar ferramentas
    - Workflows de múltiplas etapas com contexto preservado
    - Integração com LangChainCore para funcionalidades básicas
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa o controlador de workflow LangChain.
        
        Args:
            model_id: ID do modelo Bedrock (usa env BEDROCK_MODEL_ID se None)
            region: Região AWS para Bedrock (padrão: us-east-1)
            temperature: Controla criatividade (0.0-1.0, padrão: 0.0)
            max_tokens: Limite máximo de tokens na resposta
            top_p: Nucleus sampling parameter (0.0-1.0)
            load_env: Carrega variáveis de ambiente automaticamente
        """
        # Inicializa o core LangChain
        self.core = LangChainCore(
            model_id=model_id, region=region, temperature=temperature,
            max_tokens=max_tokens, top_p=top_p, load_env=load_env
        )
        
        # Lista de tools e agente
        self.tools: List[BaseTool] = []
        self.agent = None
        self.agent_executor = None
        self.agent_template = None
        
        # Logger
        self.logger = logging.getLogger(__name__)
    
    @property
    def model_id(self):
        """Retorna o model_id do core."""
        return self.core.model_id
    
    @property
    def llm(self):
        """Retorna o modelo LLM do core."""
        return self.core.llm
    
    # ===============================
    # GERENCIAMENTO DE TOOLS - Criação, adição e remoção de ferramentas
    # ===============================
    
    def create_custom_tool(self, name: str, description: str, func: Callable) -> BaseTool:
        """
        Cria uma tool customizada a partir de uma função Python.
        
        Permite transformar qualquer função em uma ferramenta que o agente pode usar.
        Útil para integrar funcionalidades específicas do seu domínio.
        """
        @tool(name=name, description=description)
        def custom_tool(input_text: str) -> str:
            return func(input_text)
        return custom_tool
    
    def add_tool(self, tool: BaseTool) -> bool:
        """
        Adiciona uma tool à lista de ferramentas do agente.
        
        Automaticamente recria o agente se ele já existir para incluir a nova tool.
        Retorna False se a tool já existir (evita duplicatas).
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
        
        Mais eficiente que adicionar uma por uma. Retorna o número de tools
        que foram efetivamente adicionadas (exclui duplicatas).
        """
        added_count = 0
        for tool in tools:
            if self.add_tool(tool):
                added_count += 1
        return added_count
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove uma tool da lista."""
        try:
            for i, tool in enumerate(self.tools):
                if tool.name == tool_name:
                    self.tools.pop(i)
                    if self.agent is not None:
                        self._recreate_agent()
                    return True
            self.logger.warning(f"Tool {tool_name} não encontrada")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao remover tool: {e}")
            return False
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Retorna informações sobre as tools disponíveis."""
        return [{"name": tool.name, "description": tool.description, "type": type(tool).__name__} for tool in self.tools]
    
    # ===============================
    # CRIAÇÃO E EXECUÇÃO DE AGENTES - Core da funcionalidade de IA
    # ===============================
    
    def create_agent_template(self, system_prompt: str) -> ChatPromptTemplate:
        """
        Cria template de prompt otimizado para agentes com tools.
        
        O template inclui placeholders para histórico e scratchpad (área de trabalho
        do agente para raciocínio). Essential para agentes que usam ferramentas.
        """
        self.agent_template = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        return self.agent_template
    
    def create_agent(self, template: Optional[ChatPromptTemplate] = None) -> bool:
        """
        Cria o agente com as tools configuradas.
        
        Combina o modelo LLM, tools e template em um agente executável.
        Requer pelo menos uma tool e um template. Retorna True se bem-sucedido.
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
            
            # Cria o executor
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
        
        O agente analisará a entrada, decidirá quais tools usar (se necessário),
        executará as tools e fornecerá uma resposta final. Mantém contexto
        conversacional se include_history=True.
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
    # WORKFLOWS MULTI-STEP - Orquestração de tarefas complexas
    # ===============================
    
    def execute_workflow(self, steps: List[Dict[str, Any]], context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Executa um workflow de múltiplas etapas com preservação de contexto.
        
        Suporta tipos de step: 'agent' (com tools), 'simple' (inferência direta),
        'template' (com template customizado). Cada step pode acessar resultados
        dos steps anteriores através do contexto.
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
                else:
                    raise ValueError(f"Tipo de step desconhecido: {step_type}")
                
                results.append({
                    'step': i+1, 'type': step_type, 'input': step_input,
                    'output': result, 'success': True
                })
                workflow_context[f'step_{i+1}_result'] = result
            
            return {
                'success': True, 'results': results, 
                'context': workflow_context, 'total_steps': len(steps)
            }
            
        except Exception as e:
            self.logger.error(f"Erro no workflow: {e}")
            return {
                'success': False, 'error': str(e), 'results': results,
                'context': workflow_context, 'failed_step': len(results) + 1
            }
    
    # ===============================
    # ACESSO AO CORE E HISTÓRICO - Bridge para funcionalidades básicas
    # ===============================
    
    def clear_conversation_history(self) -> bool:
        """Limpa histórico de conversação. Útil para iniciar nova sessão."""
        return self.core.clear_history()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Retorna histórico formatado. Útil para análise ou backup."""
        return self.core.get_history()
    
    def load_conversation_history(self, history: List[Dict[str, str]]) -> bool:
        """Carrega histórico salvo. Útil para restaurar sessões."""
        return self.core.load_history(history)
    
    def get_workflow_info(self) -> Dict[str, Any]:
        """
        Retorna informações completas sobre o estado atual do workflow.
        
        Inclui informações do modelo, tools carregadas, status do agente,
        e todas as capacidades disponíveis. Útil para debugging e monitoramento.
        """
        core_info = self.core.get_model_info()
        core_info.update({
            'class_type': 'LangChainWorkflow',
            'tools_count': len(self.tools),
            'available_tools': self.get_available_tools(),
            'agent_created': self.agent is not None,
            'agent_executor_created': self.agent_executor is not None,
            'workflow_features': ['tool_calling', 'multi_step_workflows', 'context_preservation', 'error_handling', 'custom_tools']
        })
        return core_info
    
    def export_workflow_state(self) -> Dict[str, Any]:
        """Exporta o estado completo do workflow."""
        return {
            'workflow_info': self.get_workflow_info(),
            'conversation_history': self.get_conversation_history(),
            'tools_info': self.get_available_tools(),
            'core_session': self.core.export_session(),
            'timestamp': str(os.popen('echo %date% %time%').read().strip()) if os.name == 'nt' else str(os.popen('date').read().strip())
        }
