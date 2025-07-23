"""
Example usage of the Visual Analysis LangGraph Agent

This module demonstrates how to use the visual analysis agent for:
1. Analyzing PDF files directly (full pipeline)
2. Analyzing extracted images and URLs (direct input)
3. Integration patterns with other agents

The Visual Deception Analyst (VDA) performs cross-modal analysis combining
visual evidence with technical data to identify deception tactics.
"""

import json
from pathlib import Path

from visual_analysis.schemas import VisualAnalysisInput, VisualAnalysisOutput
from visual_analysis.graph import process_pdf_with_visual_agent

# Import for direct usage examples
from pdf_processing.agent_schemas import ExtractedImage, ExtractedURL


def example_1_analyze_pdf_file():
    """
    Example 1: Analyze a PDF file directly
    
    This is the most common usage pattern - provide a PDF path and let
    the agent extract images and URLs, then perform visual analysis.
    """
    print("=" * 60)
    print("EXAMPLE 1: Analyzing PDF File Directly")
    print("=" * 60)
    
    # Define input - replace with your actual PDF path
    pdf_path = "tests/sample_document.pdf"  # Update this path
    
    if not Path(pdf_path).exists():
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   Please update the path to point to an actual PDF file.")
        return
    
    # Create input for visual analysis
    input_data = VisualAnalysisInput(
        pdf_path=pdf_path,
        pages_to_process=2,  # Analyze first 2 pages
        output_directory="./visual_analysis_output"
    )
    
    print(f"📄 Analyzing PDF: {pdf_path}")
    print(f"📊 Processing {input_data.pages_to_process} pages...")
    
    try:
        # Process the PDF with visual analysis
        result = process_pdf_with_visual_agent(input_data)
        
        # Display results
        print(f"\n✅ Analysis completed successfully: {result.success}")
        print(f"🎯 Overall Verdict: {result.overall_verdict}")
        print(f"📈 Confidence Score: {result.overall_confidence:.2f}")
        print(f"📑 Pages Analyzed: {result.total_pages_analyzed}")
        print(f"⚠️  Deception Tactics Found: {len(result.all_deception_tactics)}")
        print(f"✨ Benign Signals Found: {len(result.all_benign_signals)}")
        print(f"🚨 High Priority URLs: {len(result.high_priority_urls)}")
        print(f"⏱️  Processing Time: {result.total_processing_time:.2f}s")
        
        print(f"\n📋 Executive Summary:")
        print(f"   {result.executive_summary}")
        
        # Show deception tactics if found
        if result.all_deception_tactics:
            print(f"\n🚨 Deception Tactics Detected:")
            for i, tactic in enumerate(result.all_deception_tactics[:3], 1):  # Show top 3
                print(f"   {i}. {tactic.tactic_type} (confidence: {tactic.confidence:.2f})")
                print(f"      {tactic.description}")
        
        # Show high priority URLs if found
        if result.high_priority_urls:
            print(f"\n🔗 High Priority URLs for Investigation:")
            for i, url in enumerate(result.high_priority_urls[:3], 1):  # Show top 3
                print(f"   {i}. Priority {url.priority}: {url.url}")
                print(f"      Reason: {url.reason}")
        
        if result.errors:
            print(f"\n❌ Errors encountered: {result.errors}")
        
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")


def example_2_analyze_direct_inputs():
    """
    Example 2: Analyze with direct extracted images and URLs
    
    This demonstrates how to use the agent when you already have
    extracted images and URLs from another source.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Analyzing Direct Inputs")
    print("=" * 60)
    
    # Create sample extracted image (in real usage, this would come from pdf_processing)
    sample_image = ExtractedImage(
        page_number=0,
        base64_data="iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",  # 1x1 transparent PNG
        format="PNG",
        phash="sample_phash",
        saved_path="./extracted_images/image_0.png",
        image_sha1="sample_sha1"
    )
    
    # Create sample extracted URL
    sample_url = ExtractedURL(
        url="https://suspicious-domain.com/download",
        page_number=0,
        url_type="annotation",
        coordinates={"x": 100, "y": 200, "width": 150, "height": 30},
        is_external=True
    )
    
    # Create input with direct data
    input_data = VisualAnalysisInput(
        extracted_images=[sample_image],
        extracted_urls=[sample_url]
    )
    
    print(f"🖼️  Analyzing {len(input_data.extracted_images)} images")
    print(f"🔗 Cross-referencing with {len(input_data.extracted_urls)} URLs")
    
    try:
        # Note: This example will likely fail with the sample data since it's not a real image
        # but it demonstrates the API usage pattern
        result = process_pdf_with_visual_agent(input_data)
        
        print(f"✅ Analysis completed: {result.success}")
        print(f"🎯 Verdict: {result.overall_verdict}")
        print(f"📈 Confidence: {result.overall_confidence:.2f}")
        
    except Exception as e:
        print(f"⚠️  Expected failure with sample data: {str(e)}")
        print("   In real usage, provide actual base64 image data")


def example_3_integration_with_pdf_processing():
    """
    Example 3: Integration with PDF Processing Agent
    
    This shows how to chain the pdf_processing agent output
    directly into the visual_analysis agent.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Integration with PDF Processing")
    print("=" * 60)
    
    # This would typically be done in pdf_hunter_main, but shows the pattern
    pdf_path = "tests/sample_document.pdf"
    
    if not Path(pdf_path).exists():
        print(f"⚠️  PDF file not found: {pdf_path}")
        print("   This example requires a PDF file to demonstrate integration.")
        return
    
    try:
        # Step 1: Use PDF processing agent to extract images and URLs
        from pdf_processing.pdf_agent import process_pdf_with_agent
        from pdf_processing.agent_schemas import PDFProcessingInput
        
        print("📊 Step 1: Processing PDF to extract images and URLs...")
        pdf_input = PDFProcessingInput(
            pdf_path=pdf_path,
            pages_to_process=1
        )
        
        pdf_result = process_pdf_with_agent(pdf_input)
        
        if not pdf_result.success:
            print(f"❌ PDF processing failed: {pdf_result.errors}")
            return
        
        print(f"✅ Extracted {len(pdf_result.extracted_images)} images and {len(pdf_result.extracted_urls)} URLs")
        
        # Step 2: Use visual analysis agent with the extracted data
        print("👁️  Step 2: Performing visual deception analysis...")
        
        visual_input = VisualAnalysisInput(
            extracted_images=pdf_result.extracted_images,
            extracted_urls=pdf_result.extracted_urls
        )
        
        visual_result = process_pdf_with_visual_agent(visual_input)
        
        # Step 3: Display combined results
        print(f"\n🎯 Final Results:")
        print(f"   PDF Processing: {len(pdf_result.extracted_images)} images, {len(pdf_result.extracted_urls)} URLs")
        print(f"   Visual Analysis: {visual_result.overall_verdict} (confidence: {visual_result.overall_confidence:.2f})")
        print(f"   Deception Tactics: {len(visual_result.all_deception_tactics)}")
        print(f"   High Priority URLs: {len(visual_result.high_priority_urls)}")
        
    except ImportError as e:
        print(f"⚠️  Import error: {str(e)}")
        print("   Make sure all dependencies are installed: pip install -e .")
    except Exception as e:
        print(f"❌ Integration example failed: {str(e)}")


def example_4_langgraph_studio_usage():
    """
    Example 4: Usage patterns for LangGraph Studio
    
    This shows how the agent appears and can be used in LangGraph Studio.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 4: LangGraph Studio Usage")
    print("=" * 60)
    
    print("🎨 In LangGraph Studio, the visual_analysis graph provides:")
    print("   • Clean input interface showing only user-facing fields")
    print("   • Real-time state inspection during processing")
    print("   • Visual workflow representation")
    print("   • Step-by-step execution monitoring")
    
    print("\n📋 Input Schema (what you'll see in LangGraph Studio):")
    # Create a sample input to show the schema
    sample_input = VisualAnalysisInput(pdf_path="example.pdf", pages_to_process=1)
    schema_dict = sample_input.model_dump()
    print(json.dumps(schema_dict, indent=2))
    
    print("\n🔧 To use in LangGraph Studio:")
    print("   1. Run: langgraph dev")
    print("   2. Select the 'visual_analysis' graph")
    print("   3. Provide either:")
    print("      • pdf_path + pages_to_process (for full pipeline)")
    print("      • extracted_images + extracted_urls (for direct analysis)")
    print("   4. Execute and monitor the workflow")
    
    print("\n📊 Output will include:")
    print("   • Overall verdict and confidence score")
    print("   • Detailed analysis for each page")
    print("   • Detected deception tactics and benign signals")
    print("   • High priority URLs for further investigation")


def example_5_error_handling():
    """
    Example 5: Error handling and edge cases
    
    This demonstrates how the agent handles various error conditions.
    """
    print("\n" + "=" * 60)
    print("EXAMPLE 5: Error Handling")
    print("=" * 60)
    
    # Test case 1: Non-existent PDF file
    print("🧪 Test 1: Non-existent PDF file")
    try:
        input_data = VisualAnalysisInput(pdf_path="non_existent.pdf")
        result = process_pdf_with_visual_agent(input_data)
        print(f"   Result: {result.success}, Errors: {len(result.errors)}")
    except Exception as e:
        print(f"   Exception caught: {str(e)}")
    
    # Test case 2: Empty inputs
    print("\n🧪 Test 2: Empty inputs")
    try:
        input_data = VisualAnalysisInput(
            extracted_images=[],
            extracted_urls=[]
        )
        result = process_pdf_with_visual_agent(input_data)
        print(f"   Result: {result.success}, Errors: {len(result.errors)}")
    except Exception as e:
        print(f"   Exception caught: {str(e)}")
    
    print("\n✅ The agent provides graceful error handling with:")
    print("   • Detailed error messages in the output")
    print("   • Fallback analysis results when possible")
    print("   • Clear success indicators")
    print("   • Processing time tracking even for failed runs")


def main():
    """
    Run all examples to demonstrate the visual analysis agent capabilities.
    """
    print("🎯 Visual Analysis Agent - Example Usage")
    print("=" * 60)
    print("This script demonstrates various ways to use the Visual Deception Analyst")
    print("for PDF visual analysis and cross-modal deception detection.")
    
    # Run all examples
    example_1_analyze_pdf_file()
    example_2_analyze_direct_inputs()
    example_3_integration_with_pdf_processing()
    example_4_langgraph_studio_usage()
    example_5_error_handling()
    
    print("\n" + "=" * 60)
    print("🎉 Examples completed!")
    print("=" * 60)
    print("Next steps:")
    print("• Update PDF paths to point to your actual test files")
    print("• Try the agent in LangGraph Studio: langgraph dev")
    print("• Integrate with pdf_hunter_main for complete analysis pipeline")
    print("• Customize prompts in visual_analysis/prompts.py as needed")


if __name__ == "__main__":
    main()