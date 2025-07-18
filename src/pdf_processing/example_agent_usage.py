#!/usr/bin/env python3
"""
Example usage of the PDF Processing LangGraph Agent.

This script demonstrates how to use the LangGraph agent for parallel
PDF processing including hash calculation, image extraction, URL extraction,
and perceptual hashing.
"""

import json
import time
from pathlib import Path

from pdf_processing import process_pdf_with_agent, create_pdf_processing_graph


def example_basic_usage():
    """Basic usage example with a simple PDF."""
    print("=" * 70)
    print("PDF Processing LangGraph Agent - Basic Usage Example")
    print("=" * 70)
    
    # Example PDF path (replace with your actual PDF)
    pdf_path = "sample.pdf"
    output_directory = "./demo_extracted_images"
    
    try:
        print(f"Processing PDF: {pdf_path}")
        print(f"Output directory: {output_directory}")
        print("\nStarting parallel processing...")
        
        # Process the PDF using the LangGraph agent
        result = process_pdf_with_agent(
            pdf_path=pdf_path,
            pages_to_process=None,  # Process all pages
            output_directory=output_directory
        )
        
        # Display results
        print(f"\n=== Processing Results ===")
        print(f"✓ Success: {result.success}")
        print(f"✓ Total processing time: {result.total_processing_time:.2f}s")
        
        if result.pdf_hash:
            print(f"✓ PDF SHA1: {result.pdf_hash.sha1}")
            print(f"✓ PDF MD5: {result.pdf_hash.md5}")
        
        print(f"✓ Total pages: {result.page_count}")
        print(f"✓ Extracted images: {len(result.extracted_images)}")
        print(f"✓ Extracted URLs: {len(result.extracted_urls)}")
        
        # Show details of extracted images
        if result.extracted_images:
            print(f"\n=== Extracted Images Details ===")
            for i, img in enumerate(result.extracted_images[:3], 1):  # Show first 3
                print(f"Image {i}:")
                print(f"  Page: {img.page_number}")
                print(f"  Format: {img.format}")
                print(f"  Perceptual Hash: {img.phash}")
                print(f"  Saved to: {img.saved_path}")
                print(f"  Image SHA1: {img.image_sha1}")
        
        # Show details of extracted URLs
        if result.extracted_urls:
            print(f"\n=== Extracted URLs Details ===")
            for i, url in enumerate(result.extracted_urls[:5], 1):  # Show first 5
                print(f"URL {i}:")
                print(f"  URL: {url.url}")
                print(f"  Page: {url.page_number}")
                print(f"  Type: {url.url_type}")
                if url.coordinates:
                    print(f"  Coordinates: {url.coordinates}")
        
        # Show processing summary
        print(f"\n=== Processing Summary ===")
        print(f"✓ PDF validation and hash calculation completed")
        print(f"✓ Image extraction: {len(result.extracted_images)} images processed")
        print(f"✓ URL extraction: {len(result.extracted_urls)} URLs found")
        
        # Show any errors
        if result.errors:
            print(f"\n=== Errors ===")
            for error in result.errors:
                print(f"✗ {error}")
                
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
        print("Please provide a valid PDF file path or create a sample PDF.")
    except Exception as e:
        print(f"Error: {e}")


def example_specific_pages():
    """Example processing only specific pages."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Specific Pages Example")
    print("=" * 70)
    
    pdf_path = "sample.pdf"
    pages_to_process = [0, 1, 2]  # Process only first 3 pages
    output_directory = "./demo_specific_pages"
    
    try:
        print(f"Processing PDF: {pdf_path}")
        print(f"Pages to process: {pages_to_process}")
        print(f"Output directory: {output_directory}")
        
        result = process_pdf_with_agent(
            pdf_path=pdf_path,
            pages_to_process=pages_to_process,
            output_directory=output_directory
        )
        
        print(f"\n=== Results for Specific Pages ===")
        print(f"Success: {result.success}")
        print(f"Processing time: {result.total_processing_time:.2f}s")
        print(f"Images extracted: {len(result.extracted_images)}")
        print(f"URLs found: {len(result.extracted_urls)}")
        
        # Verify that only specified pages were processed
        if result.extracted_images:
            processed_pages = [img.page_number for img in result.extracted_images]
            print(f"Pages actually processed for images: {processed_pages}")
        
        if result.extracted_urls:
            url_pages = list(set(url.page_number for url in result.extracted_urls))
            print(f"Pages with URLs found: {url_pages}")
            
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")


def example_graph_visualization():
    """Example showing how to work with the LangGraph directly."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Graph Visualization Example")
    print("=" * 70)
    
    try:
        # Create the graph directly
        graph = create_pdf_processing_graph()
        
        print("✓ LangGraph created successfully")
        print("✓ Graph structure: START → validation → [image_extraction, url_extraction] → aggregation → END")
        
        # Show the graph's structure
        print("\n=== Graph Nodes ===")
        # Note: In a real implementation, you could use graph.get_graph() to inspect structure
        nodes = ["validation", "image_extraction", "url_extraction", "aggregation"]
        for node in nodes:
            print(f"  - {node}")
        
        print("\n=== Graph Flow Pattern ===")
        print("  START")
        print("    ↓")
        print("  validation")
        print("    ├── image_extraction ──┐")
        print("    └── url_extraction ────┼── aggregation ── END")
        
        # Example of manual graph execution
        pdf_path = "sample.pdf"
        if Path(pdf_path).exists():
            print(f"\n=== Manual Graph Execution ===")
            initial_state = {
                "pdf_path": pdf_path,
                "pages_to_process": [0],  # Just first page for demo
                "output_directory": "./demo_manual",
                "processing_results": [],
                "pdf_hash": None,
                "page_count": None,
                "extracted_images": [],
                "extracted_urls": [],
                "errors": [],
                "completed_nodes": []
            }
            
            print("Executing graph with manual state...")
            start_time = time.time()
            final_state = graph.invoke(initial_state)
            execution_time = time.time() - start_time
            
            print(f"✓ Graph execution completed in {execution_time:.2f}s")
            print(f"✓ PDF hash calculated: {final_state.get('pdf_hash') is not None}")
            print(f"✓ Images extracted: {len(final_state.get('extracted_images', []))}")
            print(f"✓ URLs found: {len(final_state.get('extracted_urls', []))}")
        else:
            print(f"\nSkipping manual execution - PDF file not found: {pdf_path}")
            
    except Exception as e:
        print(f"Error: {e}")


def example_export_results():
    """Example showing how to export results to JSON."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Export Results Example")
    print("=" * 70)
    
    pdf_path = "sample.pdf"
    
    try:
        if not Path(pdf_path).exists():
            print(f"Creating a demo state for export example...")
            # Create a mock result for demonstration
            from pdf_processing.agent_schemas import PDFProcessingOutput, PDFHashData, ExtractedImage, ExtractedURL
            
            result = PDFProcessingOutput(
                success=True,
                pdf_path=pdf_path,
                pdf_hash=PDFHashData(sha1="abc123", md5="def456"),
                page_count=5,
                extracted_images=[
                    ExtractedImage(
                        page_number=0,
                        base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                        format="png",
                        phash="d2d3d4d5d6d7d8d9",
                        saved_path="./demo/abc123.png",
                        image_sha1="abc123"
                    )
                ],
                extracted_urls=[
                    ExtractedURL(
                        url="https://example.com",
                        page_number=0,
                        url_type="annotation",
                        coordinates={"x0": 100, "y0": 200, "x1": 300, "y1": 220},
                        is_external=True
                    )
                ],
                errors=[],
                total_processing_time=0.15
            )
        else:
            # Process actual PDF
            result = process_pdf_with_agent(pdf_path, pages_to_process=[0])
        
        # Export to JSON
        output_file = "pdf_processing_results.json"
        
        # Convert Pydantic model to dictionary
        result_dict = result.model_dump()
        
        with open(output_file, 'w') as f:
            json.dump(result_dict, f, indent=2)
        
        print(f"✓ Results exported to: {output_file}")
        print(f"✓ File size: {Path(output_file).stat().st_size} bytes")
        
        # Show a sample of the exported data
        print(f"\n=== Sample of Exported Data ===")
        print(json.dumps({
            "success": result_dict["success"],
            "pdf_path": result_dict["pdf_path"],
            "page_count": result_dict["page_count"],
            "extracted_images_count": len(result_dict["extracted_images"]),
            "extracted_urls_count": len(result_dict["extracted_urls"]),
            "total_processing_time": result_dict["total_processing_time"]
        }, indent=2))
        
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Run all examples."""
    print("PDF Processing LangGraph Agent - Usage Examples")
    print("=" * 70)
    
    # Run examples
    example_basic_usage()
    example_specific_pages()
    example_graph_visualization()
    example_export_results()
    
    print("\n" + "=" * 70)
    print("Usage Summary")
    print("=" * 70)
    print("""
The PDF Processing LangGraph Agent provides parallel processing with:

 1. **Sequential Then Parallel Architecture**:
    - validation: PDF validation, hash calculation, output directory creation
    - image_extraction: Base64 images + perceptual hashing + SHA1 file saving (parallel)
    - url_extraction: URLs from annotations and text (parallel)
    - aggregation: Final validation and cleanup

2. **Key Features**:
   - Automatic parallel execution using LangGraph
   - Comprehensive error handling and logging
   - Flexible page selection (all pages or specific pages)
   - Structured output with detailed timing information
   - Perceptual hashing for image similarity detection
   - SHA1-based image filename generation

3. **Usage Patterns**:
```python
from pdf_processing import process_pdf_with_agent

# Process all pages
result = process_pdf_with_agent("document.pdf")

# Process specific pages
result = process_pdf_with_agent("document.pdf", pages_to_process=[0, 1, 2])

# Custom output directory
result = process_pdf_with_agent("document.pdf", output_directory="./my_images/")

# Access results
print(f"SHA1: {result.pdf_hash.sha1}")
print(f"Images: {len(result.extracted_images)}")
print(f"URLs: {len(result.extracted_urls)}")
```

 4. **Graph Structure**:
    The LangGraph implements validation first, then fan-out/fan-in pattern where
    image and URL extraction nodes execute in parallel after validation, then
    converge to an aggregation node.
""")


if __name__ == "__main__":
    main() 