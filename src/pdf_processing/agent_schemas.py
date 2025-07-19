"""
Schemas for the PDF Processing LangGraph Agent

This module defines the state schemas and data models for the LangGraph agent
that processes PDFs in parallel for hash calculations, image extraction, 
URL extraction, and perceptual hashing.

UPDATED: Enhanced with proper Pydantic validation and field validators.
"""

import operator
from typing import List, Dict, Optional
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, model_validator
from typing_extensions import Annotated, TypedDict


class PDFHashData(BaseModel):
    """Hash information for the PDF file."""
    sha1: str = Field(..., description="SHA1 hash of the PDF file", min_length=40, max_length=40)
    md5: str = Field(..., description="MD5 hash of the PDF file", min_length=32, max_length=32)
    
    @field_validator('sha1')
    @classmethod
    def validate_sha1(cls, v: str) -> str:
        """Validate SHA1 hash format."""
        if not v.isalnum():
            raise ValueError('SHA1 hash must contain only alphanumeric characters')
        return v.lower()
    
    @field_validator('md5')
    @classmethod
    def validate_md5(cls, v: str) -> str:
        """Validate MD5 hash format."""
        if not v.isalnum():
            raise ValueError('MD5 hash must contain only alphanumeric characters')
        return v.lower()


class ExtractedImage(BaseModel):
    """Information about an extracted image."""
    page_number: int = Field(..., description="Page number the image was extracted from (0-based)", ge=0)
    base64_data: str = Field(..., description="Base64-encoded image data", min_length=1)
    format: str = Field(..., description="Image format (e.g., 'png', 'jpg')")
    phash: Optional[str] = Field(None, description="Perceptual hash of the image")
    saved_path: Optional[str] = Field(None, description="Path where the image was saved with SHA1 filename")
    image_sha1: Optional[str] = Field(None, description="SHA1 hash of the image data")
    
    @field_validator('format')
    @classmethod
    def validate_format(cls, v: str) -> str:
        """Validate image format."""
        allowed_formats = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'}
        if v.lower() not in allowed_formats:
            raise ValueError(f'Image format must be one of: {", ".join(allowed_formats)}')
        return v.upper()
    
    @field_validator('saved_path')
    @classmethod
    def validate_saved_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate saved path format."""
        if v is not None and not Path(v).suffix:
            raise ValueError('Saved path should include file extension')
        return v


class ExtractedURL(BaseModel):
    """Information about an extracted URL."""
    url: str = Field(..., description="The extracted URL", min_length=1)
    page_number: int = Field(..., description="Page number where the URL was found", ge=0)
    url_type: str = Field(..., description="Type of URL (annotation or text)")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Coordinates of the URL if from annotation")
    is_external: Optional[bool] = Field(None, description="Whether the URL is external")
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Basic URL validation."""
        # Basic URL validation - could be enhanced with more sophisticated checks
        if not (v.startswith(('http://', 'https://', 'ftp://', 'mailto:', 'file://')) or 
                v.startswith(('www.', '/')) or '@' in v):
            raise ValueError('URL must be a valid URL format')
        return v.strip()
    
    @field_validator('url_type')
    @classmethod
    def validate_url_type(cls, v: str) -> str:
        """Validate URL type."""
        allowed_types = {'annotation', 'text', 'link', 'embedded'}
        if v.lower() not in allowed_types:
            raise ValueError(f'URL type must be one of: {", ".join(allowed_types)}')
        return v.lower()


class PDFProcessingState(TypedDict):
    """
    State for the PDF Processing LangGraph Agent.
    
    This state manages the processing of a PDF document including:
    - File validation and hash calculations  
    - Image extraction with base64 encoding and phash
    - URL extraction from PDF annotations and text
    - Error tracking
    
    Note: pages_to_process in state contains actual 0-based page numbers (converted from input)
    """
    
    # Input parameters (converted from PDFProcessingInput)
    pdf_path: str  # Path to the PDF file to process
    pages_to_process: Optional[List[int]]  # Actual 0-based page numbers to process (converted from input count)
    output_directory: str  # Directory to save extracted images (auto-generated if needed)
    
    # PDF metadata (set by validation node)
    pdf_hash: Optional[PDFHashData]  # Hash data for the PDF file
    page_count: Optional[int]  # Total number of pages in the PDF
    
    # Extracted data (each updated by a single node in our restructured graph)
    extracted_images: List[ExtractedImage]  # Images extracted from pages
    extracted_urls: List[ExtractedURL]  # URLs extracted from PDF
    
    # Error tracking (can be updated by multiple nodes, so needs reducer)
    errors: Annotated[List[str], operator.add]  # List of errors encountered during processing


class PDFProcessingInput(BaseModel):
    """
    Input model for the PDF Processing Agent.
    
    This model validates all input parameters before processing begins,
    ensuring type safety and catching common errors early.
    """
    pdf_path: str = Field(..., description="Path to the PDF file to process", min_length=1)
    pages_to_process: Optional[int] = Field(
        1, 
        description="Number of pages to process from the beginning (1-based). Default is 1 (first page only)",
        ge=1
    )
    output_directory: Optional[str] = Field(
        None, 
        description="Directory to save extracted images. If not provided, will create './extracted_images_<timestamp>'"
    )
    
    @field_validator('pdf_path')
    @classmethod
    def validate_pdf_path(cls, v: str) -> str:
        """Validate PDF path format and basic accessibility."""
        v = v.strip()
        if not v:
            raise ValueError('PDF path cannot be empty')
        
        # Check if path has PDF extension
        path_obj = Path(v)
        if path_obj.suffix.lower() != '.pdf':
            raise ValueError('File must have .pdf extension')
        
        return v
    
    @field_validator('pages_to_process')
    @classmethod
    def validate_pages_to_process(cls, v: Optional[int]) -> Optional[int]:
        """Validate number of pages to process."""
        if v is not None and v < 1:
            raise ValueError('Number of pages to process must be at least 1')
        return v
    
    @field_validator('output_directory')
    @classmethod
    def validate_output_directory(cls, v: Optional[str]) -> Optional[str]:
        """Validate output directory path."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('Output directory cannot be empty (use None for auto-generation)')
            # Normalize path separators
            return str(Path(v))
        return v
    
    @model_validator(mode='after')
    def validate_model(self) -> 'PDFProcessingInput':
        """Final model validation and auto-generation of output directory."""
        # Auto-generate output directory if not provided
        if self.output_directory is None:
            import time
            timestamp = int(time.time())
            self.output_directory = f"./extracted_images_{timestamp}"
        
        return self


class PDFProcessingOutput(BaseModel):
    """
    Output model for the PDF Processing Agent.
    
    This model guarantees the structure and types of all processing results,
    providing type safety for downstream consumers.
    """
    success: bool = Field(..., description="Whether the overall processing was successful")
    pdf_path: str = Field(..., description="Path to the processed PDF file")
    pdf_hash: Optional[PDFHashData] = Field(None, description="Hash data for the PDF file")
    page_count: Optional[int] = Field(None, description="Total number of pages in the PDF", ge=0)
    extracted_images: List[ExtractedImage] = Field(
        default_factory=list, 
        description="Images extracted from pages"
    )
    extracted_urls: List[ExtractedURL] = Field(
        default_factory=list, 
        description="URLs extracted from PDF"
    )
    errors: List[str] = Field(
        default_factory=list, 
        description="List of errors encountered during processing"
    )
    total_processing_time: Optional[float] = Field(
        None, 
        description="Total time taken for all processing",
        ge=0.0
    )
    
    @field_validator('pdf_path')
    @classmethod
    def validate_pdf_path(cls, v: str) -> str:
        """Ensure PDF path is not empty."""
        if not v.strip():
            raise ValueError('PDF path cannot be empty')
        return v.strip()
    
    @model_validator(mode='after')
    def validate_consistency(self) -> 'PDFProcessingOutput':
        """Validate internal consistency of the output."""
        # If processing was successful, there should be no errors
        if self.success and self.errors:
            raise ValueError('Processing cannot be successful if errors are present')
        
        # If there are errors, success should be False
        if self.errors and self.success:
            raise ValueError('Success must be False when errors are present')
        
        # Validate extracted images page numbers against page count
        if self.page_count is not None and self.extracted_images:
            invalid_pages = [
                img.page_number for img in self.extracted_images 
                if img.page_number >= self.page_count
            ]
            if invalid_pages:
                raise ValueError(
                    f'Extracted images reference invalid page numbers: {invalid_pages}. '
                    f'PDF only has {self.page_count} pages.'
                )
        
        # Validate extracted URLs page numbers against page count
        if self.page_count is not None and self.extracted_urls:
            invalid_pages = [
                url.page_number for url in self.extracted_urls 
                if url.page_number >= self.page_count
            ]
            if invalid_pages:
                raise ValueError(
                    f'Extracted URLs reference invalid page numbers: {invalid_pages}. '
                    f'PDF only has {self.page_count} pages.'
                )
        
        return self
    
    def get_processing_summary(self) -> Dict[str, any]:
        """Get a summary of processing results."""
        return {
            "success": self.success,
            "processing_time": self.total_processing_time,
            "page_count": self.page_count,
            "images_extracted": len(self.extracted_images),
            "urls_found": len(self.extracted_urls),
            "errors_count": len(self.errors),
            "has_hash": self.pdf_hash is not None
        }
    
    def to_json_summary(self) -> str:
        """Get a JSON summary of key metrics."""
        import json
        return json.dumps(self.get_processing_summary(), indent=2) 