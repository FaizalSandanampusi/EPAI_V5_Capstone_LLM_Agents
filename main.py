#!/usr/bin/env python3
"""
Main entry point for the Capstone Project.
This script provides LLM-based task interpretation and orchestration.
"""

import logging
from src.llm.agent import get_user_tasks
from src.llm.orchestrator import plan_and_execute_tasks
from dotenv import load_dotenv

# Loading environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def print_welcome_message():
    """Print welcome message with ASCII art bot."""
    welcome = """
    Hello! I'm your AI Assistant Bot!
         _____
        /_____\\
       /|     |\\
      /_|_____|_\\
        |  |  |
        |--+--|
        |__|__|
       (oO___Oo)
    
    I can help you with:
    - Organizing files 
    - Compressing files 
    - Running todo tasks
    
    How may I assist you today?
    """
    print(welcome)

def main():
    """
    Main function that handles task interpretation and orchestration.
    """
    try:
        print_welcome_message()
        
        # Get tasks from user through agent
        tasks, folder_path = get_user_tasks()
        
        # Pass tasks to orchestrator for planning and execution
        plan_and_execute_tasks(tasks, folder_path)
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main() 