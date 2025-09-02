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
                'audio_duration': audio_result['duration']
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

# ============================================================================
# Main execution
# ----------------------------------------------------------------------------
if __name__ == "__main__":
    print("🤖 Lambda Handler Function Demo - Simplified Architecture")
    print("Architecture: LangChainWorkflow + LangChainCore")
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
            "Character counting (simplified workflow)",
            "Simple question (tests LangChainCore integration)", 
            "Word counting (tests workflow orchestration)",
            "Math calculation (tests auto-discovery)"
        ]
        
        print("=== 🎮 Testing Simplified LangChain Architecture ===")
        print("Architecture: LangChainWorkflow (controller) + LangChainCore (services)")
        
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
                print(f"🔧 Tools used: {response['body']['tools_used']}")
                print(f"📊 Tools count: {response['body']['tools_count']}")
                if i == 1:
                    print(f"🎯 Model used: {response['body']['model_used']}")
                elif i == 4:
                    print(f"📊 Response: {response['body']['response']}")
                    print(f"🎵 Audio file: {response['body']['audio_file']}")
            else:
                print(f"❌ Error: {response['body']['error']}")
            
            if i < len(test_queries):
                print("\n" + "-"*60)
        
        print("\n🎉 All tests completed with simplified architecture!")
        
    except Exception as e:
        print(f"\n❌ Erro durante a execução do demo: {e}")