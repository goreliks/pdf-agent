"""
LangGraph PDF Processing Agent

This module implements a LangGraph agent that processes PDFs in parallel using
multiple nodes for hash calculation, image extraction, URL extraction, and 
perceptual hashing.
"""

import time
import pathlib
from typing import Dict, Any, Optional, List

from langgraph.graph import StateGraph, START, END

try:
    # Try relative imports first (when run as module)
    from .agent_schemas import (
        PDFProcessingState, 
        PDFProcessingInput, 
        PDFProcessingOutput,
        PDFHashData,
        ExtractedImage,
        ExtractedURL
    )

    from . import (
        calculate_file_hashes,
        extract_pages_as_base64_images,
        extract_first_page_as_pil,
        save_image_with_sha1_filename,
        calculate_image_phash,
        get_pdf_page_count,
        extract_urls_from_pdf,
        validate_pdf_path,
        ensure_output_directory
    )
except ImportError:
    # Fallback to absolute imports (when run directly in IDE)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    from pdf_processing.agent_schemas import (
        PDFProcessingState, 
        PDFProcessingInput, 
        PDFProcessingOutput,
        PDFHashData,
        ExtractedImage,
        ExtractedURL
    )

    from pdf_processing import (
        calculate_file_hashes,
        extract_pages_as_base64_images,
        extract_first_page_as_pil,
        save_image_with_sha1_filename,
        calculate_image_phash,
        get_pdf_page_count,
        extract_urls_from_pdf,
        validate_pdf_path,
        ensure_output_directory
    )


def validation_node(state: PDFProcessingState) -> Dict[str, Any]:
    """
    Validation node that validates PDF path, creates output directory,
    calculates file hashes, and gets page count.
    
    This node runs first and provides data needed by parallel processing nodes.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        Dictionary with validation results and PDF metadata
    """
    try:
        # Validate PDF path
        pdf_path = validate_pdf_path(state["pdf_path"])
        
        # Ensure output directory exists
        output_dir = pathlib.Path(state["output_directory"])
        ensure_output_directory(output_dir)
        
        # Calculate file hashes
        hashes = calculate_file_hashes(pdf_path)
        
        # Create hash data
        pdf_hash = PDFHashData(
            sha1=hashes["sha1"],
            md5=hashes["md5"]
        )
        
        # Get page count
        page_count = get_pdf_page_count(pdf_path)
        
        return {
            "pdf_hash": pdf_hash,
            "page_count": page_count
        }
        
    except Exception as e:
        error_msg = f"Error in validation: {str(e)}"
        return {
            "errors": [error_msg]
        }


def image_extraction_node(state: PDFProcessingState) -> Dict[str, Any]:
    """
    Node for extracting images from PDF pages, converting to base64, 
    calculating phash, and saving with SHA1 filenames.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        Dictionary with extracted image data
    """
    try:
        pdf_path = state["pdf_path"]
        output_dir = pathlib.Path(state["output_directory"])
        
        # Determine pages to process
        pages_to_process = state.get("pages_to_process")
        if pages_to_process is None:
            # Process all pages if not specified
            page_count = state.get("page_count")
            if page_count is None:
                raise ValueError("Page count not available from validation node")
            pages_to_process = list(range(page_count))
        
        # Extract images as base64
        base64_images = extract_pages_as_base64_images(
            pdf_path=pdf_path,
            pages=pages_to_process,
            dpi=150,
            format="PNG"
        )
        
        extracted_images = []
        
        for img_data in base64_images:
            try:
                # Convert base64 back to PIL image for phash calculation and saving
                import base64
                from PIL import Image
                import io
                
                img_bytes = base64.b64decode(img_data["base64_data"])
                pil_image = Image.open(io.BytesIO(img_bytes))
                
                # Calculate perceptual hash
                phash = calculate_image_phash(pil_image)
                
                # Save image with SHA1 filename
                saved_path = save_image_with_sha1_filename(
                    image=pil_image,
                    output_dir=output_dir,
                    format="PNG"
                )
                
                # Extract SHA1 from saved path filename
                image_sha1 = pathlib.Path(saved_path).stem
                
                # Create extracted image object
                extracted_image = ExtractedImage(
                    page_number=img_data["page_number"],
                    base64_data=img_data["base64_data"],
                    format=img_data["format"],
                    phash=phash,
                    saved_path=saved_path,
                    image_sha1=image_sha1
                )
                
                extracted_images.append(extracted_image)
                
            except Exception as e:
                # Log error but continue with other images
                error_msg = f"Error processing image for page {img_data['page_number']}: {str(e)}"
                print(f"Warning: {error_msg}")
        
        return {
            "extracted_images": extracted_images
        }
        
    except Exception as e:
        error_msg = f"Error in image_extraction: {str(e)}"
        return {
            "errors": [error_msg]
        }


def url_extraction_node(state: PDFProcessingState) -> Dict[str, Any]:
    """
    Node for extracting URLs from PDF annotations and text.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        Dictionary with extracted URL data
    """
    try:
        pdf_path = state["pdf_path"]
        
        # Determine pages to process
        pages_to_process = state.get("pages_to_process")
        
        # Extract URLs from PDF
        try:
            if pages_to_process:
                # Extract from specific pages
                url_data = extract_urls_from_pdf(
                    pdf_path=pdf_path,
                    extract_from_annotations=True,
                    extract_from_text=True,
                    specific_pages=pages_to_process
                )
            else:
                # Extract from all pages
                url_data = extract_urls_from_pdf(
                    pdf_path=pdf_path,
                    extract_from_annotations=True,
                    extract_from_text=True,
                    default_to_first_page=False
                )
        except Exception as e:
            # If URL extraction fails, return empty list instead of crashing
            print(f"Warning: URL extraction failed: {e}")
            url_data = []
        
        # Convert to ExtractedURL objects
        extracted_urls = []
        for url_dict in url_data:
            extracted_url = ExtractedURL(
                url=url_dict["url"],
                page_number=url_dict["page_number"],
                url_type=url_dict["type"],
                coordinates=url_dict.get("coordinates"),
                is_external=url_dict.get("is_external")
            )
            extracted_urls.append(extracted_url)
        
        return {
            "extracted_urls": extracted_urls
        }
        
    except Exception as e:
        error_msg = f"Error in url_extraction: {str(e)}"
        return {
            "errors": [error_msg]
        }


def aggregation_node(state: PDFProcessingState) -> Dict[str, Any]:
    """
    Final node that validates all processing completed successfully.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        Dictionary with any final validation errors
    """
    try:
        # Check for any errors
        errors = state.get("errors", [])
        
        # Validate that we have the expected data
        if not state.get("pdf_hash"):
            errors = errors + ["PDF hash not calculated"]
        if not state.get("page_count"):
            errors = errors + ["Page count not determined"]
        
        # Return any additional errors found
        if errors != state.get("errors", []):
            return {
                "errors": errors[len(state.get("errors", [])):]  # Only new errors
            }
        
        # No additional errors to report
        return {}
        
    except Exception as e:
        error_msg = f"Error in aggregation: {str(e)}"
        return {
            "errors": [error_msg]
        }


def create_pdf_processing_graph() -> StateGraph:
    """
    Create the LangGraph for PDF processing.
    
    Graph structure: validation -> [image_extraction, url_extraction] -> aggregation
    
    Returns:
        Compiled StateGraph for PDF processing
    """
    # Create the state graph
    builder = StateGraph(PDFProcessingState)
    
    # Add all processing nodes
    builder.add_node("validation", validation_node)
    builder.add_node("image_extraction", image_extraction_node)
    builder.add_node("url_extraction", url_extraction_node)
    builder.add_node("aggregation", aggregation_node)
    
    # Create the flow: validation first, then parallel processing, then aggregation
    builder.add_edge(START, "validation")
    
    # After validation, dispatch to parallel processing nodes
    builder.add_edge("validation", "image_extraction")
    builder.add_edge("validation", "url_extraction")
    
    # Both parallel nodes feed into aggregation
    builder.add_edge("image_extraction", "aggregation")
    builder.add_edge("url_extraction", "aggregation")
    
    # Aggregation node leads to END
    builder.add_edge("aggregation", END)
    
    # Compile the graph
    return builder.compile()


def process_pdf_with_agent(
    pdf_path: str,
    pages_to_process: Optional[List[int]] = None,
    output_directory: str = "./extracted_images"
) -> PDFProcessingOutput:
    """
    Process a PDF using the LangGraph agent with parallel processing.
    
    Args:
        pdf_path: Path to the PDF file to process
        pages_to_process: List of pages to process (0-based), None for all pages
        output_directory: Directory to save extracted images
        
    Returns:
        PDFProcessingOutput with all processing results
        
    Example:
        >>> result = process_pdf_with_agent("document.pdf", pages_to_process=[0, 1])
        >>> print(f"Processed {len(result.extracted_images)} images")
        >>> print(f"Found {len(result.extracted_urls)} URLs")
    """
    # Create the processing graph
    graph = create_pdf_processing_graph()
    
    # Prepare initial state
    initial_state = {
        "pdf_path": pdf_path,
        "pages_to_process": pages_to_process,
        "output_directory": output_directory,
        "pdf_hash": None,
        "page_count": None,
        "extracted_images": [],
        "extracted_urls": [],
        "errors": []
    }
    
    # Execute the graph
    start_time = time.time()
    final_state = graph.invoke(initial_state)
    total_time = time.time() - start_time
    
    # Determine overall success
    errors = final_state.get("errors", [])
    success = len(errors) == 0
    
    # Create output
    return PDFProcessingOutput(
        success=success,
        pdf_path=pdf_path,
        pdf_hash=final_state.get("pdf_hash"),
        page_count=final_state.get("page_count"),
        extracted_images=final_state.get("extracted_images", []),
        extracted_urls=final_state.get("extracted_urls", []),
        errors=errors,
        total_processing_time=total_time
    )


# Main execution function for IDE usage
def main():
    """Main function for running the PDF processing agent in IDE."""
    
    # Configuration for IDE execution
    pdf_path = "tests/test_mal_one.pdf"
    output_directory = "./extracted_images"
    
    print("=" * 60)
    print("PDF Processing LangGraph Agent - IDE Execution")
    print("=" * 60)
    print(f"Processing PDF: {pdf_path}")
    print(f"Output directory: {output_directory}")
    print("Starting processing...")
    
    # Process the PDF
    result = process_pdf_with_agent(pdf_path, output_directory=output_directory)
    
    # Print results
    print(f"\n=== PDF Processing Results ===")
    print(f"Success: {result.success}")
    print(f"Total processing time: {result.total_processing_time:.2f}s")
    
    if result.pdf_hash:
        print(f"PDF SHA1: {result.pdf_hash.sha1}")
        print(f"PDF MD5: {result.pdf_hash.md5}")
    
    print(f"Page count: {result.page_count}")
    print(f"Extracted images: {len(result.extracted_images)}")
    print(f"Extracted URLs: {len(result.extracted_urls)}")
    
    if result.errors:
        print(f"\nErrors encountered:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print(f"\n✓ No errors encountered!")
    
    # Print detailed results
    if result.extracted_images:
        print(f"\n=== Image Details ===")
        for i, img in enumerate(result.extracted_images, 1):
            print(f"Image {i}:")
            print(f"  Page: {img.page_number}")
            print(f"  Format: {img.format}")
            print(f"  Perceptual Hash: {img.phash}")
            print(f"  Saved to: {img.saved_path}")
            print(f"  Image SHA1: {img.image_sha1}")
            print(f"  Base64 length: {len(img.base64_data)} chars")
    
    if result.extracted_urls:
        print(f"\n=== URL Details ===")
        for i, url in enumerate(result.extracted_urls, 1):
            print(f"URL {i}:")
            print(f"  URL: {url.url}")
            print(f"  Page: {url.page_number}")
            print(f"  Type: {url.url_type}")
            if url.coordinates:
                print(f"  Coordinates: {url.coordinates}")
            if url.is_external is not None:
                print(f"  External: {url.is_external}")
    
    # Print processing summary
    print(f"\n=== Processing Summary ===")
    print(f"✓ PDF validation and hash calculation completed")
    print(f"✓ Image extraction: {len(result.extracted_images)} images processed")
    print(f"✓ URL extraction: {len(result.extracted_urls)} URLs found")
    
    return result


if __name__ == "__main__":
    main() 