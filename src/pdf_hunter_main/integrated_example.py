"""
Example of the Complete Integrated PDF Hunter with Visual Analysis

This demonstrates the enhanced PDF Hunter pipeline that now includes:
1. PDF Processing (extract images, URLs, hashes)
2. Static Analysis (forensic investigation) 
3. Visual Analysis (deception detection) - NEW!
4. Final Aggregation (comprehensive results)

The static and visual analysis now run in parallel for better performance.
"""

from pdf_hunter_main.schemas import PDFHunterInput
from pdf_hunter_main.pdf_hunter_graph import process_pdf_with_hunter

def demonstrate_integrated_pipeline():
    """
    Demonstrate the complete integrated pipeline with visual analysis.
    """
    print("🚀 PDF Hunter - Integrated Pipeline with Visual Analysis")
    print("=" * 70)
    
    # Note: Update this path to point to an actual PDF file for testing
    test_pdf = "tests/sample.pdf"  # Update this path
    
    try:
        # Create input for the complete pipeline
        input_data = PDFHunterInput(
            pdf_path=test_pdf,
            pages_to_process=1,  # Process first page
            output_directory="./integrated_analysis_output"
        )
        
        print(f"📄 Analyzing: {input_data.pdf_path}")
        print(f"📊 Pages to process: {input_data.pages_to_process}")
        print(f"📁 Output directory: {input_data.output_directory}")
        
        print("\n🔄 Running Complete Analysis Pipeline...")
        print("   • PDF Processing (extract images, URLs, hashes)")
        print("   • Static Analysis (forensic investigation)")  
        print("   • Visual Analysis (deception detection)")
        print("   • Final Aggregation (comprehensive results)")
        
        # Process with the complete hunter pipeline
        result = process_pdf_with_hunter(input_data)
        
        print(f"\n" + "=" * 70)
        print(f"🏁 COMPLETE ANALYSIS RESULTS")
        print(f"=" * 70)
        
        # Overall Results
        print(f"✅ Overall Success: {result.success}")
        print(f"⏱️  Total Processing Time: {result.total_processing_time:.2f}s")
        
        # PDF Processing Results
        print(f"\n📊 PDF Processing Results:")
        print(f"   • Page Count: {result.page_count}")
        print(f"   • Images Extracted: {len(result.extracted_images)}")
        print(f"   • URLs Found: {len(result.extracted_urls)}")
        if result.pdf_hash:
            print(f"   • PDF SHA1: {result.pdf_hash.sha1[:16]}...")
        print(f"   • Processing Errors: {len(result.pdf_processing_errors)}")
        
        # Static Analysis Results
        print(f"\n🕵️  Static Analysis Results:")
        print(f"   • Forensic Verdict: {result.forensic_verdict.value if result.forensic_verdict else 'N/A'}")
        print(f"   • Coherence Score: {result.narrative_coherence_score}")
        print(f"   • IoCs Found: {len(result.indicators_of_compromise)}")
        print(f"   • Attack Chain Length: {result.attack_chain_length or 0}")
        print(f"   • Artifacts Extracted: {result.extracted_artifacts_count or 0}")
        print(f"   • Analysis Errors: {len(result.forensic_analysis_errors)}")
        
        # Visual Analysis Results - NEW!
        print(f"\n👁️  Visual Analysis Results:")
        if result.visual_analysis_result:
            visual = result.visual_analysis_result
            print(f"   • Visual Verdict: {visual.overall_verdict}")
            print(f"   • Confidence Score: {visual.overall_confidence:.2f}")
            print(f"   • Pages Analyzed: {visual.total_pages_analyzed}")
            print(f"   • Deception Tactics Found: {len(visual.all_deception_tactics)}")
            print(f"   • Benign Signals Found: {len(visual.all_benign_signals)}")
            print(f"   • High Priority URLs: {len(visual.high_priority_urls)}")
            print(f"   • Executive Summary: {visual.executive_summary}")
        else:
            print(f"   • Visual Analysis: Not available")
        print(f"   • Analysis Errors: {len(result.visual_analysis_errors)}")
        
        # Combined Intelligence Assessment
        print(f"\n🎯 Combined Intelligence Assessment:")
        print(f"   • Is Suspicious (Forensic): {result.is_suspicious()}")
        print(f"   • Has Forensic Artifacts: {result.has_artifacts()}")
        if result.visual_analysis_result:
            visual_suspicious = result.visual_analysis_result.overall_verdict in ["Suspicious", "Highly Deceptive"]
            print(f"   • Is Suspicious (Visual): {visual_suspicious}")
        
        # Show detailed findings if available
        if result.visual_analysis_result and result.visual_analysis_result.all_deception_tactics:
            print(f"\n🚨 Top Deception Tactics Detected:")
            for i, tactic in enumerate(result.visual_analysis_result.all_deception_tactics[:3], 1):
                print(f"   {i}. {tactic.tactic_type} (confidence: {tactic.confidence:.2f})")
                print(f"      {tactic.description}")
        
        if result.visual_analysis_result and result.visual_analysis_result.high_priority_urls:
            print(f"\n🔗 High Priority URLs for Investigation:")
            for i, url in enumerate(result.visual_analysis_result.high_priority_urls[:3], 1):
                print(f"   {i}. Priority {url.priority}: {url.url}")
                print(f"      Reason: {url.reason}")
        
        # Error Summary
        total_errors = (len(result.pdf_processing_errors) + 
                       len(result.forensic_analysis_errors) + 
                       len(result.visual_analysis_errors))
        
        if total_errors > 0:
            print(f"\n⚠️  Errors Encountered ({total_errors} total):")
            for error in result.pdf_processing_errors:
                print(f"   • PDF Processing: {error}")
            for error in result.forensic_analysis_errors:
                print(f"   • Static Analysis: {error}")
            for error in result.visual_analysis_errors:
                print(f"   • Visual Analysis: {error}")
        
        print(f"\n📋 Complete Analysis Summary:")
        summary = result.get_summary()
        for category, data in summary.items():
            if isinstance(data, dict):
                print(f"   {category.replace('_', ' ').title()}:")
                for key, value in data.items():
                    print(f"     - {key.replace('_', ' ').title()}: {value}")
            else:
                print(f"   {category.replace('_', ' ').title()}: {data}")
        
        return result
        
    except FileNotFoundError:
        print(f"❌ PDF file not found: {test_pdf}")
        print("   Please update the test_pdf path to point to an actual PDF file.")
        return None
    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def demonstrate_access_patterns():
    """
    Demonstrate how to access the complete visual analysis results.
    """
    print(f"\n" + "=" * 70)
    print(f"📖 VISUAL ANALYSIS ACCESS PATTERNS")
    print(f"=" * 70)
    
    print("After running process_pdf_with_hunter(), you can access:")
    print()
    print("# Get complete visual analysis results:")
    print("visual_result = result.visual_analysis_result")
    print("if visual_result:")
    print("    print(f'Verdict: {visual_result.overall_verdict}')")
    print("    print(f'Confidence: {visual_result.overall_confidence}')")
    print("    print(f'Summary: {visual_result.executive_summary}')")
    print()
    print("# Access specific findings:")
    print("for tactic in visual_result.all_deception_tactics:")
    print("    print(f'Found: {tactic.tactic_type} - {tactic.description}')")
    print()
    print("for url in visual_result.high_priority_urls:")
    print("    print(f'Investigate: {url.url} (Priority {url.priority})')")
    print()
    print("# Get per-page analysis:")
    print("for page_analysis in visual_result.page_analyses:")
    print("    print(f'Page analysis: {page_analysis.visual_verdict}')")
    print()
    print("# Access through summary:")
    print("summary = result.get_summary()")
    print("visual_summary = summary['visual_analysis']")
    print("print(f'Visual analysis available: {visual_summary[\"available\"]}')")


if __name__ == "__main__":
    # Run the demonstration
    result = demonstrate_integrated_pipeline()
    
    # Show access patterns
    demonstrate_access_patterns()
    
    print(f"\n" + "=" * 70)
    print(f"🎉 INTEGRATION COMPLETE!")
    print(f"=" * 70)
    print("The PDF Hunter now includes:")
    print("✅ PDF Processing (images, URLs, hashes)")
    print("✅ Static Analysis (forensic investigation)")
    print("✅ Visual Analysis (deception detection) - NEW!")
    print("✅ Parallel processing for better performance")
    print("✅ Complete results aggregation")
    print("✅ Future-ready for overview agent integration")
    print()
    print("Next steps:")
    print("• Test with actual PDF files")
    print("• Use in LangGraph Studio: langgraph dev -> select 'pdf_hunter'")
    print("• Future: Add overview agent for final decision making")