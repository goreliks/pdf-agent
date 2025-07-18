"""
Schemas for the PDF Processing LangGraph Agent

This module defines the state schemas and data models for the LangGraph agent
that processes PDFs in parallel for hash calculations, image extraction, 
URL extraction, and perceptual hashing.
"""

import operator
from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from typing_extensions import Annotated, TypedDict


class PDFHashData(BaseModel):
    """Hash information for the PDF file."""
    sha1: str = Field(..., description="SHA1 hash of the PDF file")
    md5: str = Field(..., description="MD5 hash of the PDF file")


class ExtractedImage(BaseModel):
    """Information about an extracted image."""
    page_number: int = Field(..., description="Page number the image was extracted from (0-based)")
    base64_data: str = Field(..., description="Base64-encoded image data")
    format: str = Field(..., description="Image format (e.g., 'png', 'jpg')")
    phash: Optional[str] = Field(None, description="Perceptual hash of the image")
    saved_path: Optional[str] = Field(None, description="Path where the image was saved with SHA1 filename")
    image_sha1: Optional[str] = Field(None, description="SHA1 hash of the image data")


class ExtractedURL(BaseModel):
    """Information about an extracted URL."""
    url: str = Field(..., description="The extracted URL")
    page_number: int = Field(..., description="Page number where the URL was found")
    url_type: str = Field(..., description="Type of URL (annotation or text)")
    coordinates: Optional[Dict[str, float]] = Field(None, description="Coordinates of the URL if from annotation")
    is_external: Optional[bool] = Field(None, description="Whether the URL is external")


class PDFProcessingState(TypedDict):
    """
    State for the PDF Processing LangGraph Agent.
    
    This state manages the processing of a PDF document including:
    - File validation and hash calculations  
    - Image extraction with base64 encoding and phash
    - URL extraction from PDF annotations and text
    - Error tracking
    """
    
    # Input parameters
    pdf_path: str  # Path to the PDF file to process
    pages_to_process: Optional[List[int]]  # List of pages to process (0-based), None for all pages
    output_directory: str  # Directory to save extracted images
    
    # PDF metadata (set by validation node)
    pdf_hash: Optional[PDFHashData]  # Hash data for the PDF file
    page_count: Optional[int]  # Total number of pages in the PDF
    
    # Extracted data (each updated by a single node in our restructured graph)
    extracted_images: List[ExtractedImage]  # Images extracted from pages
    extracted_urls: List[ExtractedURL]  # URLs extracted from PDF
    
    # Error tracking (can be updated by multiple nodes, so needs reducer)
    errors: Annotated[List[str], operator.add]  # List of errors encountered during processing


class PDFProcessingInput(BaseModel):
    """Input model for the PDF Processing Agent."""
    pdf_path: str = Field(..., description="Path to the PDF file to process")
    pages_to_process: Optional[List[int]] = Field(None, description="List of pages to process (0-based), None for all pages")
    output_directory: str = Field("./extracted_images", description="Directory to save extracted images")


class PDFProcessingOutput(BaseModel):
    """Output model for the PDF Processing Agent."""
    success: bool = Field(..., description="Whether the overall processing was successful")
    pdf_path: str = Field(..., description="Path to the processed PDF file")
    pdf_hash: Optional[PDFHashData] = Field(None, description="Hash data for the PDF file")
    page_count: Optional[int] = Field(None, description="Total number of pages in the PDF")
    extracted_images: List[ExtractedImage] = Field(default_factory=list, description="Images extracted from pages")
    extracted_urls: List[ExtractedURL] = Field(default_factory=list, description="URLs extracted from PDF")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered during processing")
    total_processing_time: Optional[float] = Field(None, description="Total time taken for all processing") 