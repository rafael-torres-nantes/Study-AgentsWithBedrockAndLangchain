import os
import json
import logging

# Import service classes para MCP Handler Function - SIMPLIFIED ARCHITECTURE
from services.mcp_langchain_core import MCPLangChainCore
from controller.mcp_langchain_workflow import MCPLangChainWorkflow
from services.polly_services import TTSPollyService

# Import utilities
from utils.response_processor import ResponseProcessor, process_response, extract_clean_response 

# Import template classes for LLM
from templates.prompt_template import PromptTemplate
from templates.template_test_tools import PromptTemplate as TriviaPromptTemplate

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from dotenv import load_dotenv
load_dotenv()

# Get AWS region from environment variables (Lambda runtime provides this)
AWS_REGION = os.getenv('AWS_REGION', 'us-east-2')

# Get temporary directory from .env file
TMP_DIR = os.getenv('TMP_DIR', '/tmp/')

# ============================================================================
# MCP Handler Function for Bedrock model inference using LangChain + MCP
# ----------------------------------------------------------------------------
def lambda_handler(event, context=None):
    """
    MCP Handler Function for Bedrock model inference using simplified LangChain + MCP architecture.
    
    Uses MCPLangChainWorkflow (controller) which integrates MCPLangChainCore for
    streamlined MCP agent execution with automatic tool discovery and loading.
    
    Supports both direct invocation and API Gateway events.
    
    Args:
        event: Event containing user query and parameters (direct or API Gateway format)
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
        # 3 - Parse event based on source (API Gateway or direct invocation)
        if 'httpMethod' in event:
            # API Gateway event
            print('[DEBUG] Detected API Gateway event')
            
            # Handle health check
            if event.get('path') == '/health' and event.get('httpMethod') == 'GET':
                return {
                    'statusCode': 200,
                    'headers': {
                        'Content-Type': 'application/json',
                        'Access-Control-Allow-Origin': '*',
                        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                    },
                    'body': json.dumps({
                        'status': 'healthy',
                        'message': 'AI Virtual Assistant is running',
                        'timestamp': context.aws_request_id if context else 'local-test'
                    })
                }
            
            # Parse JSON body for assistant endpoint
            if event.get('body'):
                try:
                    body = json.loads(event['body'])
                except json.JSONDecodeError:
                    raise ValueError("Invalid JSON in request body")
            else:
                raise ValueError("Request body is required")
                
            user_query = body.get('query', '')
            conversation_history = body.get('history', [])
            voice_id = body.get('voice_id', 'Joanna')
            output_format = body.get('output_format', 'mp3')
            speed = body.get('speed', 'medium')
            use_neural = body.get('use_neural', True)
            
        else:
            # Direct invocation event
            print('[DEBUG] Detected direct invocation event')
            user_query = event.get('query', '')
            conversation_history = event.get('history', [])
            voice_id = event.get('voice_id', 'Joanna')
            output_format = event.get('output_format', 'mp3')
            speed = event.get('speed', 'medium')
            use_neural = event.get('use_neural', True)
        
        # 4 - Validate user query
        if not user_query:
            raise ValueError("User query is required")
        print(f'[DEBUG] User Query: {user_query}')
        print(f'[DEBUG] History length: {len(conversation_history)}')

        # 5 - Define template for LLM
        prompt_template = TriviaPromptTemplate(user_query=user_query).get_prompt_text()
        print(f'[DEBUG] Prompt Template: {prompt_template[:100]}...')

        # 6 - Initialize Bedrock MCP workflow with LangChain (simplified architecture)
        print(f'[DEBUG] Using AWS region: {AWS_REGION}')
        bedrock_mcp_service = MCPLangChainWorkflow(region=AWS_REGION, auto_load_mcp=True)
        
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
        
        # 12 - Process agent response using utility
        response_json = process_response(response)
        
        # 13 - Display clean output response
        clean_output = extract_clean_response(response_json)
        print(f'[DEBUG] Clean output response:')
        print(f'{clean_output}')

        # 14 - Get updated conversation history
        updated_history = bedrock_mcp_service.get_conversation_history()

        # 15 - Get optional TTS parameters (already parsed above)
        print(f'[DEBUG] TTS parameters configured:')
        print(f'        - Voice ID: {voice_id}')
        print(f'        - Format: {output_format}')
        print(f'        - Speed: {speed}')
        print(f'        - Neural Engine: {use_neural}')

        # 16 - Initialize TTS service with custom temporary directory and correct region
        tts_service = TTSPollyService(region_name='us-east-1', output_dir=TMP_DIR)
        print(f'[DEBUG] TTS service successfully initialized for region: US-EAST-1')

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

        # 19 - Prepare response based on event source
        response_body = {
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
            'audio_duration': audio_result['duration']
        }

        # Return appropriate format based on event source
        if 'httpMethod' in event:
            # API Gateway response format
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps(response_body)
            }
        else:
            # Direct invocation response format
            return {
                'statusCode': 200,
                'body': response_body
            }
    
    except Exception as e:
        logger.error(f'[ERROR] {e}')
        
        error_response = {
            'error': str(e),
            'message': 'Error processing user query with MCP'
        }
        
        if 'httpMethod' in event:
            # API Gateway error response
            return {
                'statusCode': 500,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
                    'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
                },
                'body': json.dumps(error_response)
            }
        else:
            # Direct invocation error response
            return {
                'statusCode': 500,
                'body': error_response
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
            "Qual o endereço do CEP 79081-120?",
            "How many times does the letter 'e' appear in the word 'elephant'?",
            "Hello! How are you?",
            "Count how many words are in the sentence 'The cat climbed on the roof'",
            "Calculate 25 multiplied by 8"
        ]
        
        test_descriptions = [
            "Character counting (simplified MCP workflow)",
            "Simple question (tests MCPLangChainCore integration)", 
            "Word counting (tests MCP workflow orchestration)",
            "Math calculation (tests MCP auto-discovery)",
            "Math calculation (tests calculadora_basica tool)"
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
