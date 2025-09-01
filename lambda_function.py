import os
import json
from dotenv import load_dotenv

# Importar as classes de serviços necessárias para a Lambda Function
from services.langchain_agent import LangChainAgent

# Importar tools da pasta tools/ (sem usar __init__.py)
from tools.tool_loader import get_all_tools

# Importar utilitários
from utils import process_response

# Importar a classes de templates para a llm
from templates.prompt_template import PromptTemplate
from templates.template_test_tools import PromptTemplate as TriviaPromptTemplate

load_dotenv()

# ============================================================================
# Função Lambda para inferência de modelos no Bedrock usando LangChain
# ----------------------------------------------------------------------------
def lambda_handler(event, context):
    """
    Lambda Function para inferência de modelos no Bedrock usando LangChain
    
    Args:
        event: Evento contendo a query do usuário e parâmetros
        context: Contexto da Lambda
        
    Returns:
        dict: Resposta com status e dados processados
    """
    
    print('*********** Start Lambda - AI Assistant with LangChain ***************') 
    print(f'[DEBUG] Event: {event}') 
   
    try:
        # 1 - Obtém parâmetros do evento
        user_query = event.get('query', '')
        conversation_history = event.get('history', [])
        
        # 2 - Validação
        if not user_query:
            raise ValueError("Query do usuário é obrigatória")

        print(f'[DEBUG] User Query: {user_query}')
        print(f'[DEBUG] History length: {len(conversation_history)}')

        # 3 - Define o template para a llm
        prompt_template = TriviaPromptTemplate(user_query=user_query).get_prompt_text()
        print(f'[DEBUG] Prompt Template: {prompt_template[:200]}...')

        # 4 - Inicializa o agente
        bedrock_service = LangChainAgent()
        
        # 5 - Adiciona todas as tools disponíveis da pasta tools/
        available_tools = get_all_tools()
        for tool_func in available_tools:
            bedrock_service.add_tool(tool_func)
        
        # Cria template para agente
        bedrock_service.create_agent_template(prompt_template)
        
        # Cria o agente
        if not bedrock_service.create_agent():
            raise ValueError("Falha ao criar agente com tools")
        
        print(f'[DEBUG] Model ID: {bedrock_service.model_id}')
        print(f'[DEBUG] Tools disponíveis: {[tool.name for tool in bedrock_service.tools]}')
                
        # 6 - Carrega histórico se fornecido
        if conversation_history:
            bedrock_service.load_conversation_history(conversation_history)
            print(f'[DEBUG] Histórico carregado: {len(conversation_history)} mensagens')
        
        # 7 - Realiza a inferência usando o agente
        response = bedrock_service.invoke_agent(user_query)
        print(f'[DEBUG] Resposta do Bedrock: {response}') 

        # 8 - Processa resposta do agente usando utilitário
        response_json = process_response(response)

        # 9 - Obtém histórico atualizado
        updated_history = bedrock_service.get_conversation_history()

        # 10 - Prepara a resposta da Lambda
        return {
            'statusCode': 200,
            'body': {
                'message': 'Query processada com sucesso pelo agente.',
                'response': response_json,
                'model_used': bedrock_service.model_id,
                'tools_used': [tool.name for tool in bedrock_service.tools],
                'history': updated_history,
                'history_length': len(updated_history)
            },
        }
    
    except Exception as e:
        print(f'[ERROR] {e}')
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Erro ao processar query do usuário'
            }
        }

# Testes da função lambda_handler
if __name__ == "__main__":

    print("=== 🎮 Teste das Tools Modularizadas ===")

    # Teste 1: Contagem de caracteres
    test_event_1 = {
        "query": "Quantas vezes a letra 'e' aparece na palavra 'elefante'?",
        "history": []
    }
    
    print("📝 Teste 1: Contagem de caracteres")
    response1 = lambda_handler(test_event_1, None)
    if response1['statusCode'] == 200:
        print(f"✅ Sucesso!")
        print(f"🔧 Tools usadas: {response1['body']['tools_used']}")
    else:
        print(f"❌ Erro: {response1['body']['error']}")
    
    print("\n" + "-"*60 + "\n")
    
    # Teste 2: Pergunta que não precisa de tool
    test_event_2 = {
        "query": "Olá! Como você está?",
        "history": []
    }
    
    print("� Teste 2: Pergunta simples (sem tool)")
    response2 = lambda_handler(test_event_2, None)
    if response2['statusCode'] == 200:
        print(f"✅ Sucesso!")
        print(f"🔧 Tools usadas: {response2['body']['tools_used']}")
    else:
        print(f"❌ Erro: {response2['body']['error']}")
    
    print("\n" + "-"*60 + "\n")
    
    # Teste 3: Análise mais complexa
    test_event_3 = {
        "query": "Conte quantas palavras tem na frase 'O gato subiu no telhado'",
        "history": []
    }
    
    print("📝 Teste 3: Contagem de palavras")
    response3 = lambda_handler(test_event_3, None)
    if response3['statusCode'] == 200:
        print(f"✅ Sucesso!")
        print(f"🔧 Tools usadas: {response3['body']['tools_used']}")
    else:
        print(f"❌ Erro: {response3['body']['error']}")
    
    print("\n🎉 Todos os testes concluídos!")