"""
Base LLM module for Gemini-2.0-flash-exp integration.
"""

import logging
import google.generativeai as genai
from typing import Optional
import os

logger = logging.getLogger(__name__)

def initialize_llm(model_name: str = "gemini-1.5-flash") -> Optional[genai.GenerativeModel]:
    """
    Initialize the Gemini LLM model.

    Args:
        model_name (str): Name of the Gemini model to use

    Returns:
        Optional[genai.GenerativeModel]: Initialized model if successful, None otherwise
    """
    try:
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set")
        
        genai.configure(api_key=api_key)
        agent= genai.GenerativeModel(model_name)
        return agent
    except Exception as e:
        logger.error(f"Error initializing LLM: {str(e)}")
        return None

def generate_response(prompt: str, agent: Optional[genai.GenerativeModel] = None) -> Optional[str]:
    """
    Generate a response using the LLM.

    Args:
        prompt (str): Input prompt for the LLM
        agent (Optional[genai.GenerativeModel]): Initialized agent to use

    Returns:
        Optional[str]: Generated response if successful, None otherwise
    """
    try:
        if agent is None:
            print("Initializing LLM")
            agent = initialize_llm()
            if agent is None:
                return None  
        response = agent.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return None