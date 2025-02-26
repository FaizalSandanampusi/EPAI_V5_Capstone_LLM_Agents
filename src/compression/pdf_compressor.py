"""
PDF compression module that interfaces with ILovePDF compression service.
"""

import logging
import os
from pathlib import Path
from typing import Optional
from iloveapi import ILoveApi

logger = logging.getLogger(__name__)

def initialize_ilovepdf() -> Optional[ILoveApi]:
    """
    Initialize the ILovePDF API client.

    Returns:
        Optional[ILoveApi]: Initialized client if successful, None otherwise
    """
    public_key = os.getenv('PDF_COMPRESSION_API_KEY_PUBLIC')
    secret_key = os.getenv('PDF_COMPRESSION_API_KEY_SECRET')
    
    if not public_key or not secret_key:
        logger.warning("Missing API keys for PDF compression service")
        return None
    
    try:
        client = ILoveApi(
            public_key=public_key,
            secret_key=secret_key
        )
        return client
    except Exception as e:
        logger.error(f"Error initializing ILovePDF client: {str(e)}")
        return None

def compress_pdf(file_path: Path) -> Optional[Path]:
    """
    Compress a PDF file using ILovePDF service.

    Args:
        file_path (Path): Path to the PDF file to compress

    Returns:
        Optional[Path]: Path to the compressed file if successful, None otherwise
    """
    if not file_path.suffix.lower() == '.pdf':
        logger.warning(f"Not a PDF file: {file_path}")
        return None

    # Skip if file name contains 'compressed'
    if 'compressed' in file_path.stem.lower():
        logger.info(f"Skipping {file_path.name} as filename suggests it's already compressed")
        return None

    client = initialize_ilovepdf()
    if not client:
        return None

    try:
        # Create compressed filename
        name = file_path.stem
        compressed_path = file_path.parent / f"{name}_compressed.pdf"

        # Create and process the compression task
        task = client.create_task("compress")
        task.process_files(str(file_path))
        task.download(str(compressed_path))

        logger.info(f"Compressed PDF saved to: {compressed_path}")
        
        # Log compression results
        original_size = file_path.stat().st_size / 1024  # KB
        compressed_size = compressed_path.stat().st_size / 1024  # KB
        savings = ((original_size - compressed_size) / original_size) * 100
        logger.info(f"Compressed {file_path.name}: {original_size:.2f}KB -> {compressed_size:.2f}KB ({savings:.1f}% saved)")
        
        return compressed_path

    except Exception as e:
        logger.error(f"Error compressing PDF {file_path}: {str(e)}")
        return None

# def compress_pdfs_in_directory(directory: Path) -> None:
#     """
#     Compress all PDF files in a directory and its subdirectories.

#     Args:
#         directory (Path): Directory path containing PDFs to compress
#     """
#     logger.info(f"Compressing PDFs in {directory}")
    
#     try:
#         for file_path in directory.rglob('*.pdf'):
#             if file_path.is_file() and '_compressed' not in file_path.stem:
#                 compressed_path = compress_pdf(file_path)
#                 if not compressed_path:
#                     logger.warning(f"Failed to compress {file_path}")
    
#     except Exception as e:
#         logger.error(f"Error processing directory {directory}: {str(e)}") 