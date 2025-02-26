"""
File organization module that handles scanning directories and organizing files.
"""

import logging
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import google.generativeai as genai
from src.file_organizer.file_classifier import classify_files
from src.llm.base_llm import initialize_llm

import os

logger = logging.getLogger(__name__)

def organize_files(folder_path: str, file_classifier_agent: Optional[genai.GenerativeModel]) -> None:
    """
    Organize files in the 'My Files' subdirectory into categorized folders.

    Args:
        root_dir (str): Root directory path to organize
    """
    root_path = Path(folder_path) / "Files"  # Adjust the path to target 'Files' subdirectory
    category_dirs ={
        'documents': Path(folder_path) / "Documents",
        'images': Path(folder_path) / "Images",
        'code': Path(folder_path) / "Code",
        'others': Path(folder_path) / "Others"
    }    
    
    # Get the list of files to organize
    
    file_paths = scan_directory(root_path)
    
    # use classify_files to get category for each file
    classifications = classify_files(file_paths, file_classifier_agent)
    
    # Move files to respective category directories
    for file_path in file_paths:
        try:
            # Check if the file still exists before processing
            if not file_path.exists():
                logger.warning(f"Source file does not exist: {file_path}")
                continue

            category = classifications.get(file_path.name, 'Others')  # Default to 'others' if not found
            if category in category_dirs:
                dest_dir = category_dirs[category]
                dest_file_path = dest_dir / file_path.name
                # shutil.move(str(file_path), str(dest_dir / file_path.name))
                # logger.info(f"Moved {file_path.name} to {category} directory")
                # Remove the existing file if it exists
                if dest_file_path.exists():
                    dest_file_path.unlink()
                
                # Copy the file to the destination directory
                shutil.copy2(str(file_path), str(dest_file_path))
                logger.info(f"Copied {file_path.name} to {category} directory")
        except Exception as e:
            logger.error(f"Error copying {file_path}: {str(e)}")

def create_category_dirs(folder_path: Path) -> Dict[str, Path]:
    """
    Create category directories if they don't exist.

    Args:
        root_path (Path): Root directory path

    Returns:
        Dict[str, Path]: Dictionary mapping categories to directory paths

    Raises:
        ValueError: If directories cannot be created due to permissions
    """
    
    # Validate the root path first
    validate_folder(str(folder_path))
    
    root_path = Path(folder_path)  # Convert the string to a Path object

    categories = {
        'documents': root_path / 'Documents',
        'images': root_path / 'Images',
        'code': root_path / 'Code',
        'others': root_path / 'Others'
    }

    try:
        for dir_path in categories.values():
            dir_path.mkdir(exist_ok=True, parents=True)
            logger.info(f"Ensured directory exists: {dir_path}")
    except PermissionError:
        raise ValueError(f"Cannot create directories in {root_path}. Permission denied.")
    except OSError as e:
        raise ValueError(f"Cannot create directories in {root_path}. Error: {str(e)}")

    return categories

def scan_directory(root_path: Path) -> List[Path]:
    """
    Scan the root directory for files, excluding hidden files.

    Args:
        root_path (Path): Root directory path to scan

    Returns:
        List[Path]: List of file paths found in the directory
    """
    files = []
    for item in root_path.rglob('*'):
        if item.is_file() and not item.name.startswith('.'):
            files.append(item)
    return files 

def validate_folder(folder_path: str) -> Path:
    """
    Validate the folder path and check permissions.

    Args:
        folder_path (str): Path to the folder

    Returns:
        Path: Validated Path object

    Raises:
        ValueError: If the path is invalid or lacks write permissions
    """
    path = Path(folder_path).resolve()

    if not path.exists():
        raise ValueError(f"Directory does not exist: {path}")

    if not os.access(str(path), os.W_OK):
        raise ValueError(f"No write permission for {path}. Please use a different location.")

    return path

def is_organized(folder_path: str,file_classifier_agent: Optional[genai.GenerativeModel]) -> bool:
    """
    Check if the files in the folder are organized into the expected category directories.

    This function scans the 'Files' subdirectory to get all unorganized files,
    then uses the batch classifier (classify_files) to obtain a predicted mapping
    (file name → category). It also extracts the actual organization by scanning the
    category folders (Documents, Images, Code, Others). Finally, it compares both mappings.

    Args:
        folder_path (str): Root directory path to check.

    Returns:
        bool: True if every file is in the correct location as per its LLM classification, otherwise False.
    """
    path = Path(folder_path)
    expected_folders = ['Documents', 'Images', 'Code', 'Others']
    
    # Ensure all expected category folders exist
    if not all((path / folder).exists() for folder in expected_folders):
        logger.info("Not all category folders exist.")
        return False
    
    # Get list of files from the unorganized 'Files' directory
    my_files_path = path / "Files"
    files = scan_directory(my_files_path)
    
    
    # Manually extract the current organization by scanning each category folder.
    # This mapping is file name → category (as determined by its folder location).
    manual_mapping = {}
    file_paths = []
    for folder in expected_folders:
        folder_path_cat = path / folder
        for file in scan_directory(folder_path_cat):
            file_paths.append(file)
            manual_mapping[file.name] = folder.lower()
    
     # Get LLM-based classifications in batch    
    
    predicted_classifications=classify_files(file_paths,file_classifier_agent)
    
    # print('manual mapping:', manual_mapping)
    # print("Predicted mapping: ", predicted_classifications)
    # Compare the predicted classification with the manual organization.
    for file in files:
        file_name = file.name
        predicted_category = predicted_classifications.get(file_name, 'others')
        manual_category = manual_mapping.get(file_name)
        if manual_category != predicted_category:
            logger.warning(f"Mismatch for {file_name}: predicted {predicted_category}, but found in {manual_category}")
            return False
    
    return True