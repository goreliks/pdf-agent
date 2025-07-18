"""
PDF Processing Package

This package provides utilities for PDF preprocessing, including:
- Hash calculation (SHA1, MD5)
- Image extraction from PDF pages
- URL extraction from PDFs (annotations and text)
- File validation and utilities

This package is designed to support the visual analysis agent by providing
clean, efficient preprocessing capabilities.
"""

from .hashing import (
    calculate_file_hashes,
    calculate_sha1,
    calculate_md5,
)

from .image_extraction import (
    extract_first_page_image,
    extract_first_page_as_pil,
    extract_pages_as_base64_images,
    save_image_with_sha1_filename,
    calculate_image_phash,
    get_pdf_page_count,
    get_pdf_page_dimensions,
)

from .utils import (
    validate_pdf_path,
    ensure_output_directory,
    get_safe_filename,
    format_file_size,
    get_file_info,
    batch_validate_paths,
    PDFProcessingError,
    PDFValidationError,
    ImageExtractionError,
    HashCalculationError,
)

from .url_extraction import (
    extract_urls_from_pdf,
    PDFURLExtractor,
    URLMatch,
    URLType,
    URLExtractionError,
)

from .agent_schemas import (
    PDFProcessingState,
    PDFProcessingInput,
    PDFProcessingOutput,
    PDFHashData,
    ExtractedImage,
    ExtractedURL,
)

from .pdf_agent import (
    process_pdf_with_agent,
    create_pdf_processing_graph,
)

__version__ = "0.1.0"
__author__ = "PDF Agent Team"

__all__ = [
    # Hashing functions
    "calculate_file_hashes",
    "calculate_sha1",
    "calculate_md5",
    
    # Image extraction functions
    "extract_first_page_image",
    "extract_first_page_as_pil",
    "extract_pages_as_base64_images",
    "save_image_with_sha1_filename",
    "calculate_image_phash",
    "get_pdf_page_count",
    "get_pdf_page_dimensions",
    
    # URL extraction functions
    "extract_urls_from_pdf",
    "PDFURLExtractor",
    "URLMatch",
    "URLType",
    
    # Agent schemas
    "PDFProcessingState",
    "PDFProcessingInput", 
    "PDFProcessingOutput",
    "PDFHashData",
    "ExtractedImage",
    "ExtractedURL",
    
    # PDF Agent
    "process_pdf_with_agent",
    "create_pdf_processing_graph",
    
    # Utility functions
    "validate_pdf_path",
    "ensure_output_directory",
    "get_safe_filename",
    "format_file_size",
    "get_file_info",
    "batch_validate_paths",
    
    # Exceptions
    "PDFProcessingError",
    "PDFValidationError",
    "ImageExtractionError",
    "HashCalculationError",
    "URLExtractionError",
]