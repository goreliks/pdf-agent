"""
Hash calculation utilities for PDF processing.

This module provides functions for calculating SHA1 and MD5 hashes of files
in a memory-efficient manner using chunk-based processing.
"""

import hashlib
import pathlib
from typing import Dict, Union


def calculate_file_hashes(file_path: Union[str, pathlib.Path], chunk_size: int = 8192) -> Dict[str, str]:
    """
    Calculate SHA1 and MD5 hashes for a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read at a time (default: 8192 bytes)
        
    Returns:
        Dictionary containing 'sha1' and 'md5' hash values as hexadecimal strings
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read due to permissions
        OSError: If there's an error reading the file
        
    Example:
        >>> hashes = calculate_file_hashes("document.pdf")
        >>> print(f"SHA1: {hashes['sha1']}")
        >>> print(f"MD5: {hashes['md5']}")
    """
    file_path = pathlib.Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    # Initialize hash objects
    sha1_hash = hashlib.sha1()
    md5_hash = hashlib.md5()
    
    # Read file in chunks to handle large files efficiently
    try:
        with open(file_path, 'rb') as file:
            while chunk := file.read(chunk_size):
                sha1_hash.update(chunk)
                md5_hash.update(chunk)
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")
    except OSError as e:
        raise OSError(f"Error reading file {file_path}: {e}")
    
    return {
        'sha1': sha1_hash.hexdigest(),
        'md5': md5_hash.hexdigest()
    }


def calculate_sha1(file_path: Union[str, pathlib.Path], chunk_size: int = 8192) -> str:
    """
    Calculate SHA1 hash for a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read at a time (default: 8192 bytes)
        
    Returns:
        SHA1 hash as hexadecimal string
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read due to permissions
        OSError: If there's an error reading the file
    """
    return calculate_file_hashes(file_path, chunk_size)['sha1']


def calculate_md5(file_path: Union[str, pathlib.Path], chunk_size: int = 8192) -> str:
    """
    Calculate MD5 hash for a file.
    
    Args:
        file_path: Path to the file to hash
        chunk_size: Size of chunks to read at a time (default: 8192 bytes)
        
    Returns:
        MD5 hash as hexadecimal string
        
    Raises:
        FileNotFoundError: If the specified file does not exist
        PermissionError: If the file cannot be read due to permissions
        OSError: If there's an error reading the file
    """
    return calculate_file_hashes(file_path, chunk_size)['md5']