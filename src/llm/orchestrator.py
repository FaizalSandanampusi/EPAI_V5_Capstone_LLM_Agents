"""
Orchestration LLM agent using Gemini-2.0-flash-exp.
"""

import logging
import json
import inspect
from typing import List, Dict, Any
from pathlib import Path
from .base_llm import generate_response, initialize_llm
from src.file_organizer.organizer import organize_files, create_category_dirs, validate_folder, is_organized
from src.compression.pdf_compressor import compress_pdf
from src.compression.image_compressor import compress_image
from src.todo.todo_executer import process_tasks


logger = logging.getLogger(__name__)


def plan_and_execute_tasks(tasks: List[str], folder_path: str) -> None:
    """
    Plan and execute tasks using LLM orchestration.
    
    Args:
        tasks (List[str]): List of tasks to execute
        folder_path (str): Path to the target folder
    """
    # Initialize LLM
    executing_plan_agent = initialize_llm()
    
    # Create context with available functions
    function_context = """
    Available functions and their purposes:
    
    1. validate_folder(folder_path: Path) -> Path:
       - Validates if folder exists and has write permissions
       - Creates folder if it doesn't exist
       - Returns Path object if successful, raises ValueError if not
    
    2. is_organized(folder_path: Path,file_classifier_agent: file_classifier_agent) -> bool:
       - Checks if folder has organized structure (Documents, Images, etc.)
       - Returns True if organized, False otherwise
    
    3. create_category_dirs(folder_path: Path) -> Dict[str, Path]:
       - Creates category directories (Documents, Images, Code, Others)
       - Returns dictionary mapping categories to directory paths
    
    4. organize_files(folder_path: Path, file_classifier_agent: file_classifier_agent) -> None:
       - Organizes files into appropriate category folders
       - Handles file classification and moving
    
    5. compress_pdf(folder_path: Path) -> Optional[Path]:
       - Compresses a single PDF file
       - Returns path to compressed file if successful
    
    6. compress_image(folder_path: Path) -> Optional[Path]:
       - Compresses a single image file
       - Returns path to compressed file if successful
       
    7. process_tasks(todo_file: str, agent: Optional[genai.GenerativeModel]):
      - Process all tasks from the given todo.txt file using the provided LLM agent.
    Args:
        todo_file (str): The path to the todo.txt file containing tasks.
        agent (Optional[genai.GenerativeModel]): The LLM agent instance used for parsing tasks.
        - Returns: None
    """
    
    # Create planning prompt
    prompt = f"""
    Given these tasks: {tasks}
    And folder path: {folder_path}
    
    {function_context}
    
    Plan the sequence of function calls needed to execute these tasks. For compression tasks, you don't havae to run all until compress. 
    Just run compression which already has functionality to check if files are organized and then compresses them.
    If users selects only todo then return only the process_tasks function. No need of other functions.
    If user selects all function then give all functions in the plan in order that process_tasks is last.
    Return a JSON array of function calls in order that needs to be executed.
    Don't give args or kwargs in the plan. Just return one json file with function names and steps in order like below """ + \
    """[ {step': 'step_number', 'function': 'function_name'}]
    """
    
    try:
        response = generate_response(prompt, executing_plan_agent)
        
        # Give some good logging to say that the process is starting on CLI like drawing a bot
        logger.info(
            "\n"
            "Starting task execution...\n"
            "     ,----.\n"
            "   ,/      \\\n"
            "  ((  ◕‿◕  ))\n"
            "   `\\      /'\n"
            "     `----'\n"
            "  🤖 Task Bot 🤖\n"
            "\nI'm processing your requests!\n"
        )
        
        
        
        
        
        if not response:
            raise ValueError("Failed to get execution plan from LLM")
        
        # Sanitize the response by removing any code block markers
        sanitized_response = response.replace("```json", "").replace("```", "").strip()
        
        # Attempt to parse the sanitized response
        try:
            execution_plan = json.loads(sanitized_response)
        except json.JSONDecodeError as e:
            logger.error(f"JSON decoding error: {str(e)}")
            logger.error(f"Sanitized response content: {sanitized_response}")
            raise
        
        has_other_task=False
        # Log the execution plan
        logger.info("Execution plan:")
        i=1
        for step in execution_plan:
            if step['function'] in ['compress_images', 'compress_pdf','process_tasks']:
                has_other_task=True
            logger.info(f"{i}- {step['function']}")
            i+=1
        
        # initialise file classifier agent
        # logger.info("Initialising file classifier agent")
        file_classifier_agent=initialize_llm()
        tasks_interpreter_agent=initialize_llm()
        
        params = {
        'folder_path': folder_path,
        'file_classifier_agent': file_classifier_agent,
        'tasks_interpreter_agent': tasks_interpreter_agent,
        'todo_file': Path(folder_path) / 'Files/todo.txt'
        }
        
        # Map function names to actual function objects
        function_map = {
            'validate_folder': validate_folder,
            'is_organized': is_organized,
            'create_category_dirs': create_category_dirs,
            'organize_files': organize_files,
            'compress_pdf': compress_pdf,
            'compress_image': compress_image,
            'process_tasks': process_tasks
        }
        
        organise_check=False
        
        # Execute the plan
        for step in execution_plan:
            func_name = step['function']
            
            if organise_check and not has_other_task:
                logger.info("Skipping create_category_dirs and organize_files as files are already organized")
                break
            # Log the args for debugging
            logger.info(f"Executing function: {func_name}")
            
            # Get the function from the map
            func = function_map.get(func_name)
            
            # Execute the function with args and kwargs
            sig = inspect.signature(func)
    
            # Filter params based on what the function expects
            filtered_args = {k: v for k, v in params.items() if k in sig.parameters}
            
            if func_name== 'is_organized':
                # print("parametrs",filtered_args)
                result = func(**filtered_args)
                print("result",result)
                if result:
                    logger.info("Folder is already organized")
                    organise_check=True
            elif func_name in ['create_category_dirs','organize_files'] and organise_check:
                if not has_other_task:
                    logger.info("Skipping create_category_dirs and organize_files as files are already organized")
                    break
                else:
                    logger.info(f"Skipping {func_name} as files are already organized")
                    continue
            elif func_name in ['compress_pdf','compress_image']:
                if not organise_check:
                    # Check if files are organized before compression
                    logger.info(f"Checking if files are organized before compression")
                    if is_organized(folder_path, file_classifier_agent):
                        logger.info("Files are already organized")
                    else:
                        logger.info("Organizing Files before compression.")
                        create_category_dirs(folder_path)
                        organize_files(folder_path,file_classifier_agent)
                    organise_check=True
                # Special handling for compress functions
                folder_type = "Documents" if func_name == 'compress_pdf' else "Images"
                folder = Path(folder_path) / folder_type
                for file in folder.rglob('*'):
                    if func_name == 'compress_pdf' and file.suffix.lower() == '.pdf':
                        func(file)
                    elif func_name == 'compress_image' and file.suffix.lower() in ['.jpg', '.jpeg', '.png']:
                        func(file)
            else:
                func(**filtered_args)
        
        logger.info(
            "\n"
            "All tasks completed successfully!\n"
            "    \(^o^)/\n"
            "     |___|    \n"
            "     /   \    \n"
            "\nThank you for using AI Assistant Bot!\n"
        )
        
    except Exception as e:  
        logger.error(f"Error in task execution: {str(e)}")
