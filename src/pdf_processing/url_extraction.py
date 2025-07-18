"""
URL Extraction Module for PDF Processing

This module provides comprehensive URL extraction capabilities for PDF documents,
supporting both annotation-based links with coordinates and text-based URLs.
Optimized for maximum efficiency and robustness.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

try:
    import pymupdf
except ImportError:
    raise ImportError("PyMuPDF is required for URL extraction. Install with: pip install pymupdf")

try:
    from .utils import validate_pdf_path, PDFProcessingError
except ImportError:
    # For standalone testing, define minimal versions
    from pathlib import Path
    
    def validate_pdf_path(pdf_path):
        """Minimal validation for standalone testing."""
        path = Path(pdf_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        if not path.suffix.lower() == '.pdf':
            raise ValueError(f"File is not a PDF: {path}")
        return path
    
    class PDFProcessingError(Exception):
        """Base exception for PDF processing errors."""
        pass


class URLType(Enum):
    """Enumeration of URL types found in PDFs."""
    ANNOTATION = "annotation"  # URLs from PDF annotations/links (with coordinates)
    TEXT = "text"  # URLs extracted from text content (without coordinates)


@dataclass
class URLMatch:
    """Represents a URL found in a PDF with its metadata."""
    url: str
    url_type: URLType
    page_number: int  # 0-based
    
    # Coordinate information (only for annotation-based URLs)
    x0: Optional[float] = None  # Left coordinate
    y0: Optional[float] = None  # Bottom coordinate  
    x1: Optional[float] = None  # Right coordinate
    y1: Optional[float] = None  # Top coordinate
    
    # Additional metadata
    is_external: Optional[bool] = None  # True if external URL
    link_type: Optional[str] = None     # Type of link (e.g., 'uri', 'goto')
    xref: Optional[int] = None          # PDF cross-reference number
    
    def __post_init__(self):
        """Validate URL match data after initialization."""
        if self.url_type == URLType.ANNOTATION:
            # Annotation-based URLs should have coordinates
            if any(coord is None for coord in [self.x0, self.y0, self.x1, self.y1]):
                logging.warning(f"Annotation URL missing coordinates: {self.url}")
        
        # Ensure URL is not empty
        if not self.url or not self.url.strip():
            raise ValueError("URL cannot be empty")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert URLMatch to dictionary for serialization."""
        result = {
            'url': self.url,
            'type': self.url_type.value,
            'page_number': self.page_number,
        }
        
        # Add coordinates if available
        if self.url_type == URLType.ANNOTATION and all(
            coord is not None for coord in [self.x0, self.y0, self.x1, self.y1]
        ):
            result['coordinates'] = {
                'x0': self.x0,
                'y0': self.y0,
                'x1': self.x1,
                'y1': self.y1
            }
        
        # Add optional metadata
        if self.is_external is not None:
            result['is_external'] = self.is_external
        if self.link_type is not None:
            result['link_type'] = self.link_type
        if self.xref is not None:
            result['xref'] = self.xref
            
        return result


class URLExtractionError(PDFProcessingError):
    """Raised when URL extraction fails."""
    pass


class PDFURLExtractor:
    """
    High-performance URL extractor for PDF documents.
    
    Supports extraction from both PDF annotations/links (with coordinates)
    and text content (without coordinates as requested).
    """
    
    # Comprehensive URL regex pattern
    URL_PATTERN = re.compile(
        r'''
        (?i)                                 # Case insensitive
        (?:
            (?:https?|ftp|ftps)://           # Protocol
            |www\.                           # www. prefix
            |[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.  # Domain start
            (?:com|org|net|edu|gov|mil|int|co\.uk|uk|de|fr|au|jp|cn|ru|br|mx|ca|nl|it|se|no|dk|fi|be|ch|at|es|pl|gr|cz|hu|pt|sk|si|ee|lv|lt|bg|ro|hr|rs|ba|mk|al|me|ad|sm|va|li|mc|lu|mt|ie|is|tr|cy|in|kr|tw|hk|sg|my|th|vn|ph|id|bd|pk|lk|np|bt|mm|kh|la|mn|uz|kz|kg|tj|tm|af|ir|iq|sa|ae|qa|kw|bh|om|ye|jo|sy|lb|il|ps|eg|ly|tn|dz|ma|sd|ss|et|so|dj|er|ke|ug|tz|rw|bi|cd|cg|cf|td|cm|gq|ga|st|gw|gn|sn|gm|sl|lr|ci|gh|tg|bj|ne|bf|ml|mr|cv|mz|mg|mu|sc|km|mw|zm|zw|bw|na|sz|ls|za|ao|...)  # TLD
        )
        (?:[^\s<>"'{}|\\^`\[\]]{1,256})?     # Rest of URL
        ''',
        re.VERBOSE
    )
    
    def __init__(self, min_url_length: int = 4, max_url_length: int = 2048):
        """
        Initialize the URL extractor.
        
        Args:
            min_url_length: Minimum length for extracted URLs
            max_url_length: Maximum length for extracted URLs
        """
        self.min_url_length = min_url_length
        self.max_url_length = max_url_length
        self.logger = logging.getLogger(__name__)
    
    def extract_urls_from_pdf(
        self,
        pdf_path: Union[str, Path],
        extract_from_annotations: bool = True,
        extract_from_text: bool = True,
        specific_pages: Optional[List[int]] = None,
        default_to_first_page: bool = True
    ) -> List[URLMatch]:
        """
        Extract all URLs from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file
            extract_from_annotations: Whether to extract URLs from annotations/links
            extract_from_text: Whether to extract URLs from text content
            specific_pages: List of specific page numbers to process (0-based). 
                          If None, behavior depends on default_to_first_page.
            default_to_first_page: If True and specific_pages is None, only process page 0.
                                 If False and specific_pages is None, process all pages.
        
        Returns:
            List of URLMatch objects containing found URLs and metadata
            
        Raises:
            URLExtractionError: If URL extraction fails
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If invalid parameters provided
        """
        try:
            # Validate inputs
            pdf_path = validate_pdf_path(pdf_path)
            
            if not extract_from_annotations and not extract_from_text:
                raise ValueError("At least one extraction method must be enabled")
            
            # Open PDF document
            doc = pymupdf.open(pdf_path)
            
            try:
                # Determine pages to process
                if specific_pages is None:
                    if default_to_first_page:
                        # Default behavior: process only the first page
                        pages_to_process = [0] if doc.page_count > 0 else []
                    else:
                        # Process all pages
                        pages_to_process = range(doc.page_count)
                else:
                    # Validate page numbers
                    for page_num in specific_pages:
                        if page_num < 0 or page_num >= doc.page_count:
                            raise ValueError(f"Invalid page number: {page_num}. Document has {doc.page_count} pages.")
                    pages_to_process = specific_pages
                
                all_urls = []
                
                # Process each page
                for page_num in pages_to_process:
                    page = doc[page_num]
                    
                    # Extract URLs from annotations/links
                    if extract_from_annotations:
                        annotation_urls = self._extract_urls_from_annotations(page, page_num)
                        all_urls.extend(annotation_urls)
                    
                    # Extract URLs from text content
                    if extract_from_text:
                        text_urls = self._extract_urls_from_text(page, page_num)
                        all_urls.extend(text_urls)
                
                # Deduplicate URLs while preserving order and prioritizing annotation URLs
                unique_urls = self._deduplicate_urls(all_urls)
                
                self.logger.info(f"Extracted {len(unique_urls)} unique URLs from {pdf_path}")
                return unique_urls
                
            finally:
                doc.close()
                
        except Exception as e:
            raise URLExtractionError(f"Failed to extract URLs from {pdf_path}: {str(e)}") from e
    
    def _extract_urls_from_annotations(self, page: pymupdf.Page, page_num: int) -> List[URLMatch]:
        """
        Extract URLs from PDF annotations and links.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            
        Returns:
            List of URLMatch objects from annotations
        """
        urls = []
        
        try:
            # Get all links on the page
            links = page.get_links()
            
            for link in links:
                # Check if link has URI
                if 'uri' in link and link['uri']:
                    uri = link['uri'].strip()
                    
                    # Validate URL
                    if self._is_valid_url(uri):
                        # Extract coordinates from 'from' rectangle
                        rect = link.get('from', pymupdf.Rect())
                        
                        url_match = URLMatch(
                            url=uri,
                            url_type=URLType.ANNOTATION,
                            page_number=page_num,
                            x0=rect.x0,
                            y0=rect.y0,
                            x1=rect.x1,
                            y1=rect.y1,
                            is_external=link.get('type') == 'uri',
                            link_type=link.get('type'),
                            xref=link.get('xref')
                        )
                        urls.append(url_match)
                        
        except Exception as e:
            self.logger.warning(f"Failed to extract URLs from annotations on page {page_num}: {str(e)}")
        
        return urls
    
    def _extract_urls_from_text(self, page: pymupdf.Page, page_num: int) -> List[URLMatch]:
        """
        Extract URLs from text content using regex.
        
        Args:
            page: PyMuPDF page object
            page_num: Page number (0-based)
            
        Returns:
            List of URLMatch objects from text
        """
        urls = []
        
        try:
            # Extract text from page
            text = page.get_text()
            
            # Find all URLs in text
            matches = self.URL_PATTERN.finditer(text)
            
            for match in matches:
                url = match.group().strip()
                
                # Clean and validate URL
                cleaned_url = self._clean_url(url)
                
                if self._is_valid_url(cleaned_url):
                    url_match = URLMatch(
                        url=cleaned_url,
                        url_type=URLType.TEXT,
                        page_number=page_num,
                        # No coordinates for text-based URLs as requested
                    )
                    urls.append(url_match)
                    
        except Exception as e:
            self.logger.warning(f"Failed to extract URLs from text on page {page_num}: {str(e)}")
        
        return urls
    
    def _clean_url(self, url: str) -> str:
        """
        Clean and normalize URL.
        
        Args:
            url: Raw URL string
            
        Returns:
            Cleaned URL string
        """
        # Remove trailing punctuation that's not part of URL
        url = re.sub(r'[.,;:!?]+$', '', url)
        
        # Add protocol if missing
        if not re.match(r'^https?://', url, re.IGNORECASE):
            if url.startswith('www.'):
                url = 'http://' + url
            elif re.match(r'^[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.', url):
                url = 'http://' + url
        
        return url
    
    def _is_valid_url(self, url: str) -> bool:
        """
        Validate if a string is a valid URL.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url or len(url) < self.min_url_length or len(url) > self.max_url_length:
            return False
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # Protocol
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # Domain
            r'localhost|'  # localhost
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # IP
            r'(?::\d+)?'  # Optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        return bool(url_pattern.match(url))
    
    def _deduplicate_urls(self, urls: List[URLMatch]) -> List[URLMatch]:
        """
        Remove duplicate URLs while preserving URLs with different coordinates or types.
        
        Args:
            urls: List of URLMatch objects
            
        Returns:
            List of unique URLMatch objects
        """
        seen_urls = set()
        unique_urls = []
        
        # Sort to prioritize annotation URLs over text URLs
        sorted_urls = sorted(urls, key=lambda x: (x.url, x.url_type != URLType.ANNOTATION))
        
        for url_match in sorted_urls:
            # Create a unique identifier that considers URL, type, page, and coordinates
            coords_key = None
            if url_match.url_type == URLType.ANNOTATION and all(
                coord is not None for coord in [url_match.x0, url_match.y0, url_match.x1, url_match.y1]
            ):
                # Round coordinates to avoid floating point precision issues
                coords_key = (
                    round(url_match.x0, 1), 
                    round(url_match.y0, 1), 
                    round(url_match.x1, 1), 
                    round(url_match.y1, 1)
                )
            
            unique_key = (
                url_match.url,
                url_match.url_type.value,
                url_match.page_number,
                coords_key
            )
            
            if unique_key not in seen_urls:
                seen_urls.add(unique_key)
                unique_urls.append(url_match)
        
        return unique_urls


def extract_urls_from_pdf(
    pdf_path: Union[str, Path],
    extract_from_annotations: bool = True,
    extract_from_text: bool = True,
    specific_pages: Optional[List[int]] = None,
    default_to_first_page: bool = True
) -> List[Dict[str, Any]]:
    """
    Convenience function to extract URLs from a PDF document.
    
    Args:
        pdf_path: Path to the PDF file
        extract_from_annotations: Whether to extract URLs from annotations/links
        extract_from_text: Whether to extract URLs from text content
        specific_pages: List of specific page numbers to process (0-based).
                       If None, behavior depends on default_to_first_page.
        default_to_first_page: If True and specific_pages is None, only process page 0 (first page).
                             If False and specific_pages is None, process all pages.
                             Default is True.
    
    Returns:
        List of dictionaries containing URL data
        
    Raises:
        URLExtractionError: If URL extraction fails
    """
    extractor = PDFURLExtractor()
    url_matches = extractor.extract_urls_from_pdf(
        pdf_path=pdf_path,
        extract_from_annotations=extract_from_annotations,
        extract_from_text=extract_from_text,
        specific_pages=specific_pages,
        default_to_first_page=default_to_first_page
    )
    
    return [url_match.to_dict() for url_match in url_matches]