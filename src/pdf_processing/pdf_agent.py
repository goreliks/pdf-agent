"""
LangGraph PDF Processing Agent

This module implements a LangGraph agent that processes PDFs in parallel using
multiple nodes for hash calculation, image extraction, URL extraction, and 
perceptual hashing.
"""

import time
import pathlib
from typing import Dict, Any, Optional, List
from pydantic import ValidationError

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
    calculates file hashes, gets page count, and converts pages_to_process.
    
    This node runs first and provides data needed by parallel processing nodes.
    It also converts the user's "number of pages" input to actual 0-based page numbers.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        Dictionary with validation results and PDF metadata
    """
    try:
        # Validate PDF path
        pdf_path = validate_pdf_path(state["pdf_path"])
        
        # Handle output directory - auto-generate if None (for LangGraph Studio usage)
        output_directory = state.get("output_directory")
        if output_directory is None or output_directory == "":
            import time
            timestamp = int(time.time())
            output_directory = f"./extracted_images_{timestamp}"
            print(f"Auto-generated output directory: {output_directory}")
        
        # Ensure output directory exists
        output_dir = pathlib.Path(output_directory)
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
        
        # Convert pages_to_process from "number of pages" to actual page numbers
        pages_to_process = state.get("pages_to_process")
        
        if pages_to_process is not None:
            # pages_to_process comes from input as int (number of pages from beginning)
            # Convert to list of actual 0-based page numbers
            if isinstance(pages_to_process, int):
                # User wants N pages from the beginning
                pages_count = min(pages_to_process, page_count)  # Don't exceed available pages
                actual_pages = list(range(pages_count))  # [0, 1, 2, ..., N-1]
            else:
                # Fallback: assume it's already a list (for backward compatibility)
                actual_pages = pages_to_process
        else:
            # Default: process only first page
            actual_pages = [0] if page_count > 0 else []
        
        # Validate that requested pages exist
        if actual_pages:
            invalid_pages = [p for p in actual_pages if p >= page_count]
            if invalid_pages:
                raise ValueError(f"Requested pages {invalid_pages} don't exist. PDF has {page_count} pages (0-{page_count-1})")
        
        return {
            "pdf_hash": pdf_hash,
            "page_count": page_count,
            "pages_to_process": actual_pages,  # Now contains actual 0-based page numbers
            "output_directory": output_directory  # Include the (possibly auto-generated) output directory
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
        
        # Safe access to output_directory
        output_directory = state.get("output_directory")
        if output_directory is None:
            raise ValueError("output_directory is None in state - auto-generation failed")
        
        output_dir = pathlib.Path(output_directory)
        
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


def aggregation_node(state: PDFProcessingState) -> PDFProcessingOutput:
    """
    Aggregation node that collects all processing results and validates completeness.
    
    This node runs last and converts the internal state to the final output schema.
    
    Args:
        state: Current state of the PDF processing workflow
        
    Returns:
        PDFProcessingOutput with complete processing results
    """
    try:
        # Determine overall success based on errors
        errors = state.get("errors", [])
        success = len(errors) == 0
        
        # Validate that required processing was completed
        if success:
            # Check if we have required data when processing was successful
            if state.get("pdf_hash") is None:
                errors.append("PDF hash calculation was not completed")
                success = False
            
            if state.get("page_count") is None:
                errors.append("Page count determination was not completed")
                success = False
        
        # Create the final output using the PDFProcessingOutput schema
        return PDFProcessingOutput(
            success=success,
            pdf_path=state["pdf_path"],
            pdf_hash=state.get("pdf_hash"),
            page_count=state.get("page_count"),
            extracted_images=state.get("extracted_images", []),
            extracted_urls=state.get("extracted_urls", []),
            errors=errors,
            total_processing_time=None  # Will be set by the main function
        )
        
    except Exception as e:
        # If aggregation itself fails, return a failure result
        error_msg = f"Error in aggregation: {str(e)}"
        return PDFProcessingOutput(
            success=False,
            pdf_path=state.get("pdf_path", "unknown"),
            errors=[error_msg],
            total_processing_time=None
        )


def create_pdf_processing_graph() -> StateGraph:
    """
    Create the LangGraph for PDF processing with proper input/output schemas.
    
    Graph structure: validation -> [image_extraction, url_extraction] -> aggregation
    
    Input Schema: PDFProcessingInput (user-facing fields only)
    Output Schema: PDFProcessingOutput (structured results)
    Internal State: PDFProcessingState (all processing fields)
    
    Returns:
        Compiled StateGraph for PDF processing
    """
    # Create the state graph with explicit input and output schemas
    builder = StateGraph(
        state_schema=PDFProcessingState,
        input_schema=PDFProcessingInput,
        output_schema=PDFProcessingOutput
    )
    
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
    input_data: PDFProcessingInput
) -> PDFProcessingOutput:
    """
    Process a PDF using the LangGraph agent with parallel processing.
    
    Args:
        input_data: PDFProcessingInput with validated input parameters
        
    Returns:
        PDFProcessingOutput with all processing results
        
    Example:
        >>> from pdf_processing.agent_schemas import PDFProcessingInput
        >>> input_data = PDFProcessingInput(
        ...     pdf_path="document.pdf",
        ...     pages_to_process=3,  # Process first 3 pages
        ...     output_directory="./my_images"
        ... )
        >>> result = process_pdf_with_agent(input_data)
        >>> print(f"Processed {len(result.extracted_images)} images")
        >>> print(f"Found {len(result.extracted_urls)} URLs")
    """
    # Input is already validated as PDFProcessingInput by function signature
    # No need for additional validation
    
    # Create the processing graph
    graph = create_pdf_processing_graph()
    
    # Convert PDFProcessingInput to internal PDFProcessingState format
    # Note: pages_to_process conversion will happen in validation_node
    initial_state = {
        "pdf_path": input_data.pdf_path,
        "pages_to_process": input_data.pages_to_process,  # Will be converted in validation_node
        "output_directory": input_data.output_directory,
        "pdf_hash": None,
        "page_count": None,
        "extracted_images": [],
        "extracted_urls": [],
        "errors": []
    }
    
    # Execute the graph with manual state conversion
    start_time = time.time()
    final_state = graph.invoke(initial_state)
    total_time = time.time() - start_time
    
    # Convert final state to PDFProcessingOutput
    # The aggregation node already returns a PDFProcessingOutput, but we need to update the time
    if isinstance(final_state, PDFProcessingOutput):
        # Update the processing time
        return PDFProcessingOutput(
            **final_state.model_dump(),
            total_processing_time=total_time
        )
    else:
        # Fallback: manually create output from state dict
        errors = final_state.get("errors", [])
        success = len(errors) == 0
        
        return PDFProcessingOutput(
            success=success,
            pdf_path=input_data.pdf_path,
            pdf_hash=final_state.get("pdf_hash"),
            page_count=final_state.get("page_count"),
            extracted_images=final_state.get("extracted_images", []),
            extracted_urls=final_state.get("extracted_urls", []),
            errors=errors,
            total_processing_time=total_time
        )


# Backward compatibility wrapper
def process_pdf_with_agent_legacy(
    pdf_path: str,
    pages_to_process: Optional[List[int]] = None,
    output_directory: str = "./extracted_images"
) -> PDFProcessingOutput:
    """
    Legacy wrapper for backward compatibility.
    
    DEPRECATED: Use process_pdf_with_agent(PDFProcessingInput(...)) instead.
    
    Args:
        pdf_path: Path to the PDF file to process
        pages_to_process: List of pages to process (0-based), None for all pages
        output_directory: Directory to save extracted images
        
    Returns:
        PDFProcessingOutput with all processing results
    """
    import warnings
    warnings.warn(
        "process_pdf_with_agent_legacy is deprecated. "
        "Use process_pdf_with_agent(PDFProcessingInput(...)) instead.",
        DeprecationWarning,
        stacklevel=2
    )
    
    # Convert old-style parameters to new schema format
    # Old: pages_to_process was List[int] (specific page numbers)
    # New: pages_to_process is int (number of pages from beginning)
    if pages_to_process is None:
        # Default: process only first page
        pages_count = 1
    else:
        # Convert list of page numbers to count
        # Assume user wanted contiguous pages from beginning
        if pages_to_process:
            max_page = max(pages_to_process) + 1  # Convert 0-based to count
            pages_count = max_page
        else:
            pages_count = 1
    
    # Create input using new schema
    input_data = PDFProcessingInput(
        pdf_path=pdf_path,
        pages_to_process=pages_count,
        output_directory=output_directory
    )
    
    return process_pdf_with_agent(input_data)


# Main execution function for IDE usage
def main():
    """Main function for running the PDF processing agent in IDE."""
    
    # Configuration for IDE execution
    pdf_path = "tests/test_mal_one.pdf"
    output_directory = "./extracted_images"
    
    print("=" * 60)
    print("PDF Processing LangGraph Agent - Schema-Based IDE Execution")
    print("=" * 60)
    print(f"Processing PDF: {pdf_path}")
    print(f"Output directory: {output_directory}")
    print("Starting processing with schema validation...")
    
    try:
        # Create validated input using the schema
        input_data = PDFProcessingInput(
            pdf_path=pdf_path,
            pages_to_process=1,  # Process only first page
            output_directory=output_directory
        )
        
        print(f"✅ Input validation successful")
        print(f"   PDF Path: {input_data.pdf_path}")
        print(f"   Pages to process: {input_data.pages_to_process} (from beginning)")
        print(f"   Output Dir: {input_data.output_directory}")
        
        # Process the PDF using schema-based approach
        result = process_pdf_with_agent(input_data)
        
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
        print(f"✓ Schema validation: Input and output validated successfully")
        
        return result
        
    except ValidationError as e:
        print(f"\n❌ Input validation failed:")
        for error in e.errors():
            print(f"  - {error['loc'][0]}: {error['msg']}")
        return None
        
    except Exception as e:
        print(f"\n❌ Processing failed: {e}")
        return None


# Export the app for LangGraph Studio
app = create_pdf_processing_graph()


if __name__ == "__main__":
    main() 