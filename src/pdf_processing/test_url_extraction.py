#!/usr/bin/env python3
"""
Test script for URL extraction functionality.

This script demonstrates and tests the URL extraction capabilities
of the pdf_processing module.
"""

import logging
import json
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_url_extraction_basic():
    """Test basic URL extraction functionality."""
    print("=" * 60)
    print("Testing URL Extraction Functionality")
    print("=" * 60)
    
    # Import the module
    try:
        from pdf_processing.url_extraction import PDFURLExtractor, URLType
        print("✓ Successfully imported URL extraction module")
    except ImportError as e:
        print(f"✗ Failed to import URL extraction module: {e}")
        return False
    
    # Test URL pattern matching
    extractor = PDFURLExtractor()
    print("✓ Created PDFURLExtractor instance")
    
    # Test URL validation
    test_urls = [
        "https://www.example.com",
        "http://test.org/page",
        "ftp://files.example.com/file.pdf",
        "www.google.com",
        "invalid-url",
        "mailto:test@example.com",
        "",
        "https://very-long-domain-name.example.com/path/to/resource?param=value#anchor"
    ]
    
    print("\nTesting URL validation:")
    for url in test_urls:
        is_valid = extractor._is_valid_url(url)
        status = "✓" if is_valid else "✗"
        print(f"  {status} {url:<50} -> {is_valid}")
    
    # Test URL cleaning
    print("\nTesting URL cleaning:")
    dirty_urls = [
        "www.example.com.",
        "https://test.org,",
        "http://example.com;",
        "www.site.com!",
    ]
    
    for dirty_url in dirty_urls:
        cleaned = extractor._clean_url(dirty_url)
        print(f"  {dirty_url:<30} -> {cleaned}")
    
    return True

def test_url_extraction_with_sample_pdf():
    """Test URL extraction with a sample PDF if available."""
    print("\n" + "=" * 60)
    print("Testing URL Extraction with Sample PDF")
    print("=" * 60)
    
    # Look for sample PDFs in common locations
    sample_paths = [
        Path("tests/sample.pdf"),
        Path("examples/sample.pdf"),
        Path("sample.pdf"),
        Path("../tests/sample.pdf"),
    ]
    
    sample_pdf = None
    for path in sample_paths:
        if path.exists():
            sample_pdf = path
            break
    
    if sample_pdf is None:
        print("ℹ No sample PDF found. Skipping PDF extraction test.")
        print("  To test with a real PDF, place a file at one of these locations:")
        for path in sample_paths:
            print(f"    - {path}")
        return True
    
    try:
        from pdf_processing import extract_urls_from_pdf
        
        print(f"✓ Found sample PDF: {sample_pdf}")
        
        # Extract URLs (default behavior: first page only)
        urls = extract_urls_from_pdf(
            pdf_path=sample_pdf,
            extract_from_annotations=True,
            extract_from_text=True
        )
        
        print(f"✓ Extracted {len(urls)} URLs from first page of PDF")
        
        # Also test extracting from all pages
        urls_all = extract_urls_from_pdf(
            pdf_path=sample_pdf,
            extract_from_annotations=True,
            extract_from_text=True,
            default_to_first_page=False
        )
        
        print(f"✓ Extracted {len(urls_all)} URLs from all pages of PDF")
        
        # Display results from first page
        if urls:
            print("\nExtracted URLs from first page:")
            for i, url_data in enumerate(urls, 1):
                print(f"\n{i}. {url_data['url']}")
                print(f"   Type: {url_data['type']}")
                print(f"   Page: {url_data['page_number']}")
                
                if 'coordinates' in url_data:
                    coords = url_data['coordinates']
                    print(f"   Coordinates: ({coords['x0']:.1f}, {coords['y0']:.1f}, {coords['x1']:.1f}, {coords['y1']:.1f})")
                
                if 'is_external' in url_data:
                    print(f"   External: {url_data['is_external']}")
        else:
            print("ℹ No URLs found on the first page of the PDF")
            
        # Show difference between first page and all pages
        if len(urls_all) > len(urls):
            print(f"\nℹ Found {len(urls_all) - len(urls)} additional URLs on other pages")
        elif len(urls_all) == len(urls):
            print(f"\nℹ All URLs are on the first page")
        else:
            print(f"\nℹ Total URLs: {len(urls_all)}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing with sample PDF: {e}")
        return False

def test_url_extraction_api():
    """Test the URL extraction API comprehensively."""
    print("\n" + "=" * 60)
    print("Testing URL Extraction API")
    print("=" * 60)
    
    try:
        from pdf_processing import (
            PDFURLExtractor,
            URLMatch,
            URLType,
            URLExtractionError
        )
        
        # Test URLType enum
        print("✓ URLType enum:")
        print(f"  - ANNOTATION: {URLType.ANNOTATION.value}")
        print(f"  - TEXT: {URLType.TEXT.value}")
        
        # Test URLMatch dataclass
        print("✓ URLMatch dataclass:")
        url_match = URLMatch(
            url="https://example.com",
            url_type=URLType.TEXT,
            page_number=0
        )
        print(f"  - Created: {url_match}")
        
        # Test to_dict conversion
        url_dict = url_match.to_dict()
        print(f"  - to_dict(): {json.dumps(url_dict, indent=2)}")
        
        # Test URLMatch with coordinates
        annotation_match = URLMatch(
            url="https://example.com/link",
            url_type=URLType.ANNOTATION,
            page_number=1,
            x0=100.0,
            y0=200.0,
            x1=300.0,
            y1=220.0,
            is_external=True,
            link_type="uri"
        )
        
        annotation_dict = annotation_match.to_dict()
        print(f"  - Annotation URL dict: {json.dumps(annotation_dict, indent=2)}")
        
        print("✓ All API tests passed")
        return True
        
    except Exception as e:
        print(f"✗ API test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("PDF URL Extraction Test Suite")
    print("=" * 60)
    
    tests = [
        test_url_extraction_basic,
        test_url_extraction_api,
        test_url_extraction_with_sample_pdf,
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed!")
        return 0
    else:
        print("✗ Some tests failed")
        return 1

if __name__ == "__main__":
    exit(main())