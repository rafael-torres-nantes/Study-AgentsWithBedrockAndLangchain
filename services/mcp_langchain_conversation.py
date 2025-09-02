"""
Classe LangChain Conversation refatorada para usar MCP (Model Context Protocol)
"""
import os
import json
import logging
from typing import List, Dict, Optional, Any
from dotenv import load_dotenv
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import tool
from services.langchain_inference import LangChainInference


class MCPLangChainConversation:
    """
    Classe para gerenciamento de conversação usando MCP (Model Context Protocol) com LangChain.
    
    Esta classe integra o padrão MCP para criar ferramentas e serviços de forma mais organizada,
    permitindo melhor modularização e reutilização de código.
    """
    
    def __init__(self, model_id: Optional[str] = None, region: str = 'us-east-1', 
                 temperature: float = 0.0, max_tokens: Optional[int] = None, 
                 top_p: Optional[float] = None, load_env: bool = True):
        """
        Inicializa a classe MCP de conversação do Bedrock.
        
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
        
        # Registro de tools MCP
        self.mcp_tools = {}
        
        # Inicializa as tools padrão do MCP (usando tools da pasta tools/)
        self._register_default_mcp_tools()
    
    def _register_default_mcp_tools(self):
        """Registra as tools padrão do MCP."""
        # Registra as tools usando o padrão MCP
        self.register_mcp_tool("contador_caracteres", self._contador_caracteres_tool)
        self.register_mcp_tool("analisar_texto", self._analisar_texto_tool)
        self.register_mcp_tool("calculadora_basica", self._calculadora_basica_tool)
        self.register_mcp_tool("analisar_sentimento", self._analisar_sentimento_tool)
        self.register_mcp_tool("extrair_emails", self._extrair_emails_tool)
    
    def register_mcp_tool(self, name: str, tool_func):
        """
        Registra uma nova tool no padrão MCP.
        
        Args:
            name (str): Nome da tool
            tool_func: Função que implementa a tool
        """
        self.mcp_tools[name] = tool_func
        self.logger.info(f"Tool MCP '{name}' registrada com sucesso")
    
    def get_mcp_tools(self) -> List:
        """
        Retorna todas as tools MCP registradas como tools LangChain.
        
        Returns:
            List: Lista de tools LangChain
        """
        from langchain_core.tools import StructuredTool
        
        langchain_tools = []
        
        for name, tool_func in self.mcp_tools.items():
            # Cria uma tool estruturada do LangChain
            langchain_tool = StructuredTool.from_function(
                func=tool_func,
                name=name,
                description=f"Tool MCP: {name}"
            )
            langchain_tools.append(langchain_tool)
        
        return langchain_tools
    
    def _contador_caracteres_tool(self, texto: str, caracter: str) -> str:
        """Tool MCP para contar caracteres."""
        try:
            if not texto or not caracter:
                return json.dumps({
                    "erro": "Texto e caracter são obrigatórios",
                    "texto_recebido": texto,
                    "caracter_recebido": caracter
                }, ensure_ascii=False, indent=2)
            
            count_exact = texto.count(caracter)
            count_upper = texto.count(caracter.upper()) 
            count_lower = texto.count(caracter.lower())
            total_case_insensitive = count_upper + count_lower
            
            resultado = {
                "tipo_resposta": "contagem_caracteres",
                "palavra_analisada": texto,
                "caracter_procurado": caracter,
                "resultados": {
                    "exato": count_exact,
                    "maiusculo": count_upper,
                    "minusculo": count_lower,
                    "total_case_insensitive": total_case_insensitive
                },
                "resumo": f"O caractere '{caracter}' aparece {count_exact} vez(es) de forma exata no texto '{texto}'"
            }
            
            return json.dumps(resultado, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erro na tool contador_caracteres: {e}")
            return json.dumps({
                "erro": "Erro ao processar contagem",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def _analisar_texto_tool(self, texto: str, tipo_analise: str = "contar_palavras") -> str:
        """Tool MCP para análise de texto."""
        try:
            if not texto:
                return json.dumps({
                    "erro": "Texto não fornecido"
                }, ensure_ascii=False, indent=2)
            
            if tipo_analise == "contar_palavras":
                palavras = len(texto.split())
                resultado = {
                    "tipo_resposta": "contagem_palavras",
                    "texto_analisado": texto,
                    "total_palavras": palavras,
                    "resumo": f"O texto '{texto}' tem {palavras} palavra(s)"
                }
            elif tipo_analise in ["maiuscula", "maiúscula"]:
                resultado = {
                    "tipo_resposta": "conversao_maiuscula",
                    "texto_original": texto,
                    "texto_convertido": texto.upper(),
                    "resumo": f"Texto convertido para maiúscula"
                }
            elif tipo_analise in ["minuscula", "minúscula", "converter_minusculas"]:
                resultado = {
                    "tipo_resposta": "conversao_minuscula", 
                    "texto_original": texto,
                    "texto_convertido": texto.lower(),
                    "resumo": f"Texto convertido para minúscula"
                }
            elif tipo_analise == "caracteres_total":
                total_chars = len(texto)
                chars_sem_espaco = len(texto.replace(" ", ""))
                resultado = {
                    "tipo_resposta": "contagem_caracteres_total",
                    "texto_analisado": texto,
                    "total_caracteres": total_chars,
                    "caracteres_sem_espaco": chars_sem_espaco,
                    "espacos": total_chars - chars_sem_espaco,
                    "resumo": f"O texto tem {total_chars} caracteres total ({chars_sem_espaco} sem espaços)"
                }
            else:
                resultado = {
                    "erro": f"Tipo de análise '{tipo_analise}' não suportado",
                    "tipos_suportados": ["contar_palavras", "maiuscula", "minuscula", "caracteres_total", "converter_minusculas"]
                }
            
            return json.dumps(resultado, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erro na tool analisar_texto: {e}")
            return json.dumps({
                "erro": "Erro na análise de texto",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def _calculadora_basica_tool(self, operacao: str, numero1: float, numero2: float) -> str:
        """Tool MCP para cálculos básicos."""
        try:
            if operacao == "+":
                resultado = numero1 + numero2
            elif operacao == "-":
                resultado = numero1 - numero2
            elif operacao == "*":
                resultado = numero1 * numero2
            elif operacao == "/":
                if numero2 == 0:
                    return json.dumps({
                        "erro": "Divisão por zero não é permitida",
                        "operacao": operacao,
                        "numero1": numero1,
                        "numero2": numero2
                    }, ensure_ascii=False, indent=2)
                resultado = numero1 / numero2
            else:
                return json.dumps({
                    "erro": f"Operação '{operacao}' não suportada",
                    "operacoes_suportadas": ["+", "-", "*", "/"]
                }, ensure_ascii=False, indent=2)
            
            resposta = {
                "tipo_resposta": "calculo_matematico",
                "operacao": operacao,
                "numero1": numero1,
                "numero2": numero2,
                "resultado": resultado,
                "resumo": f"{numero1} {operacao} {numero2} = {resultado}"
            }
            
            return json.dumps(resposta, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erro na tool calculadora_basica: {e}")
            return json.dumps({
                "erro": "Erro no cálculo",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def _analisar_sentimento_tool(self, texto: str) -> str:
        """Tool MCP para análise de sentimento."""
        try:
            if not texto:
                return json.dumps({
                    "erro": "Texto não fornecido"
                }, ensure_ascii=False, indent=2)
            
            palavras_positivas = ['bom', 'ótimo', 'excelente', 'maravilhoso', 'feliz', 'alegre', 'amor', 'sucesso', 'positivo']
            palavras_negativas = ['ruim', 'péssimo', 'terrível', 'horrível', 'triste', 'raiva', 'ódio', 'fracasso', 'negativo']
            
            texto_lower = texto.lower()
            score_positivo = sum(1 for palavra in palavras_positivas if palavra in texto_lower)
            score_negativo = sum(1 for palavra in palavras_negativas if palavra in texto_lower)
            
            if score_positivo > score_negativo:
                sentimento = "positivo"
            elif score_negativo > score_positivo:
                sentimento = "negativo"
            else:
                sentimento = "neutro"
            
            resultado = {
                "tipo_resposta": "analise_sentimento",
                "texto_analisado": texto,
                "sentimento": sentimento,
                "score_positivo": score_positivo,
                "score_negativo": score_negativo,
                "resumo": f"O texto tem sentimento {sentimento} (positivo: {score_positivo}, negativo: {score_negativo})"
            }
            
            return json.dumps(resultado, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erro na tool analisar_sentimento: {e}")
            return json.dumps({
                "erro": "Erro na análise de sentimento",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def _extrair_emails_tool(self, texto: str) -> str:
        """Tool MCP para extração de emails."""
        try:
            import re
            
            if not texto:
                return json.dumps({
                    "erro": "Texto não fornecido"
                }, ensure_ascii=False, indent=2)
            
            pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(pattern, texto)
            
            resultado = {
                "tipo_resposta": "extracao_emails",
                "texto_analisado": texto,
                "emails_encontrados": emails,
                "total_emails": len(emails),
                "resumo": f"Foram encontrados {len(emails)} email(s) no texto"
            }
            
            return json.dumps(resultado, ensure_ascii=False, indent=2)
            
        except Exception as e:
            self.logger.error(f"Erro na tool extrair_emails: {e}")
            return json.dumps({
                "erro": "Erro na extração de emails",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
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
            current_template = template or self.conversation_template
            
            if current_template is None:
                raise ValueError("Nenhum template de conversação foi definido. Use create_conversation_template() primeiro.")
            
            messages = current_template.format_messages(
                history=self.chat_history.messages,
                user_input=user_input
            )
            
            result = self.llm.invoke(messages)
            
            self.chat_history.add_user_message(user_input)
            self.chat_history.add_ai_message(result.content)
            
            return result.content
            
        except Exception as e:
            self.logger.error(f"Erro na invocação com histórico: {e}")
            raise
    
    def invoke_mcp_tool(self, tool_name: str, *args, **kwargs) -> str:
        """
        Invoca uma tool MCP específica.
        
        Args:
            tool_name (str): Nome da tool MCP
            *args: Argumentos posicionais
            **kwargs: Argumentos nomeados
            
        Returns:
            str: Resultado da tool
        """
        if tool_name not in self.mcp_tools:
            return json.dumps({
                "erro": f"Tool '{tool_name}' não encontrada",
                "tools_disponiveis": list(self.mcp_tools.keys())
            }, ensure_ascii=False, indent=2)
        
        try:
            return self.mcp_tools[tool_name](*args, **kwargs)
        except Exception as e:
            self.logger.error(f"Erro ao executar tool MCP '{tool_name}': {e}")
            return json.dumps({
                "erro": f"Erro ao executar tool '{tool_name}'",
                "detalhes": str(e)
            }, ensure_ascii=False, indent=2)
    
    def list_mcp_tools(self) -> List[str]:
        """
        Lista todas as tools MCP disponíveis.
        
        Returns:
            List[str]: Lista com nomes das tools
        """
        return list(self.mcp_tools.keys())
    
    def get_mcp_tool_info(self) -> Dict[str, Any]:
        """
        Retorna informações sobre as tools MCP registradas.
        
        Returns:
            Dict[str, Any]: Informações das tools MCP
        """
        return {
            "total_tools": len(self.mcp_tools),
            "tools_disponiveis": list(self.mcp_tools.keys()),
            "mcp_version": "1.0",
            "framework": "LangChain + MCP"
        }
    
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
    
    def get_conversation_info(self) -> Dict[str, Any]:
        """Retorna informações sobre a conversação atual."""
        model_info = self.inference.get_model_info()
        model_info.update({
            'class_type': 'MCPLangChainConversation',
            'history_length': len(self.chat_history.messages),
            'has_conversation_template': self.conversation_template is not None,
            'mcp_tools_info': self.get_mcp_tool_info(),
            'conversation_features': [
                'history_management',
                'multi_turn_conversation',
                'context_preservation',
                'mcp_tools_integration'
            ]
        })
        return model_info
