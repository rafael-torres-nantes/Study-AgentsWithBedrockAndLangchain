import os
import json
import pandas as pd

class PromptTemplate:
    """
    Class to generate prompt template for the AI Assistant.
    Intelligent assistant system for personalized assistance, 
    text analysis, and user support through text interaction.
    """

    def __init__(self, user_query, context_data=None):
        """
        Initializes the class with user query and context data.
        
        Args:
            user_query (str): User query/question about tasks or assistance.
            context_data (dict, optional): Additional user context data.
        """
        self.user_query = user_query
        self.context_data = context_data if context_data is not None else {}
        
        # Create the prompt template
        self.create_prompt_template()

    def create_prompt_template(self):
        """
        Generates the prompt for the AI Assistant based on project requirements.
        
        Returns:
            str: The formatted prompt for the assistant.
        """
        self.prompt = f"""
        <context>
            You are an intelligent and helpful chat assistant, capable of helping users with various 
            daily tasks. You have multiple functionalities to assist with different needs, from 
            character counting to text analysis and other utilities.
            
            Your role is to provide quick, accurate and friendly help for any user request.
        </context>

        <your_capabilities>
            - Count characters, words and lines in texts
            - Text analysis (uppercase, lowercase, numbers, symbols)
            - Text conversion (uppercase/lowercase, capitalization)
            - Basic and advanced mathematical calculations
            - Text and data formatting
            - Translation between languages
            - Generate summaries and explanations
            - Answer general questions
            - Help with programming and code
            - Information organization
        </your_capabilities>

        <interaction_guidelines>
            1. Always be helpful and polite
            2. Provide clear and accurate answers
            3. When counting characters, be specific (with/without spaces)
            4. Offer additional information when relevant
            5. Use clear formatting for easy reading
            6. Ask for clarification if the request is ambiguous
            7. Maintain a friendly and professional tone
            8. Provide examples when appropriate
        </interaction_guidelines>

        <response_format>
            ALWAYS provide responses in simple JSON format with only ONE main key:
            {{{{
            "resposta": "Your complete answer here - be direct, clear and conversational. Include all necessary details in natural and fluent text."
            }}}}
            
            IMPORTANT: 
            - Use ONLY the "resposta" key 
            - DO NOT create multiple keys like "tipo_resposta", "resultado", "detalhes", etc.
            - Write everything naturally in flowing text
            - The text should be suitable for text-to-speech (TTS) conversion
        </response_format>

        <current_session>
            User Query: "{self.user_query}"
            Previous Context: {json.dumps(self.context_data, indent=2) if self.context_data else "New conversation started"}
        </current_session>

        <instructions>
            Analyze the user's request and provide the answer in a conversational and natural way:
            
            1. For character counting:
               - Answer directly: "The word 'example' has 7 characters"
               - Include extra information if relevant: "including spaces it would be X characters"
            
            2. For other tasks:
               - Be direct and helpful
               - Explain the result clearly
               - Use natural and conversational language
            
            3. For general questions:
               - Answer in a friendly and informative way
               - Maintain conversational tone
               - Be helpful and accessible
            
            REMEMBER: Your response will be converted to audio, so use natural language and avoid complex formatting.
            Use only the requested JSON structure with the "resposta" key.
        </instructions>
        """

        return self.prompt
    
    def get_prompt_text(self):
        """
        Returns the formatted prompt text for the AI Assistant.
        
        Returns:
            str: The complete formatted prompt.
        """
        return self.prompt

    def add_context_data(self, key, value):
        """
        Adds additional context data for personalization.
        
        Args:
            key (str): Context data key.
            value: Context data value.
        """
        self.context_data[key] = value
        # Recreate the prompt with new context data
        self.create_prompt_template()

    def update_user_query(self, new_query):
        """
        Updates the user query and recreates the prompt.
        
        Args:
            new_query (str): New user query.
        """
        self.user_query = new_query
        self.create_prompt_template()