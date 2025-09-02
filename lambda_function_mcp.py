"""
Exemplo de função handler usando sistema LangChain refatorado com MCP (Model Context Protocol)
Estrutura similar ao lambda_function.py para comparação de melhores práticas
Versão simplificada usando MCPLangChainWorkflow + MCPLangChainCore
"""
import os
import json
import logging
from dotenv import load_dotenv

# Import service classes para MCP Handler Function - SIMPLIFIED ARCHITECTURE
from services.mcp_langchain_core import MCPLangChainCore
from controller.mcp_langchain_workflow import MCPLangChainWorkflow
from services.polly_services import TTSPollyService

# Import utilities
from utils.response_processor import ResponseProcessor, process_response 

# Import template classes for LLM
from templates.prompt_template import PromptTemplate
from templates.template_test_tools import PromptTemplate as TriviaPromptTemplate

load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get temporary directory from .env file
TMP_DIR = os.getenv('TMP_DIR', './tmp')

# ============================================================================
# MCP Handler Function for Bedrock model inference using LangChain + MCP
# ----------------------------------------------------------------------------
def lambda_handler(event, context=None):
    """
    MCP Handler Function for Bedrock model inference using simplified LangChain + MCP architecture.
    
    Uses MCPLangChainWorkflow (controller) which integrates MCPLangChainCore for
    streamlined MCP agent execution with automatic tool discovery and loading.
    
    Args:
        event: Event containing user query and parameters
        context: Handler context (similar to Lambda context)
        
    Returns:
        dict: Response with status and processed data
    """
    
    # 1 - Print received event and start processing
    print('*********** Start MCP Handler - AI Assistant with LangChain + MCP ***************') 
    print(f'[DEBUG] Event: {event}') 

    # 2 - Ensure temporary directory exists
    os.makedirs(TMP_DIR, exist_ok=True)
    print(f'[DEBUG] Temporary directory configured: {TMP_DIR}')
   
    try:
        # 3 - Extract event parameters
        user_query = event.get('query', '')
        conversation_history = event.get('history', [])
        
        # 4 - Validate user query
        if not user_query:
            raise ValueError("User query is required")
        print(f'[DEBUG] User Query: {user_query}')
        print(f'[DEBUG] History length: {len(conversation_history)}')

        # 5 - Define template for LLM
        prompt_template = TriviaPromptTemplate(user_query=user_query).get_prompt_text()
        print(f'[DEBUG] Prompt Template: {prompt_template[:100]}...')

        # 6 - Initialize Bedrock MCP workflow with LangChain (simplified architecture)
        bedrock_mcp_service = MCPLangChainWorkflow(auto_load_mcp=True)
        
        # 7 - MCP tools are automatically loaded by MCPLangChainWorkflow
        mcp_tools_info = bedrock_mcp_service.get_mcp_tools_info()
        print(f'[DEBUG] MCP Tools automatically loaded: {len(mcp_tools_info)}')
        print(f'[DEBUG] Available MCP tools: {[tool["name"] for tool in mcp_tools_info]}')
        
        # 8 - Create agent template according to prompt
        bedrock_mcp_service.create_agent_template(prompt_template)
        
        # 9 - Create agent with MCP tools
        if not bedrock_mcp_service.create_agent():
            raise ValueError("Failed to create MCP agent with tools")
        print(f'[DEBUG] Model ID: {bedrock_mcp_service.model_id}')
        print(f'[DEBUG] Total tools available: {len(bedrock_mcp_service.get_available_tools())}')
                
        # 10 - Load conversation history if provided
        if conversation_history:
            bedrock_mcp_service.load_conversation_history(conversation_history)
            print(f'[DEBUG] History loaded: {len(conversation_history)} messages')
        
        # 11 - Perform inference using MCP agent
        response = bedrock_mcp_service.invoke_agent(user_query)
        print(f'[DEBUG] Bedrock MCP response: {response}') 

        # 12 - Process agent response using utility
        response_json = process_response(response)

        # 13 - Get updated conversation history
        updated_history = bedrock_mcp_service.get_conversation_history()

        # 14 - Get optional TTS parameters with default values
        voice_id = event.get('voice_id', 'Joanna')
        output_format = event.get('output_format', 'mp3')
        speed = event.get('speed', 'medium')
        use_neural = event.get('use_neural', True)
        
        print(f'[DEBUG] TTS parameters configured:')
        print(f'        - Voice ID: {voice_id}')
        print(f'        - Format: {output_format}')
        print(f'        - Speed: {speed}')
        print(f'        - Neural Engine: {use_neural}')

        # 15 - Initialize TTS service with custom temporary directory
        tts_service = TTSPollyService(output_dir=TMP_DIR)
        print(f'[DEBUG] TTS service successfully initialized')

        # 16 - Extract text for TTS from response
        tts_text = response_json.get('resposta', response_json.get('message', 'No response available'))

        # 17 - Convert text to speech
        audio_result = tts_service.text_to_speech(
            text=tts_text,
            voice_id=voice_id,
            output_format=output_format,
            speed=speed,
            use_neural=use_neural
        )
        
        # 18 - Check if conversion was successful
        if not audio_result['success']:
            raise Exception(f"TTS conversion error: {audio_result['error']}")
        
        print(f'[DEBUG] TTS conversion completed successfully:')
        print(f'        - File: {audio_result["filename"]}')
        print(f'        - Size: {audio_result["file_size_mb"]} MB')
        print(f'        - Duration: {audio_result["duration"]} seconds')
        print(f'        - Processing time: {audio_result["processing_time"]} seconds')

        # 19 - Prepare MCP Handler response with enhanced information
        return {
            'statusCode': 200,
            'body': {
                'message': 'Query processed successfully by simplified MCP workflow.',
                'response': response_json,
                'model_used': bedrock_mcp_service.model_id,
                'mcp_tools_used': [tool["name"] for tool in mcp_tools_info],
                'total_tools': len(bedrock_mcp_service.get_available_tools()),
                'mcp_tools_count': len(mcp_tools_info),
                'custom_tools_count': len(bedrock_mcp_service.tools) - len(bedrock_mcp_service.mcp_tools),
                'history': updated_history,
                'history_length': len(updated_history),
                'audio_file': audio_result['filename'],
                'audio_duration': audio_result['duration'],
                'architecture': 'MCPLangChainWorkflow + MCPLangChainCore',
                'framework': 'LangChain + MCP (Simplified)'
            },
        }
    
    except Exception as e:
        logger.error(f'[ERROR] {e}')
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Error processing user query with MCP'
            }
        }

# ============================================================================
# Main execution
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 MCP Handler Function Demo - Simplified Architecture")
    print("Architecture: MCPLangChainWorkflow + MCPLangChainCore")
    print("=" * 70)
    
    try:
        # Define test queries
        test_queries = [
            "How many times does the letter 'e' appear in the word 'elephant'?",
            "Hello! How are you?",
            "Count how many words are in the sentence 'The cat climbed on the roof'",
            "Calculate 25 multiplied by 8"
        ]
        
        test_descriptions = [
            "Character counting (simplified MCP workflow)",
            "Simple question (tests MCPLangChainCore integration)", 
            "Word counting (tests MCP workflow orchestration)",
            "Math calculation (tests MCP auto-discovery)"
        ]
        
        print("=== 🎮 Testing Simplified MCP Architecture ===")
        print("Architecture: MCPLangChainWorkflow (controller) + MCPLangChainCore (services)")
        
        # Execute tests
        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: {test_descriptions[i-1]}")
            
            test_event = {
                "query": query,
                "history": []
            }
            
            response = lambda_handler(test_event, None)
            
            if response['statusCode'] == 200:
                print(f"✅ Success!")
                print(f"🏗️  Architecture: {response['body']['architecture']}")
                print(f"🔧 MCP Tools: {response['body']['mcp_tools_used']}")
                print(f"📊 Total tools: {response['body']['total_tools']}")
                if i == 1:
                    print(f"🎯 MCP tools count: {response['body']['mcp_tools_count']}")
                elif i == 4:
                    print(f"📊 Response: {response['body']['response']}")
            else:
                print(f"❌ Error: {response['body']['error']}")
            
            if i < len(test_queries):
                print("\n" + "-"*60)
        
        print("\n🎉 All MCP tests completed with simplified architecture!")
        
    except Exception as e:
        logger.error(f"Erro durante a execução do demo: {e}")
        print(f"\n❌ Erro: {e}")
