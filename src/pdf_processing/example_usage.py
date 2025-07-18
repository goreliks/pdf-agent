#!/usr/bin/env python3
"""
Example usage of the PDF URL extraction functionality.

This script demonstrates how to use the pdf_processing module
to extract URLs from PDF documents.
"""

import json
from pathlib import Path

def example_basic_usage():
    """Basic usage example."""
    print("=" * 60)
    print("Basic URL Extraction Example")
    print("=" * 60)
    
    # Import the URL extraction function
    from pdf_processing.url_extraction import extract_urls_from_pdf
    
    # Example PDF path (replace with your actual PDF)
    pdf_path = "sample.pdf"
    
    try:
        # Extract URLs from both annotations and text (default: first page only)
        urls = extract_urls_from_pdf(
            pdf_path=pdf_path,
            extract_from_annotations=True,
            extract_from_text=True
        )
        
        print(f"Found {len(urls)} URLs on the first page of the PDF:")
        
        for i, url_data in enumerate(urls, 1):
            print(f"\n{i}. {url_data['url']}")
            print(f"   Type: {url_data['type']}")
            print(f"   Page: {url_data['page_number']}")
            
            # Show coordinates if available (annotation-based URLs)
            if 'coordinates' in url_data:
                coords = url_data['coordinates']
                print(f"   Coordinates: ({coords['x0']:.1f}, {coords['y0']:.1f}, {coords['x1']:.1f}, {coords['y1']:.1f})")
            
            # Show additional metadata
            if 'is_external' in url_data:
                print(f"   External: {url_data['is_external']}")
            if 'link_type' in url_data:
                print(f"   Link type: {url_data['link_type']}")
    
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
        print("Please provide a valid PDF file path.")
    except Exception as e:
        print(f"Error extracting URLs: {e}")

def example_advanced_usage():
    """Advanced usage with custom configuration."""
    print("\n" + "=" * 60)
    print("Advanced URL Extraction Example")
    print("=" * 60)
    
    from pdf_processing.url_extraction import PDFURLExtractor, URLType
    
    # Create extractor with custom settings
    extractor = PDFURLExtractor(
        min_url_length=8,    # Minimum URL length
        max_url_length=1000  # Maximum URL length
    )
    
    pdf_path = "sample.pdf"
    
    try:
        # Extract URLs with specific configuration - process first 3 pages
        urls = extractor.extract_urls_from_pdf(
            pdf_path=pdf_path,
            extract_from_annotations=True,
            extract_from_text=True,
            specific_pages=[0, 1, 2]  # Process first 3 pages (0-based indexing)
        )
        
        print(f"Processing specific pages: {len(urls)} URLs found")
        
        # Alternative: Extract from all pages
        urls_all = extractor.extract_urls_from_pdf(
            pdf_path=pdf_path,
            extract_from_annotations=True,
            extract_from_text=True,
            default_to_first_page=False  # Process all pages
        )
        
        # Separate URLs by type
        annotation_urls = [url for url in urls if url.url_type == URLType.ANNOTATION]
        text_urls = [url for url in urls if url.url_type == URLType.TEXT]
        
        print(f"Annotation URLs from specific pages: {len(annotation_urls)}")
        print(f"Text URLs from specific pages: {len(text_urls)}")
        print(f"Total URLs from all pages: {len(urls_all)}")
        
        # Export to JSON
        json_data = [url.to_dict() for url in urls_all]
        
        output_file = "extracted_urls.json"
        with open(output_file, 'w') as f:
            json.dump(json_data, f, indent=2)
        
        print(f"URLs exported to: {output_file}")
        
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

def example_text_only():
    """Extract URLs only from text content."""
    print("\n" + "=" * 60)
    print("Text-Only URL Extraction Example")
    print("=" * 60)
    
    from pdf_processing.url_extraction import extract_urls_from_pdf
    
    pdf_path = "sample.pdf"
    
    try:
        # Extract only from text (no coordinates) - default: first page only
        urls = extract_urls_from_pdf(
            pdf_path=pdf_path,
            extract_from_annotations=False,  # Skip annotations
            extract_from_text=True           # Only from text
        )
        
        print(f"Found {len(urls)} URLs in text content on first page:")
        
        for url_data in urls:
            print(f"  - {url_data['url']} (page {url_data['page_number']})")
            
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

def example_annotations_only():
    """Extract URLs only from annotations with coordinates."""
    print("\n" + "=" * 60)
    print("Annotations-Only URL Extraction Example")
    print("=" * 60)
    
    from pdf_processing.url_extraction import extract_urls_from_pdf
    
    pdf_path = "sample.pdf"
    
    try:
        # Extract only from annotations (with coordinates) - default: first page only
        urls = extract_urls_from_pdf(
            pdf_path=pdf_path,
            extract_from_annotations=True,   # Only from annotations
            extract_from_text=False          # Skip text
        )
        
        print(f"Found {len(urls)} clickable URLs with coordinates on first page:")
        
        for url_data in urls:
            print(f"  - {url_data['url']}")
            if 'coordinates' in url_data:
                coords = url_data['coordinates']
                print(f"    Location: ({coords['x0']:.1f}, {coords['y0']:.1f}) to ({coords['x1']:.1f}, {coords['y1']:.1f})")
            
    except FileNotFoundError:
        print(f"PDF file not found: {pdf_path}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Run all examples."""
    print("PDF URL Extraction - Usage Examples")
    print("=" * 60)
    
    # Run examples
    example_basic_usage()
    example_advanced_usage()
    example_text_only()
    example_annotations_only()
    
    print("\n" + "=" * 60)
    print("Usage Summary")
    print("=" * 60)
    print("""
The pdf_processing module provides comprehensive URL extraction with:

1. **Two extraction methods**:
   - Annotation-based URLs (with precise coordinates)
   - Text-based URLs (found in document text)

2. **Flexible page processing**:
   - Default: Process first page only (page 0)
   - Option to process specific pages
   - Option to process all pages
   - Custom URL validation rules

3. **Rich metadata**:
   - URL coordinates for clickable links
   - Page numbers
   - Link types and external status
   - Structured output format

4. **High performance**:
   - Uses PyMuPDF for efficient processing
   - Robust error handling
   - Deduplication of URLs

Example usage:
```python
from pdf_processing import extract_urls_from_pdf

# Default: Extract URLs from first page only
urls = extract_urls_from_pdf("document.pdf")
print(f"Found {len(urls)} URLs on first page")

# Extract from all pages
urls_all = extract_urls_from_pdf("document.pdf", default_to_first_page=False)
print(f"Found {len(urls_all)} URLs in entire document")

# Extract from specific pages
urls_specific = extract_urls_from_pdf("document.pdf", specific_pages=[0, 2, 4])
print(f"Found {len(urls_specific)} URLs on pages 1, 3, and 5")
```
""")

if __name__ == "__main__":
    main()