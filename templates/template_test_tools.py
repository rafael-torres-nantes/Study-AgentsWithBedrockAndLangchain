import os
import json
import pandas as pd

class PromptTemplate:
    """
    Classe para gerar template de prompt para o iShopMeta AI Assistant.
    Sistema de assistente inteligente para descoberta personalizada de produtos, 
    filtragem de marcas e suporte ao usuário através de interação por texto.
    """

    def __init__(self, user_query, context_data=None):
        """
        Inicializa a classe com a query do usuário e dados de contexto.
        
        Args:
            user_query (str): Query/pergunta do usuário sobre produtos ou marcas.
            user_id (str): ID único do usuário para personalização.
            context_data (dict, optional): Dados adicionais de contexto do usuário.
        """
        self.user_query = user_query
        self.context_data = context_data if context_data is not None else {}
        
        # Cria o template do prompt
        self.create_prompt_template()

    def create_prompt_template(self):
        """
        Gera o prompt para o iShopMeta AI Assistant baseado nos requisitos do projeto.
        
        Returns:
            str: O prompt formatado para o assistente de compras.
        """
        self.prompt = f"""
        <context>
            Você é um assistente de chat inteligente e útil, capaz de ajudar os usuários com diversas tarefas 
            cotidianas. Você tem múltiplas funcionalidades para auxiliar em diferentes necessidades, desde 
            contagem de caracteres até análises de texto e outras utilidades.
            
            Seu papel é fornecer ajuda rápida, precisa e amigável para qualquer solicitação do usuário.
        </context>

        <suas_funcionalidades>
            - Contar caracteres, palavras e linhas em textos
            - Análise de texto (maiúsculas, minúsculas, números, símbolos)
            - Conversão de texto (maiúscula/minúscula, capitalização)
            - Cálculos matemáticos básicos e avançados
            - Formatação de texto e dados
            - Tradução entre idiomas
            - Geração de resumos e explicações
            - Responder perguntas gerais
            - Ajuda com programação e código
            - Organização de informações
        </suas_funcionalidades>

        <diretrizes_de_interacao>
            1. Seja sempre prestativo e educado
            2. Forneça respostas claras e precisas
            3. Quando contar caracteres, seja específico (com/sem espaços)
            4. Ofereça informações adicionais quando relevante
            5. Use formatação clara para facilitar a leitura
            6. Pergunte esclarecimentos se a solicitação for ambígua
            7. Mantenha um tom amigável e profissional
            8. Forneça exemplos quando apropriado
        </diretrizes_de_interacao>

        <formato_resposta>
            Forneça respostas em formato JSON com a seguinte estrutura:
            {{{{
            "tipo_resposta": "contagem|calculo|formatacao|informacao|ajuda",
            "resultado": "O resultado principal da solicitação",
            "detalhes": "Informações adicionais ou breakdown detalhado",
            "sugestoes": ["sugestão1", "sugestão2"] (se aplicável),
            "exemplo": "Exemplo prático se necessário"
            }}}}
        </formato_resposta>

        <sessao_atual>
            Consulta do Usuário: "{self.user_query}"
            Contexto Anterior: {json.dumps(self.context_data, indent=2) if self.context_data else "Nova conversa iniciada"}
        </sessao_atual>

        <instrucoes>
            Analise a solicitação do usuário e forneça a ajuda apropriada:
            
            1. Se for uma solicitação de contagem de caracteres:
               - Conte os caracteres exatos (incluindo e excluindo espaços)
               - Forneça também contagem de palavras se relevante
               - Mencione caracteres especiais se houver
            
            2. Para outras tarefas:
               - Identifique o tipo de ajuda necessária
               - Execute a tarefa solicitada
               - Forneça informações complementares úteis
            
            3. Se a solicitação não for clara:
               - Peça esclarecimentos de forma educada
               - Sugira possíveis interpretações
            
            Seja eficiente, preciso e sempre disposto a ajudar! 🤖
        </instrucoes>
        """

        return self.prompt
    
    def get_prompt_text(self):
        """
        Retorna o texto do prompt formatado para o iShopMeta AI Assistant.
        
        Returns:
            str: O prompt completo formatado.
        """
        return self.prompt

    def add_context_data(self, key, value):
        """
        Adiciona dados de contexto adicionais para personalização.
        
        Args:
            key (str): Chave do dado de contexto.
            value: Valor do dado de contexto.
        """
        self.context_data[key] = value
        # Recriar o prompt com os novos dados de contexto
        self.create_prompt_template()

    def update_user_query(self, new_query):
        """
        Atualiza a query do usuário e recria o prompt.
        
        Args:
            new_query (str): Nova query do usuário.
        """
        self.user_query = new_query
        self.create_prompt_template()