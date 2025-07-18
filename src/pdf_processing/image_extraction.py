"""
PDF image extraction utilities.

This module provides functions for extracting the first page of a PDF document
as a high-quality image using PyMuPDF (fitz).
"""

import io
import base64
import pathlib
from typing import Union, Optional, Tuple
from PIL import Image
import pymupdf

try:
    import imagehash
except ImportError:
    imagehash = None

from .hashing import calculate_sha1


def extract_first_page_image(
    pdf_path: Union[str, pathlib.Path],
    output_path: Optional[Union[str, pathlib.Path]] = None,
    dpi: int = 150,
    format: str = "PNG"
) -> str:
    """
    Extract the first page of a PDF as an image.
    
    Args:
        pdf_path: Path to the PDF file
        output_path: Path where the image should be saved. If None, saves in same directory as PDF
        dpi: Resolution in dots per inch (default: 150)
        format: Image format (default: "PNG")
        
    Returns:
        Path to the saved image file
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If the PDF has no pages or invalid parameters
        RuntimeError: If PDF cannot be opened or image cannot be extracted
        
    Example:
        >>> image_path = extract_first_page_image("document.pdf", dpi=200)
        >>> print(f"Image saved to: {image_path}")
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    if dpi <= 0:
        raise ValueError("DPI must be positive")
    
    # Generate output path if not provided
    if output_path is None:
        output_path = pdf_path.parent / f"{pdf_path.stem}_page1.{format.lower()}"
    else:
        output_path = pathlib.Path(output_path)
    
    try:
        # Open PDF document
        doc = pymupdf.open(str(pdf_path))
        
        if len(doc) == 0:
            raise ValueError("PDF document has no pages")
        
        # Get first page
        page = doc[0]
        
        # Calculate scale factor from DPI
        # PyMuPDF uses 72 DPI as default, so scale = target_dpi / 72
        scale = dpi / 72.0
        
        # Create transformation matrix for scaling
        matrix = pymupdf.Matrix(scale, scale)
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix)
        
        # Save the image
        pixmap.save(str(output_path))
        
        # Clean up
        doc.close()
        
        return str(output_path)
        
    except Exception as e:
        raise RuntimeError(f"Error extracting image from PDF: {e}")


def extract_first_page_as_pil(
    pdf_path: Union[str, pathlib.Path],
    dpi: int = 150
) -> Image.Image:
    """
    Extract the first page of a PDF as a PIL Image object.
    
    Args:
        pdf_path: Path to the PDF file
        dpi: Resolution in dots per inch (default: 150)
        
    Returns:
        PIL Image object of the first page
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If the PDF has no pages or invalid parameters
        RuntimeError: If PDF cannot be opened or image cannot be extracted
        
    Example:
        >>> pil_image = extract_first_page_as_pil("document.pdf")
        >>> pil_image.show()
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    if dpi <= 0:
        raise ValueError("DPI must be positive")
    
    try:
        # Open PDF document
        doc = pymupdf.open(str(pdf_path))
        
        if len(doc) == 0:
            raise ValueError("PDF document has no pages")
        
        # Get first page
        page = doc[0]
        
        # Calculate scale factor from DPI
        scale = dpi / 72.0
        
        # Create transformation matrix for scaling
        matrix = pymupdf.Matrix(scale, scale)
        
        # Render page to pixmap
        pixmap = page.get_pixmap(matrix=matrix)
        
        # Convert to PIL Image
        img_data = pixmap.tobytes("png")
        pil_image = Image.open(io.BytesIO(img_data))
        
        # Clean up
        doc.close()
        
        return pil_image
        
    except Exception as e:
        raise RuntimeError(f"Error extracting image from PDF: {e}")


def extract_pages_as_base64_images(
    pdf_path: Union[str, pathlib.Path],
    pages: Optional[list] = None,
    dpi: int = 150,
    format: str = "PNG"
) -> list:
    """
    Extract specified pages from a PDF as base64-encoded images.
    
    Args:
        pdf_path: Path to the PDF file
        pages: List of page numbers to extract (0-based). If None, extracts all pages
        dpi: Resolution in dots per inch (default: 150)
        format: Image format (default: "PNG")
        
    Returns:
        List of dictionaries containing page_number and base64_data
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If the PDF has no pages or invalid parameters
        RuntimeError: If PDF cannot be opened or image cannot be extracted
        
    Example:
        >>> images = extract_pages_as_base64_images("document.pdf", pages=[0, 1])
        >>> print(f"Extracted {len(images)} images as base64")
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    if dpi <= 0:
        raise ValueError("DPI must be positive")
    
    try:
        # Open PDF document
        doc = pymupdf.open(str(pdf_path))
        
        if len(doc) == 0:
            raise ValueError("PDF document has no pages")
        
        # Determine pages to extract
        if pages is None:
            pages = list(range(len(doc)))
        else:
            # Validate page numbers
            for page_num in pages:
                if page_num < 0 or page_num >= len(doc):
                    raise ValueError(f"Invalid page number: {page_num}. Document has {len(doc)} pages.")
        
        images = []
        
        # Extract each page
        for page_num in pages:
            page = doc[page_num]
            
            # Calculate scale factor from DPI
            scale = dpi / 72.0
            
            # Create transformation matrix for scaling
            matrix = pymupdf.Matrix(scale, scale)
            
            # Render page to pixmap
            pixmap = page.get_pixmap(matrix=matrix)
            
            # Convert to base64
            img_data = pixmap.tobytes(format.lower())
            base64_data = base64.b64encode(img_data).decode('utf-8')
            
            images.append({
                'page_number': page_num,
                'base64_data': base64_data,
                'format': format.lower()
            })
        
        # Clean up
        doc.close()
        
        return images
        
    except Exception as e:
        raise RuntimeError(f"Error extracting images from PDF: {e}")


def save_image_with_sha1_filename(
    image: Image.Image,
    output_dir: Union[str, pathlib.Path],
    format: str = "PNG"
) -> str:
    """
    Save a PIL Image with SHA1 hash of the image data as the filename.
    
    Args:
        image: PIL Image object to save
        output_dir: Directory to save the image in
        format: Image format (default: "PNG")
        
    Returns:
        Path to the saved image file
        
    Raises:
        ValueError: If output directory doesn't exist or invalid parameters
        RuntimeError: If image cannot be saved
        
    Example:
        >>> pil_image = extract_first_page_as_pil("document.pdf")
        >>> saved_path = save_image_with_sha1_filename(pil_image, "./images/")
        >>> print(f"Image saved to: {saved_path}")
    """
    output_dir = pathlib.Path(output_dir)
    
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    if not output_dir.is_dir():
        raise ValueError(f"Output path is not a directory: {output_dir}")
    
    try:
        # Convert image to bytes
        img_buffer = io.BytesIO()
        image.save(img_buffer, format=format.upper())
        img_bytes = img_buffer.getvalue()
        
        # Calculate SHA1 hash of image data
        import hashlib
        sha1_hash = hashlib.sha1(img_bytes).hexdigest()
        
        # Create filename with SHA1 hash
        filename = f"{sha1_hash}.{format.lower()}"
        output_path = output_dir / filename
        
        # Save the image
        image.save(str(output_path), format=format.upper())
        
        return str(output_path)
        
    except Exception as e:
        raise RuntimeError(f"Error saving image with SHA1 filename: {e}")


def calculate_image_phash(image: Image.Image) -> str:
    """
    Calculate perceptual hash (phash) of a PIL Image.
    
    Args:
        image: PIL Image object to hash
        
    Returns:
        Perceptual hash as hexadecimal string
        
    Raises:
        ImportError: If imagehash library is not installed
        RuntimeError: If hash calculation fails
        
    Example:
        >>> pil_image = extract_first_page_as_pil("document.pdf")
        >>> phash = calculate_image_phash(pil_image)
        >>> print(f"Perceptual hash: {phash}")
    """
    if imagehash is None:
        raise ImportError("imagehash library is required for perceptual hashing. Install with: pip install imagehash")
    
    try:
        # Calculate perceptual hash using imagehash library
        phash = imagehash.phash(image)
        return str(phash)
        
    except Exception as e:
        raise RuntimeError(f"Error calculating perceptual hash: {e}")


def get_pdf_page_count(pdf_path: Union[str, pathlib.Path]) -> int:
    """
    Get the number of pages in a PDF document.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Number of pages in the PDF
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        RuntimeError: If PDF cannot be opened
        
    Example:
        >>> page_count = get_pdf_page_count("document.pdf")
        >>> print(f"PDF has {page_count} pages")
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    try:
        doc = pymupdf.open(str(pdf_path))
        page_count = len(doc)
        doc.close()
        return page_count
        
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {e}")


def get_pdf_page_dimensions(pdf_path: Union[str, pathlib.Path], page_number: int = 0) -> Tuple[float, float]:
    """
    Get the dimensions of a PDF page in points.
    
    Args:
        pdf_path: Path to the PDF file
        page_number: Page number (0-based, default: 0 for first page)
        
    Returns:
        Tuple of (width, height) in points
        
    Raises:
        FileNotFoundError: If the PDF file does not exist
        ValueError: If page number is invalid
        RuntimeError: If PDF cannot be opened
        
    Example:
        >>> width, height = get_pdf_page_dimensions("document.pdf")
        >>> print(f"Page dimensions: {width}x{height} points")
    """
    pdf_path = pathlib.Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    try:
        doc = pymupdf.open(str(pdf_path))
        
        if page_number < 0 or page_number >= len(doc):
            raise ValueError(f"Invalid page number: {page_number}. PDF has {len(doc)} pages")
        
        page = doc[page_number]
        rect = page.rect
        dimensions = (rect.width, rect.height)
        
        doc.close()
        return dimensions
        
    except Exception as e:
        raise RuntimeError(f"Error reading PDF: {e}")