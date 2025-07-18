"""
Common utilities for PDF processing.

This module provides shared utilities for file validation, path management,
and error handling across the PDF processing package.
"""

import pathlib
from typing import Union, List, Optional


def validate_pdf_path(pdf_path: Union[str, pathlib.Path]) -> pathlib.Path:
    """
    Validate and normalize a PDF file path.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Normalized pathlib.Path object
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the path is not a file or not a PDF
        
    Example:
        >>> pdf_path = validate_pdf_path("document.pdf")
        >>> print(f"Validated PDF: {pdf_path}")
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"File not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    # Check if file has PDF extension (case-insensitive)
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"File does not have a PDF extension: {pdf_path}")
    
    return pdf_path


def ensure_output_directory(output_path: Union[str, pathlib.Path]) -> pathlib.Path:
    """
    Ensure the output directory exists, creating it if necessary.
    
    Args:
        output_path: Path to the output file or directory
        
    Returns:
        Normalized pathlib.Path object
        
    Raises:
        OSError: If directory cannot be created
        
    Example:
        >>> output_path = ensure_output_directory("output/images/page1.png")
        >>> print(f"Output directory ready: {output_path.parent}")
    """
    output_path = pathlib.Path(output_path)
    
    # If it's a file path, get the parent directory
    if output_path.suffix:
        directory = output_path.parent
    else:
        directory = output_path
    
    # Create directory if it doesn't exist
    try:
        directory.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise OSError(f"Cannot create output directory {directory}: {e}")
    
    return output_path


def get_safe_filename(filename: str, max_length: int = 255) -> str:
    """
    Create a safe filename by removing or replacing problematic characters.
    
    Args:
        filename: Original filename
        max_length: Maximum length for the filename (default: 255)
        
    Returns:
        Safe filename string
        
    Example:
        >>> safe_name = get_safe_filename("file<>with:bad|chars?.pdf")
        >>> print(f"Safe filename: {safe_name}")
    """
    # Characters that are problematic in filenames
    unsafe_chars = '<>:"/\\|?*'
    
    # Replace unsafe characters with underscores
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove any control characters
    safe_name = ''.join(char for char in safe_name if ord(char) >= 32)
    
    # Trim to max length
    if len(safe_name) > max_length:
        # Try to preserve the extension
        if '.' in safe_name:
            name, ext = safe_name.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            if max_name_length > 0:
                safe_name = name[:max_name_length] + '.' + ext
            else:
                safe_name = safe_name[:max_length]
        else:
            safe_name = safe_name[:max_length]
    
    # Ensure filename is not empty
    if not safe_name or safe_name.isspace():
        safe_name = "unnamed_file"
    
    return safe_name


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
        
    Example:
        >>> size_str = format_file_size(1024 * 1024)
        >>> print(f"File size: {size_str}")  # "1.0 MB"
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def get_file_info(file_path: Union[str, pathlib.Path]) -> dict:
    """
    Get comprehensive information about a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary with file information
        
    Raises:
        FileNotFoundError: If the file does not exist
        OSError: If file information cannot be retrieved
        
    Example:
        >>> info = get_file_info("document.pdf")
        >>> print(f"File size: {info['size_formatted']}")
        >>> print(f"Modified: {info['modified']}")
    """
    file_path = pathlib.Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    try:
        stat = file_path.stat()
        
        return {
            'path': str(file_path),
            'name': file_path.name,
            'stem': file_path.stem,
            'suffix': file_path.suffix,
            'size_bytes': stat.st_size,
            'size_formatted': format_file_size(stat.st_size),
            'modified': stat.st_mtime,
            'is_file': file_path.is_file(),
            'is_dir': file_path.is_dir(),
            'parent': str(file_path.parent),
            'absolute_path': str(file_path.absolute())
        }
    except OSError as e:
        raise OSError(f"Cannot get file information for {file_path}: {e}")


def batch_validate_paths(paths: List[Union[str, pathlib.Path]]) -> List[pathlib.Path]:
    """
    Validate multiple file paths, returning only valid ones.
    
    Args:
        paths: List of file paths to validate
        
    Returns:
        List of valid pathlib.Path objects
        
    Example:
        >>> valid_paths = batch_validate_paths(["file1.pdf", "file2.pdf", "missing.pdf"])
        >>> print(f"Found {len(valid_paths)} valid files")
    """
    valid_paths = []
    
    for path in paths:
        try:
            validated_path = validate_pdf_path(path)
            valid_paths.append(validated_path)
        except (FileNotFoundError, ValueError):
            # Skip invalid paths silently
            continue
    
    return valid_paths


class PDFProcessingError(Exception):
    """Base exception for PDF processing errors."""
    pass


class PDFValidationError(PDFProcessingError):
    """Raised when PDF validation fails."""
    pass


class ImageExtractionError(PDFProcessingError):
    """Raised when image extraction fails."""
    pass


class HashCalculationError(PDFProcessingError):
    """Raised when hash calculation fails."""
    pass