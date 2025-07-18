# PDF Processing LangGraph Agent

A powerful LangGraph-based agent for parallel PDF processing that extracts and analyzes multiple data types simultaneously.

## Overview

This module implements a LangGraph agent that processes PDF documents using parallel nodes for:
- **Hash Calculation**: SHA1 and MD5 file hashes
- **Image Extraction**: Base64 encoding, perceptual hashing, and SHA1-based file saving
- **URL Extraction**: URLs from PDF annotations and text content
- **Result Aggregation**: Comprehensive processing results and error handling

## Architecture

The agent uses a **validation-first then parallel processing** pattern:

```
START → validation → [image_extraction, url_extraction] → aggregation → END
```

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

- ✅ **Efficient Processing**: Validation first, then parallel extraction operations
- ✅ **Automatic Directory Creation**: Output directories created automatically if needed
- ✅ **Comprehensive Error Handling**: Graceful failure handling with detailed error reporting
- ✅ **Flexible Page Selection**: Process all pages or specify exact pages
- ✅ **Perceptual Hashing**: Generate phash for image similarity detection
- ✅ **SHA1-based Image Storage**: Automatic deduplication through hash-based filenames
- ✅ **Structured Output**: Pydantic models for type-safe results
- ✅ **Base64 Image Encoding**: Ready for API transmission or storage

## Quick Start

### Basic Usage

```python
from pdf_processing import process_pdf_with_agent

# Process all pages
result = process_pdf_with_agent("document.pdf")

print(f"Success: {result.success}")
print(f"PDF SHA1: {result.pdf_hash.sha1}")
print(f"Images extracted: {len(result.extracted_images)}")
print(f"URLs found: {len(result.extracted_urls)}")
```

### Process Specific Pages

```python
# Process only first 3 pages
result = process_pdf_with_agent(
    pdf_path="document.pdf",
    pages_to_process=[0, 1, 2],  # 0-based page numbers
    output_directory="./my_images"
)
```

### Access Detailed Results

```python
# Hash information
if result.pdf_hash:
    print(f"SHA1: {result.pdf_hash.sha1}")
    print(f"MD5: {result.pdf_hash.md5}")

# Image details
for img in result.extracted_images:
    print(f"Page {img.page_number}:")
    print(f"  Perceptual Hash: {img.phash}")
    print(f"  Saved to: {img.saved_path}")
    print(f"  Base64 length: {len(img.base64_data)}")

# URL details
for url in result.extracted_urls:
    print(f"URL: {url.url}")
    print(f"  Page: {url.page_number}")
    print(f"  Type: {url.url_type}")
    if url.coordinates:
        print(f"  Position: {url.coordinates}")
```

### Working with the Graph Directly

```python
from pdf_processing import create_pdf_processing_graph

# Create the LangGraph
graph = create_pdf_processing_graph()

# Manual state management
initial_state = {
    "pdf_path": "document.pdf",
    "pages_to_process": [0],
    "output_directory": "./images",
    "processing_results": [],
    "pdf_hash": None,
    "page_count": None,
    "extracted_images": [],
    "extracted_urls": [],
    "errors": [],
    "completed_nodes": []
}

# Execute the graph
final_state = graph.invoke(initial_state)
```

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
# Process a PDF from command line
python -m pdf_processing.pdf_agent document.pdf ./output_images/

# Run examples
python src/pdf_processing/example_agent_usage.py
```

## State Schema

The agent uses a simplified `PDFProcessingState` TypedDict:

```python
class PDFProcessingState(TypedDict):
    # Input parameters
    pdf_path: str
    pages_to_process: Optional[List[int]]
    output_directory: str
    
    # PDF metadata (set by validation node)
    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]
    
    # Extracted data (each updated by a single node)
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    
    # Error tracking (uses operator.add for concurrent updates)
    errors: Annotated[List[str], operator.add]
```

## Output Schema

Results are returned as a `PDFProcessingOutput` Pydantic model:

```python
class PDFProcessingOutput(BaseModel):
    success: bool
    pdf_path: str
    pdf_hash: Optional[PDFHashData]
    page_count: Optional[int]
    extracted_images: List[ExtractedImage]
    extracted_urls: List[ExtractedURL]
    errors: List[str]
    total_processing_time: Optional[float]
```

## Performance

The efficient architecture provides good performance:

- **Validation**: ~0.05s for typical PDF files (includes hash calculation)
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

- **Node-level errors**: Individual nodes can fail without affecting others
- **Graceful degradation**: Partial results are returned even with errors
- **Detailed error reporting**: Specific error messages with node context
- **Processing continuation**: Other nodes continue even if one fails

## Integration with Existing Forensic Analysis

This PDF processing agent is designed to complement the existing forensic analysis tools:

```python
# Use with existing static analysis
from static_analysis.graph import app as forensic_app
from pdf_processing import process_pdf_with_agent

# First, do parallel preprocessing
preprocessing_result = process_pdf_with_agent("suspicious.pdf")

# Then, run forensic analysis with the preprocessed data
forensic_input = {
    "file_path": "suspicious.pdf",
    "pdf_hash": preprocessing_result.pdf_hash.sha1,
    "extracted_urls": [url.url for url in preprocessing_result.extracted_urls],
    "page_count": preprocessing_result.page_count
}

forensic_result = forensic_app.invoke(forensic_input)
```

## Examples

See `example_agent_usage.py` for comprehensive usage examples including:
- Basic processing workflows
- Specific page selection
- Graph visualization and manual execution
- Result export to JSON
- Integration patterns

## Best Practices

1. **Page Selection**: For large PDFs, process specific pages first to validate before full processing
2. **Output Directory**: Use dedicated directories to avoid filename conflicts
3. **Error Handling**: Always check `result.success` and `result.errors` before using results
4. **Memory Management**: For very large PDFs, process in batches rather than all pages at once
5. **Performance**: Use appropriate DPI settings (150 is optimal for most use cases)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed: `pip install imagehash pymupdf pillow`
2. **Permission Errors**: Verify read access to PDF and write access to output directory
3. **Memory Issues**: For large PDFs, process fewer pages at once or reduce DPI
4. **Missing Dependencies**: Run `pip install -e .` from project root to install all dependencies

### Debugging

Enable verbose output for troubleshooting:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

result = process_pdf_with_agent("document.pdf")
``` 