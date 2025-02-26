"""
Interactive agent module for task selection and orchestration using LLM.
"""

import logging
from typing import List, Dict, Any, Tuple
from pathlib import Path
from .base_llm import generate_response, initialize_llm
from src.file_organizer.organizer import validate_folder

logger = logging.getLogger(__name__)

def interpret_user_input(user_input: str) -> List[str]:
    """
    Use LLM to interpret user input into specific tasks.
    
    Args:
        user_input (str): User's input text
        
    Returns:
        List[str]: List of interpreted tasks
    """
    prompt = f"""
    Interpret the following user input and identify which tasks they want to perform.
    Valid tasks are: 'organize' (organizing files), 'compress' (compressing files), and 'todo' (running todo tasks).
    Return only the task names in order, separated by commas. If no valid tasks are found, return 'none'.
    Also try to find close matches for the tasks if the input is unclear. If is says run all then return all tasks.
    User input: {user_input}
    """
    
    try:
        model = initialize_llm()
        response = generate_response(prompt, model)
        
        if not response or response.lower() == 'none':
            return []
            
        # Convert LLM response to list of tasks
        tasks = [task.strip().lower() for task in response.split(',')]
        valid_tasks = ['organize', 'compress', 'todo']
        
        # Filter and order valid tasks
        tasks = [task for task in tasks if task in valid_tasks]
        tasks.sort(key=lambda x: valid_tasks.index(x))
        
        return tasks
    except Exception as e:
        logger.error(f"Error interpreting tasks: {str(e)}")
        return []

def get_user_tasks() -> Tuple[List[str], str]:
    """
    Interactive function to get user tasks and folder location using LLM interpretation.
    
    Returns:
        Tuple[List[str], str]: List of selected tasks and folder location
    """
    print("\nWelcome! I'm your automation assistant.")
    print("Please tell me what tasks you'd like to perform.")
    print("Available tasks:")
    print("- Organize files")
    print("- Compress files")
    print("- Run todo tasks")
    
    while True:
        user_input = input("\nWhat would you like me to do? ").strip()
        tasks = interpret_user_input(user_input)
        
        if not tasks:
            print("\nI couldn't interpret any valid tasks from your input.")
            print("Please specify one or more of the following tasks:")
            print("- Organize files")
            print("- Compress files")
            print("- Run todo tasks")
            continue
        
        # Show interpreted tasks
        print("\nI understand you want to:")
        for task in tasks:
            if task == 'organize':
                print("- Organize your files into categories")
            elif task == 'compress':
                print("- Compress PDFs and images")
            elif task == 'todo':
                print("- Process tasks from your todo list")
        
        confirm = input("\nIs this correct? (yes/no): ").lower().strip()
        if confirm != 'yes':
            print("\nLet's try again.")
            continue
            
        while True:
            folder_path = input("\nPlease enter the folder location: ").strip()
            try:
                validate_folder(folder_path)
                break
            except ValueError as e:
                logger.error(str(e))
                print("Invalid folder path. Please try again.")
        
        print(f"\nFolder location: {folder_path}")
        confirm = input("Proceed with these tasks? (yes/no): ").lower().strip()
        if confirm == 'yes':
            return tasks, folder_path
        
        print("\nLet's start over.") 