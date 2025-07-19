# PDF Processing LangGraph Agent

A powerful LangGraph-based agent for parallel PDF processing that extracts and analyzes multiple data types simultaneously.

**🔥 NEW: Enhanced with robust Pydantic schema validation for Input/Output type safety!**

## Overview

This module implements a LangGraph agent that processes PDF documents using parallel nodes for:
- **Hash Calculation**: SHA1 and MD5 file hashes
- **Image Extraction**: Base64 encoding, perceptual hashing, and SHA1-based file saving
- **URL Extraction**: URLs from PDF annotations and text content
- **Result Aggregation**: Comprehensive processing results and error handling

**NEW: All inputs and outputs are now validated using Pydantic schemas, ensuring type safety and catching errors early.**

## Architecture

The agent uses a **validation-first then parallel processing** pattern:

```
START → validation → [image_extraction, url_extraction] → aggregation → END
```

### Schema-Based Input/Output

- **`PDFProcessingInput`**: Validates all input parameters with field validators *(User-facing in LangGraph Studio)*
- **`PDFProcessingOutput`**: Guarantees consistent, type-safe output structure *(Final results)*
- **`PDFProcessingState`**: Internal TypedDict for LangGraph state management *(Hidden from user)*

**🎯 LangGraph Studio Integration**: The graph is configured with explicit `input_schema` and `output_schema` parameters, so **LangGraph Studio will only show the 3 user-facing input fields** (`pdf_path`, `pages_to_process`, `output_directory`) instead of all internal state fields.

### Node Functions

1. **validation**: 
   - Validates PDF file accessibility
   - Creates output directory if needed
   - Computes SHA1 and MD5 hashes of the PDF file
   - Determines total page count

2. **image_extraction**:
   - Extracts pages as base64-encoded images
   - Calculates perceptual hash (phash) for each image
   - Saves images with SHA1 hash as filename
   - Supports specific page selection

3. **url_extraction**:
   - Extracts URLs from PDF annotations (with coordinates)
   - Extracts URLs from text content
   - Supports both specific pages and all pages

4. **aggregation**:
   - Validates that all required data was collected
   - Performs final error checking and validation

## Features

- ✅ **Robust Schema Validation**: Pydantic-based input/output validation
- ✅ **Type Safety**: Full type checking throughout the processing pipeline  
- ✅ **Efficient Processing**: Validation first, then parallel extraction operations
- ✅ **Automatic Directory Creation**: Output directories created automatically if needed
- ✅ **Comprehensive Error Handling**: Graceful failure handling with detailed error reporting
- ✅ **Flexible Page Selection**: Process all pages or specify exact pages
- ✅ **Perceptual Hashing**: Generate phash for image similarity detection
- ✅ **SHA1-based Image Storage**: Automatic deduplication through hash-based filenames
- ✅ **Structured Output**: Pydantic models for type-safe results
- ✅ **Base64 Image Encoding**: Ready for API transmission or storage
- ✅ **Backward Compatibility**: Legacy function available for existing code

## Quick Start

### Basic Usage (Recommended - Schema-Based)

```python
from pdf_processing import process_pdf_with_agent
from pdf_processing.agent_schemas import PDFProcessingInput

# Create validated input
input_data = PDFProcessingInput(
    pdf_path="document.pdf",
    pages_to_process=1,  # Process first page only (default)
    output_directory="./extracted_images"  # Optional: auto-generated if None
)

# Process with automatic validation
result = process_pdf_with_agent(input_data)

print(f"Success: {result.success}")
print(f"PDF SHA1: {result.pdf_hash.sha1}")
print(f"Images extracted: {len(result.extracted_images)}")
print(f"URLs found: {len(result.extracted_urls)}")
```

### Input Validation Benefits

```python
from pydantic import ValidationError
from pdf_processing.agent_schemas import PDFProcessingInput

try:
    # This will automatically validate inputs
    input_data = PDFProcessingInput(
        pdf_path="document.txt",  # ❌ ValidationError: must be .pdf
        pages_to_process=0,       # ❌ ValidationError: must be at least 1
        output_directory=""       # ❌ ValidationError: cannot be empty (use None for auto-generation)
    )
except ValidationError as e:
    print("Validation caught errors early:")
    for error in e.errors():
        print(f"- {error['loc'][0]}: {error['msg']}")
```

### Process Specific Pages

```python
# Process first 3 pages with validation
input_data = PDFProcessingInput(
    pdf_path="document.pdf",
    pages_to_process=3,  # Process first 3 pages from beginning
    output_directory="./my_images"
)

result = process_pdf_with_agent(input_data)
```

### Access Detailed Results

```python
# Hash information (validated)
if result.pdf_hash:
    print(f"SHA1: {result.pdf_hash.sha1}")  # Guaranteed 40-char lowercase
    print(f"MD5: {result.pdf_hash.md5}")    # Guaranteed 32-char lowercase

# Image details (type-safe)
for img in result.extracted_images:
    print(f"Page {img.page_number}:")        # Guaranteed non-negative
    print(f"  Format: {img.format}")         # Validated format (PNG, JPG, etc.)
    print(f"  Perceptual Hash: {img.phash}")
    print(f"  Saved to: {img.saved_path}")   # Validated path with extension
    print(f"  Base64 length: {len(img.base64_data)}")  # Non-empty

# URL details (validated)
for url in result.extracted_urls:
    print(f"URL: {url.url}")                 # Validated URL format
    print(f"  Page: {url.page_number}")      # Non-negative
    print(f"  Type: {url.url_type}")         # Validated type (annotation, text, etc.)
    if url.coordinates:
        print(f"  Position: {url.coordinates}")
```

### Legacy Usage (Backward Compatibility)

```python
from pdf_processing import process_pdf_with_agent_legacy

# Legacy approach - still works but shows deprecation warning
result = process_pdf_with_agent_legacy(
    pdf_path="document.pdf",
    pages_to_process=[0],
    output_directory="./images"
)
```

### Working with the Graph Directly

```python
from pdf_processing import create_pdf_processing_graph
from pdf_processing.agent_schemas import PDFProcessingInput, PDFProcessingOutput

# Create the LangGraph
graph = create_pdf_processing_graph()

# Create validated input
input_data = PDFProcessingInput(
    pdf_path="document.pdf",
    pages_to_process=[0],
    output_directory="./images"
)

# Manual state management with validated input
initial_state = {
    "pdf_path": input_data.pdf_path,
    "pages_to_process": input_data.pages_to_process,
    "output_directory": input_data.output_directory,
    "pdf_hash": None,
    "page_count": None,
    "extracted_images": [],
    "extracted_urls": [],
    "errors": []
}

# Execute the graph
final_state = graph.invoke(initial_state)

# Create validated output
result = PDFProcessingOutput(
    success=len(final_state.get("errors", [])) == 0,
    pdf_path=input_data.pdf_path,
    pdf_hash=final_state.get("pdf_hash"),
    page_count=final_state.get("page_count"),
    extracted_images=final_state.get("extracted_images", []),
    extracted_urls=final_state.get("extracted_urls", []),
    errors=final_state.get("errors", []),
    total_processing_time=0.0
)
```

## Schema Validation Details

### Input Validation (`PDFProcessingInput`)

```python
class PDFProcessingInput(BaseModel):
    pdf_path: str                        # Must be non-empty with .pdf extension
    pages_to_process: Optional[int] = 1  # Number of pages from beginning (default: 1)
    output_directory: Optional[str]      # Auto-generated if None
    
    # Automatic validations:
    # ✅ PDF extension checking
    # ✅ Page count validation (must be >= 1)
    # ✅ Directory path normalization or auto-generation
    # ✅ Empty value prevention
```

### Output Validation (`PDFProcessingOutput`)

```python
class PDFProcessingOutput(BaseModel):
    success: bool                        # Processing success status
    pdf_path: str                        # Non-empty PDF path
    pdf_hash: Optional[PDFHashData]      # Validated hash data
    page_count: Optional[int]            # Non-negative page count
    extracted_images: List[ExtractedImage]  # Validated image data
    extracted_urls: List[ExtractedURL]   # Validated URL data
    errors: List[str]                    # Error messages
    total_processing_time: Optional[float]  # Non-negative processing time
    
    # Automatic validations:
    # ✅ Success/error consistency checking
    # ✅ Page number bounds validation
    # ✅ Hash format validation (SHA1: 40 chars, MD5: 32 chars)
    # ✅ Image format validation (PNG, JPG, etc.)
    # ✅ URL format validation
    # ✅ Cross-field consistency checks
```

### Field-Level Validators

- **Hash Validation**: SHA1 (40 chars), MD5 (32 chars), alphanumeric only
- **Image Format**: PNG, JPG, JPEG, GIF, BMP, TIFF (case-insensitive)
- **URL Validation**: Basic format checking for common URL types
- **Page Count**: Must be at least 1 (represents number of pages from beginning)
- **File Paths**: Extension validation, path normalization, auto-generation
- **PDF Extension**: Must have .pdf extension (case-insensitive)

## Installation

The module requires the following dependencies:

```bash
pip install imagehash>=4.3.1  # For perceptual hashing
pip install pymupdf>=1.23.0   # For PDF processing
pip install pillow>=10.0.0    # For image handling
pip install langgraph          # For graph orchestration
pip install pydantic>=2.0     # For data validation
```

Or install from the project root:

```bash
pip install -e .
```

## Command Line Usage

```bash
# Process a PDF from command line (uses legacy wrapper)
python -m pdf_processing.pdf_agent document.pdf ./output_images/

# Run schema-based examples
python src/pdf_processing/example_agent_usage.py
```

## Schema Integration Benefits

### 1. **Early Error Detection**
```python
# Errors caught at input validation, not during processing
try:
    input_data = PDFProcessingInput(pdf_path="invalid.txt")
except ValidationError:
    print("Invalid file extension caught immediately!")
```

### 2. **Type Safety**
```python
# IDE autocomplete and type checking
result = process_pdf_with_agent(input_data)
hash_value: str = result.pdf_hash.sha1  # Type-safe access
image_count: int = len(result.extracted_images)  # Guaranteed list
```

### 3. **Consistent Data Contracts**
```python
# Output format guaranteed across all processing scenarios
def analyze_results(result: PDFProcessingOutput):
    # Always safe to access these fields
    assert isinstance(result.success, bool)
    assert isinstance(result.extracted_images, list)
    assert all(isinstance(img.page_number, int) for img in result.extracted_images)
```

### 4. **JSON Serialization**
```python
# Automatic JSON serialization with validation
result_dict = result.model_dump()
json_str = result.model_dump_json()

# Reload with validation
reloaded = PDFProcessingOutput.model_validate(result_dict)
```

## Performance

The efficient architecture provides good performance:

- **Validation**: ~0.01s for input validation (Pydantic overhead)
- **PDF Processing**: ~0.05s for typical PDF files (includes hash calculation)
- **Image extraction**: ~0.1-0.5s per page (depends on complexity and DPI)
- **URL extraction**: ~0.02-0.1s for typical documents  
- **Overall**: Faster than sequential processing due to parallel image/URL extraction

Processing times scale with:
- PDF file size
- Number of pages processed
- Image complexity and DPI settings
- Number of URLs in the document

## Error Handling

The agent provides comprehensive error handling:

- **Input Validation**: Early error detection with clear messages
- **Node-level errors**: Individual nodes can fail without affecting others
- **Graceful degradation**: Partial results are returned even with errors
- **Detailed error reporting**: Specific error messages with node context
- **Processing continuation**: Other nodes continue even if one fails
- **Output Validation**: Ensures consistent output structure even with errors

## Integration with Existing Forensic Analysis

This PDF processing agent is designed to complement the existing forensic analysis tools:

```python
# Use with existing static analysis
from static_analysis.graph import app as forensic_app
from pdf_processing import process_pdf_with_agent
from pdf_processing.agent_schemas import PDFProcessingInput

# First, do parallel preprocessing with validation
input_data = PDFProcessingInput(
    pdf_path="suspicious.pdf",
    output_directory="./forensic_images"
)
preprocessing_result = process_pdf_with_agent(input_data)

# Then, run forensic analysis with the validated, preprocessed data
forensic_input = {
    "file_path": preprocessing_result.pdf_path,
    "pdf_hash": preprocessing_result.pdf_hash.sha1,
    "extracted_urls": [url.url for url in preprocessing_result.extracted_urls],
    "page_count": preprocessing_result.page_count
}

forensic_result = forensic_app.invoke(forensic_input)
```

## Migration Guide

### From Legacy to Schema-Based

**Before (Legacy):**
```python
result = process_pdf_with_agent("doc.pdf", [0, 1], "./images")
```

**After (Schema-Based):**
```python
input_data = PDFProcessingInput(
    pdf_path="doc.pdf",
    pages_to_process=2,  # Process first 2 pages from beginning
    output_directory="./images"  # Optional: auto-generated if None
)
result = process_pdf_with_agent(input_data)
```

**Benefits of Migration:**
- ✅ Input validation prevents runtime errors
- ✅ Better IDE support with autocomplete
- ✅ Type safety throughout your code
- ✅ Consistent error handling
- ✅ Intuitive page specification (count vs specific numbers)
- ✅ Auto-generated output directories
- ✅ Future-proof as new features are added

## Examples

See `example_agent_usage.py` for comprehensive usage examples including:
- Schema-based processing workflows
- Input validation demonstrations
- Legacy vs new approach comparisons
- Graph visualization and manual execution
- Result export with schema validation
- Error handling patterns

## Best Practices

1. **Use Schema Validation**: Always use `PDFProcessingInput` for input validation
2. **Handle Validation Errors**: Wrap input creation in try/catch for `ValidationError`
3. **Type Hints**: Use type hints with the schema classes for better IDE support
4. **Page Selection**: For large PDFs, process specific pages first to validate before full processing
5. **Output Directory**: Use dedicated directories to avoid filename conflicts
6. **Error Handling**: Always check `result.success` and `result.errors` before using results
7. **Memory Management**: For very large PDFs, process in batches rather than all pages at once
8. **Performance**: Use appropriate DPI settings (150 is optimal for most use cases)

## Troubleshooting

### Common Validation Errors

**Invalid PDF Extension:**
```python
# ❌ Error: File must have .pdf extension
PDFProcessingInput(pdf_path="document.txt")

# ✅ Solution:
PDFProcessingInput(pdf_path="document.pdf")
```

**Invalid Page Numbers:**
```python
# ❌ Error: Number of pages to process must be at least 1
PDFProcessingInput(pdf_path="doc.pdf", pages_to_process=0)

# ✅ Solution:
PDFProcessingInput(pdf_path="doc.pdf", pages_to_process=1)
```

**Empty Output Directory:**
```python
# ❌ Error: Output directory cannot be empty (use None for auto-generation)
PDFProcessingInput(pdf_path="doc.pdf", output_directory="")

# ✅ Solution:
PDFProcessingInput(pdf_path="doc.pdf", output_directory="./images")
# OR: Let it auto-generate
PDFProcessingInput(pdf_path="doc.pdf", output_directory=None)
```

### Schema Validation Issues

- Check that all required fields are provided
- Ensure field types match the schema definitions  
- Verify page numbers are within document bounds
- Confirm PDF files have valid extensions
- Check that output directories are accessible

### Common Processing Issues

1. **PDF Not Found**: Ensure the PDF file exists and is readable
2. **Permission Errors**: Check write permissions for output directory
3. **Memory Issues**: Process fewer pages at once for large PDFs
4. **Invalid PDF**: Some PDFs may be corrupted or use unsupported features

For additional help, run the examples in `example_agent_usage.py` which demonstrate proper usage patterns and error handling. 