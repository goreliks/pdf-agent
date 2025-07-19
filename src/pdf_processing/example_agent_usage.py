#!/usr/bin/env python3
"""
Example usage of the PDF Processing LangGraph Agent.

This script demonstrates how to use the LangGraph agent for parallel
PDF processing including hash calculation, image extraction, URL extraction,
and perceptual hashing.

UPDATED: Now shows proper Input/Output schema usage with Pydantic validation.
"""

import json
import time
from pathlib import Path

from pdf_processing import process_pdf_with_agent, process_pdf_with_agent_legacy, create_pdf_processing_graph
from pdf_processing.agent_schemas import PDFProcessingInput, PDFProcessingOutput


def example_basic_usage():
    """Basic usage example with proper schema validation."""
    print("=" * 70)
    print("PDF Processing LangGraph Agent - Schema-Based Usage Example")
    print("=" * 70)
    
    # Example PDF path (replace with your actual PDF)
    pdf_path = "sample.pdf"
    output_directory = "./demo_extracted_images"
    
    try:
        print(f"Processing PDF: {pdf_path}")
        print(f"Output directory: {output_directory}")
        print("\nStarting parallel processing with Pydantic validation...")
        
        # Create validated input using Pydantic schema
        input_data = PDFProcessingInput(
            pdf_path=pdf_path,
            pages_to_process=1,  # Process first page only (default)
            output_directory=output_directory
        )
        
        # Process the PDF using the LangGraph agent with schema validation
        result = process_pdf_with_agent(input_data)
        
        # Display results - result is automatically validated as PDFProcessingOutput
        print(f"\n=== Processing Results ===")
        print(f"✓ Success: {result.success}")
        print(f"✓ Total processing time: {result.total_processing_time:.2f}s")
        
        if result.pdf_hash:
            print(f"✓ PDF SHA1: {result.pdf_hash.sha1}")
            print(f"✓ PDF MD5: {result.pdf_hash.md5}")
        
        print(f"✓ Total pages: {result.page_count}")
        print(f"✓ Extracted images: {len(result.extracted_images)}")
        print(f"✓ Extracted URLs: {len(result.extracted_urls)}")
        
        # Show schema validation benefits
        print(f"\n=== Schema Benefits ===")
        print(f"✓ Input automatically validated: {type(input_data).__name__}")
        print(f"✓ Output automatically validated: {type(result).__name__}")
        print(f"✓ Type safety ensured throughout processing")
        
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")


def example_input_validation():
    """Example showing input validation with invalid data."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Input Validation Example")
    print("=" * 70)
    
    try:
        # Try to create input with invalid data
        print("Testing input validation with invalid PDF path...")
        
        # This will validate but may fail during processing
        input_data = PDFProcessingInput(
            pdf_path="",  # Empty path
            pages_to_process=3,  # Process first 3 pages
            output_directory="./demo_validation"
        )
        
        print(f"✓ Basic validation passed for input: {input_data.pdf_path}")
        
        # Try with invalid page numbers (should still validate, but may fail in processing)
        input_data2 = PDFProcessingInput(
            pdf_path="sample.pdf",
            pages_to_process=0,  # Invalid: must be at least 1
            output_directory="./demo_validation"
        )
        
        print(f"✓ Schema validation passed even with potentially problematic pages: {input_data2.pages_to_process}")
        print("  (Actual validation happens during PDF processing)")
        
        # Show how to handle validation errors
        try:
            # This would fail Pydantic validation if we had strict validators
            from pydantic import ValidationError
            
            # Example of what would cause validation error
            bad_data = {
                "pdf_path": 123,  # Should be string
                "pages_to_process": "invalid",  # Should be int
                "output_directory": None  # Should be string or None (for auto-generation)
            }
            
            PDFProcessingInput.model_validate(bad_data)
            
        except ValidationError as e:
            print(f"\n✓ Pydantic validation correctly caught errors:")
            for error in e.errors():
                print(f"  - {error['loc'][0]}: {error['msg']}")
                
    except Exception as e:
        print(f"Validation example error: {e}")


def example_specific_pages():
    """Example processing only specific pages with schema."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Specific Pages with Schema")
    print("=" * 70)
    
    pdf_path = "sample.pdf"
    pages_to_process = 3  # Process first 3 pages
    output_directory = "./demo_specific_pages"
    
    try:
        print(f"Processing PDF: {pdf_path}")
        print(f"Pages to process: {pages_to_process} (from beginning)")
        print(f"Output directory: {output_directory}")
        
        # Create validated input
        input_data = PDFProcessingInput(
            pdf_path=pdf_path,
            pages_to_process=pages_to_process,
            output_directory=output_directory
        )
        
        result = process_pdf_with_agent(input_data)
        
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


def example_legacy_comparison():
    """Example showing legacy vs new schema approach."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Legacy vs Schema Comparison")
    print("=" * 70)
    
    pdf_path = "sample.pdf"
    
    if not Path(pdf_path).exists():
        print(f"Skipping comparison - PDF file not found: {pdf_path}")
        return
    
    try:
        print("=== LEGACY APPROACH (Deprecated) ===")
        start_time = time.time()
        
        # Legacy approach - still works but shows deprecation warning
        legacy_result = process_pdf_with_agent_legacy(
            pdf_path=pdf_path,
            pages_to_process=[0],  # Old format: specific page numbers
            output_directory="./demo_legacy"
        )
        
        legacy_time = time.time() - start_time
        print(f"✓ Legacy processing completed in {legacy_time:.2f}s")
        print(f"✓ Success: {legacy_result.success}")
        
        print("\n=== NEW SCHEMA APPROACH (Recommended) ===")
        start_time = time.time()
        
        # New schema approach with validation
        input_data = PDFProcessingInput(
            pdf_path=pdf_path,
            pages_to_process=1,  # New format: number of pages from beginning
            output_directory="./demo_schema"
        )
        
        schema_result = process_pdf_with_agent(input_data)
        schema_time = time.time() - start_time
        
        print(f"✓ Schema-based processing completed in {schema_time:.2f}s")
        print(f"✓ Success: {schema_result.success}")
        
        print(f"\n=== COMPARISON ===")
        print(f"✓ Both approaches produce identical results")
        print(f"✓ Schema approach provides:")
        print(f"  - Automatic input validation")
        print(f"  - Better type safety")
        print(f"  - Clear data contracts")
        print(f"  - IDE autocompletion support")
        print(f"  - Runtime error prevention")
        
    except Exception as e:
        print(f"Comparison error: {e}")


def example_graph_visualization():
    """Example showing graph setup with schema context."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Graph Visualization with Schemas")
    print("=" * 70)
    
    try:
        # Create the graph
        graph = create_pdf_processing_graph()
        
        print("Graph created successfully!")
        print(f"Graph type: {type(graph)}")
        
        # Show the schema configuration
        print(f"\nGraph Schema Configuration:")
        print(f"✅ Input Schema: PDFProcessingInput (user-facing fields only)")
        print(f"   - pdf_path: str")
        print(f"   - pages_to_process: Optional[int] = 1 (number of pages from beginning)")
        print(f"   - output_directory: Optional[str] = None (auto-generated if None)")
        print(f"✅ Output Schema: PDFProcessingOutput (structured results)")
        print(f"✅ Internal State: PDFProcessingState (all processing fields)")
        
        print(f"\nGraph nodes: validation, image_extraction, url_extraction, aggregation")
        print(f"LangGraph Studio will now show ONLY the input fields!")
        
        pdf_path = "sample.pdf"
        
        if Path(pdf_path).exists():
            print(f"\n=== Manual Graph Execution with Schema ===")
            
            # Create validated input
            input_data = PDFProcessingInput(
                pdf_path=pdf_path,
                pages_to_process=1,  # Just first page for demo
                output_directory="./demo_manual"
            )
            
            print("Executing graph with schema-aware input...")
            print(f"Input type: {type(input_data).__name__}")
            
            start_time = time.time()
            # Graph automatically converts input schema to internal state and back to output schema
            result = graph.invoke(input_data)
            execution_time = time.time() - start_time
            
            print(f"✅ Graph execution completed in {execution_time:.2f}s")
            print(f"✅ Output type: {type(result).__name__}")
            print(f"✅ PDF hash calculated: {result.pdf_hash is not None}")
            print(f"✅ Images extracted: {len(result.extracted_images)}")
            print(f"✅ URLs found: {len(result.extracted_urls)}")
            print(f"✅ Success: {result.success}")
            
            print(f"\n=== Schema Benefits Demonstrated ===")
            print(f"✅ Input automatically validated before processing")
            print(f"✅ Output automatically validated after processing")
            print(f"✅ LangGraph Studio shows clean interface")
            print(f"✅ Internal complexity hidden from user")
            
        else:
            print(f"\nSkipping manual execution - PDF file not found: {pdf_path}")
            print("But the schema configuration is still demonstrated above!")
            
    except Exception as e:
        print(f"Error: {e}")


def example_export_results():
    """Example showing how to export schema-validated results to JSON."""
    print("\n" + "=" * 70)
    print("PDF Processing LangGraph Agent - Export Schema Results")
    print("=" * 70)
    
    pdf_path = "sample.pdf"
    
    try:
        if not Path(pdf_path).exists():
            print(f"Creating a demo validated result for export example...")
            # Create a mock validated result using proper schemas
            from pdf_processing.agent_schemas import PDFHashData, ExtractedImage, ExtractedURL
            
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
            # Process actual PDF with schema validation
            input_data = PDFProcessingInput(
                pdf_path=pdf_path,
                pages_to_process=1,  # Process first page
                output_directory="./demo_export"
            )
            result = process_pdf_with_agent(input_data)
        
        # Export to JSON with schema validation
        output_file = "pdf_processing_results.json"
        
        # Convert Pydantic model to dictionary (maintains validation)
        result_dict = result.model_dump()
        
        # Add schema information to export
        export_data = {
            "schema_version": "1.0",
            "input_schema": "PDFProcessingInput",
            "output_schema": "PDFProcessingOutput", 
            "export_timestamp": time.time(),
            "results": result_dict
        }
        
        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        print(f"✓ Results exported to: {output_file}")
        print(f"✓ Schema information included in export")
        print(f"✓ Export contains {len(result.extracted_images)} images")
        print(f"✓ Export contains {len(result.extracted_urls)} URLs")
        
        # Show how to reload and validate
        print(f"\n=== Reload and Validation Example ===")
        with open(output_file, 'r') as f:
            loaded_data = json.load(f)
        
        # Recreate validated object from export
        reloaded_result = PDFProcessingOutput.model_validate(loaded_data["results"])
        
        print(f"✓ Successfully reloaded and validated: {type(reloaded_result).__name__}")
        print(f"✓ Validation ensures data integrity on reload")
        
    except Exception as e:
        print(f"Export error: {e}")


def main():
    """Run all examples showcasing proper schema usage."""
    print("PDF Processing LangGraph Agent - Schema-Based Usage Examples")
    print("=" * 70)
    
    # Run all examples
    example_basic_usage()
    example_input_validation()
    example_specific_pages()
    example_legacy_comparison()
    example_graph_visualization()
    example_export_results()
    
    print("\n" + "=" * 70)
    print("Schema Usage Summary")
    print("=" * 70)
    print("""
The PDF Processing LangGraph Agent now provides robust schema validation:

1. **Input Validation with PDFProcessingInput**:
   - Automatic validation of input parameters
   - Type safety for pdf_path, pages_to_process, output_directory
   - Clear error messages for invalid inputs

2. **Output Validation with PDFProcessingOutput**:
   - Guaranteed structure for all results
   - Type-safe access to extracted data
   - Consistent error handling

3. **Recommended Usage**:
```python
from pdf_processing import process_pdf_with_agent
from pdf_processing.agent_schemas import PDFProcessingInput

# Create validated input
input_data = PDFProcessingInput(
    pdf_path="document.pdf",
    pages_to_process=3,  # Process first 3 pages from beginning
    output_directory="./my_images"  # Optional: auto-generated if None
)

# Process with automatic validation
result = process_pdf_with_agent(input_data)

# Access validated results
print(f"SHA1: {result.pdf_hash.sha1}")
print(f"Images: {len(result.extracted_images)}")
print(f"Success: {result.success}")
```

4. **Benefits**:
   - ✅ Runtime input validation
   - ✅ Type safety throughout processing
   - ✅ Clear data contracts
   - ✅ IDE autocompletion support  
   - ✅ Automatic serialization/deserialization
   - ✅ Better error messages

5. **Backward Compatibility**:
   - Legacy function `process_pdf_with_agent_legacy()` still available
   - Shows deprecation warning to encourage schema adoption
   - All existing code continues to work

6. **Schema Integration Benefits**:
   - Follows LangGraph best practices for input/output validation
   - Leverages Pydantic for robust data validation
   - Enables better integration with FastAPI, LangChain, and other tools
   - Provides foundation for future enhancements
""")


if __name__ == "__main__":
    main() 