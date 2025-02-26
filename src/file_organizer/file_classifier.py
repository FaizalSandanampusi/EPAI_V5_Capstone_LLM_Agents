"""
File classification module using Gemini-2.0-flash-exp.
"""

import logging
import json
from typing import List, Dict
from pathlib import Path
from typing import Optional
from ..llm.base_llm import generate_response, initialize_llm
import google.generativeai as genai

logger = logging.getLogger(__name__)

def classify_files(file_paths: List[Path],agent: Optional[genai.GenerativeModel]) -> Dict[str, str]:
    """
    Batch classify a list of files using the Gemini LLM based on their metadata.

    The prompt will list each file (with name, extension, size) and instruct the LLM to return a
    JSON object mapping file names to one of these categories: documents, images, code, others.

    Args:
        file_paths (List[Path]): List of file paths to classify.
        a

    Returns:
        Dict[str, str]: Dictionary mapping file names to classification categories.
    """
    # try:
    prompt = "Classify this file list based on the file name and extension into one of the four categories 'documents', 'images', 'code', 'others'. " \
    "Return a dictionary with the format {file_name.extension: file_type}. File List: " + \
    f"{[f'Filename: {file_path.name} Extension: {file_path.suffix}' for file_path in file_paths]}" + \
    " Do not give code and only return the dictionary even without three backticks. Just a plain dictionary."
    
    response = generate_response(prompt,agent)
    # print("classifier response",response)
    response_str = response.replace("'", "\"")
    
    classifications = json.loads(response_str)
    
    return classifications
