"""
Image compression module that interfaces with TinyPNG compression service.
"""

import logging
import os
from pathlib import Path
from typing import Optional
import tinify

logger = logging.getLogger(__name__)

def initialize_tinify() -> bool:
    """
    Initialize the TinyPNG API client.

    Returns:
        bool: True if initialization successful, False otherwise
    """
    api_key = os.getenv('IMAGE_COMPRESSION_API_KEY')
    if not api_key:
        logger.warning("No API key provided for image compression service")
        return False
    
    try:
        tinify.key = api_key
        return True
    except Exception as e:
        logger.error(f"Error initializing TinyPNG: {str(e)}")
        return False

def compress_image(file_path: Path) -> Optional[Path]:
    """
    Compress an image file using TinyPNG service.

    Args:
        file_path (Path): Path to the image file to compress

    Returns:
        Optional[Path]: Path to the compressed file if successful, None otherwise
    """
    if not is_supported_image(file_path):
        logger.warning(f"Unsupported image format: {file_path}")
        return None
    
    if not initialize_tinify():
        return None

    try:
        # Create compressed filename
        name = file_path.stem
        
        # Skip if file name contains 'compressed'
        if 'compressed' in name.lower():
            logger.info(f"Skipping {file_path.name} as filename suggests it's already compressed")
            return None
        
        suffix = file_path.suffix
        compressed_path = file_path.parent / f"{name}_compressed{suffix}"

        # Compress using TinyPNG
        source = tinify.from_file(str(file_path))
        source.to_file(str(compressed_path))

        logger.info(f"Compressed image saved to: {compressed_path}")
        return compressed_path

    except tinify.AccountError as e:
        logger.error(f"TinyPNG account error: {str(e)}")
    except tinify.ClientError as e:
        logger.error(f"TinyPNG client error: {str(e)}")
    except tinify.ServerError as e:
        logger.error(f"TinyPNG server error: {str(e)}")
    except tinify.ConnectionError as e:
        logger.error(f"TinyPNG connection error: {str(e)}")
    except Exception as e:
        logger.error(f"Error compressing image {file_path}: {str(e)}")
    
    return None

def is_supported_image(file_path: Path) -> bool:
    """
    Check if the file is a supported image format for TinyPNG.

    Args:
        file_path (Path): Path to the file to check

    Returns:
        bool: True if the file is a supported image format, False otherwise
    """
    supported_extensions = {'.jpg', '.jpeg', '.png'}
    return file_path.suffix.lower() in supported_extensions 