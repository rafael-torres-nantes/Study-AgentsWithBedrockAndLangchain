import os
import json
from dotenv import load_dotenv

# Import service classes needed for Lambda Function
from services.langchain_core import LangChainCore
from controller.langchain_workflow import LangChainWorkflow
from services.polly_services import TTSPollyService

# Import tools from tools/ directory (without using __init__.py)
from tools.tool_loader import get_all_tools

# Import utilities
from utils.response_processor import ResponseProcessor, process_response 

# Import template classes for LLM
from templates.prompt_template import PromptTemplate
from templates.template_test_tools import PromptTemplate as TriviaPromptTemplate

load_dotenv()

# Get temporary directory from .env file
TMP_DIR = os.getenv('TMP_DIR', './tmp')

# ============================================================================
# Lambda Function for Bedrock model inference using LangChain
# ----------------------------------------------------------------------------
def lambda_handler(event, context):
    """
    Lambda Function for Bedrock model inference using simplified LangChain architecture.
    
    Uses the new LangChainWorkflow (controller) which integrates LangChainCore for
    streamlined agent execution with tools and conversation management.
    
    Args:
        event: Event containing user query and parameters
        context: Lambda context
        
    Returns:
        dict: Response with status and processed data
    """
    
    # 1 - Print received event and start processing
    print('*********** Start Lambda - AI Assistant with LangChain ***************') 
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

        # 6 - Initialize Bedrock workflow with LangChain (replaces old agent)
        bedrock_service = LangChainWorkflow()
        
        # 7 - Add all available tools from tools/ directory
        available_tools = get_all_tools()
        tools_added = bedrock_service.add_tools(available_tools)
        print(f'[DEBUG] Tools added: {tools_added}')
        
        # 8 - Create agent template according to prompt
        bedrock_service.create_agent_template(prompt_template)
        
        # 9 - Create agent with tools
        if not bedrock_service.create_agent():
            raise ValueError("Failed to create agent with tools")
        print(f'[DEBUG] Model ID: {bedrock_service.model_id}')
        print(f'[DEBUG] Available tools: {[tool.name for tool in bedrock_service.tools]}')
                
        # 10 - Load conversation history if provided
        if conversation_history:
            bedrock_service.load_conversation_history(conversation_history)
            print(f'[DEBUG] History loaded: {len(conversation_history)} messages')
        
        # 11 - Perform inference using agent
        response = bedrock_service.invoke_agent(user_query)
        print(f'[DEBUG] Bedrock response: {response}') 

        # 12 - Process agent response using utility
        response_json = process_response(response)

        # 13 - Get updated conversation history
        updated_history = bedrock_service.get_conversation_history()

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

        # 19 - Prepare Lambda response with enhanced information
        return {
            'statusCode': 200,
            'body': {
                'message': 'Query processed successfully by simplified workflow.',
                'response': response_json,
                'model_used': bedrock_service.model_id,
                'tools_used': [tool.name for tool in bedrock_service.tools],
                'tools_count': len(bedrock_service.tools),
                'history': updated_history,
                'history_length': len(updated_history),
                'audio_file': audio_result['filename'],
                'audio_duration': audio_result['duration'],
                'architecture': 'LangChainWorkflow + LangChainCore'
            },
        }
    
    except Exception as e:
        print(f'[ERROR] {e}')
        return {
            'statusCode': 500,
            'body': {
                'error': str(e),
                'message': 'Error processing user query'
            }
        }

# Tests for lambda_handler function
if __name__ == "__main__":

    print("=== 🎮 Testing Simplified LangChain Architecture ===")
    print("Architecture: LangChainWorkflow (controller) + LangChainCore (services)")

    # Test 1: Character counting with new architecture
    test_event_1 = {
        "query": "How many times does the letter 'e' appear in the word 'elephant'?",
        "history": []
    }
    
    print("\n📝 Test 1: Character counting (simplified workflow)")
    response1 = lambda_handler(test_event_1, None)
    if response1['statusCode'] == 200:
        print(f"✅ Success!")
        print(f"🏗️  Architecture: {response1['body']['architecture']}")
        print(f"🔧 Tools used: {response1['body']['tools_used']}")
        print(f"📊 Tools count: {response1['body']['tools_count']}")
    else:
        print(f"❌ Error: {response1['body']['error']}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 2: Simple question (no tools needed) - tests core inference
    test_event_2 = {
        "query": "Hello! How are you?",
        "history": []
    }
    
    print("📝 Test 2: Simple question (tests LangChainCore integration)")
    response2 = lambda_handler(test_event_2, None)
    if response2['statusCode'] == 200:
        print(f"✅ Success!")
        print(f"🏗️  Architecture: {response2['body']['architecture']}")
        print(f"🔧 Tools used: {response2['body']['tools_used']}")
    else:
        print(f"❌ Error: {response2['body']['error']}")
    
    print("\n" + "-"*60 + "\n")
    
    # Test 3: Complex analysis with workflow
    test_event_3 = {
        "query": "Count how many words are in the sentence 'The cat climbed on the roof'",
        "history": []
    }
    
    print("📝 Test 3: Word counting (tests workflow orchestration)")
    response3 = lambda_handler(test_event_3, None)
    if response3['statusCode'] == 200:
        print(f"✅ Success!")
        print(f"🏗️  Architecture: {response3['body']['architecture']}")
        print(f"🔧 Tools used: {response3['body']['tools_used']}")
        print(f"📈 History length: {response3['body']['history_length']}")
    else:
        print(f"❌ Error: {response3['body']['error']}")
    
    print("\n🎉 All tests completed with simplified architecture!")
    print("🔄 Compare with exemplo_mcp.py to see MCP vs traditional approaches")