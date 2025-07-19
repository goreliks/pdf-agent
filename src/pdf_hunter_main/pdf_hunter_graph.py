"""
PDF Hunter Main Graph

This module implements the composed LangGraph that integrates PDF processing 
and static analysis as subgraphs using the "different state schemas" pattern.

Flow: PDF Processing -> Transform -> Static Analysis -> Final Aggregation
"""

import time
from typing import Dict, Any

from langgraph.graph import StateGraph, START, END

# Import subgraph apps and schemas
from pdf_processing.pdf_agent import app as pdf_processing_app
from pdf_processing.agent_schemas import PDFProcessingInput

from static_analysis.graph import app as static_analysis_app  
from static_analysis.schemas import ForensicCaseFileInput, ForensicCaseFile, ForensicCaseFileOutput, Verdict, AnalysisPhase

# Import our main schemas
try:
    # Try relative imports first (when run as module)
    from .schemas import PDFHunterInput, PDFHunterOutput, PDFHunterState
except ImportError:
    # Fallback to absolute imports (when run directly)
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from pdf_hunter_main.schemas import PDFHunterInput, PDFHunterOutput, PDFHunterState


def pdf_processing_node(state: PDFHunterState) -> Dict[str, Any]:
    """
    Node that invokes the PDF processing subgraph.
    
    Transforms the main state to PDF processing input, invokes the subgraph,
    and transforms the result back to main state format.
    """
    try:
        print("🔍 Starting PDF Processing subgraph...")
        
        # Transform main state to PDF processing input
        pdf_input = PDFProcessingInput(
            pdf_path=state["pdf_path"],
            pages_to_process=state.get("pages_to_process", 1),
            output_directory=state.get("output_directory")
        )
        
        # Invoke the PDF processing subgraph
        pdf_result_dict = pdf_processing_app.invoke(pdf_input.model_dump())
        
        # Convert dict result to PDFProcessingOutput if needed
        if isinstance(pdf_result_dict, dict):
            from pdf_processing.agent_schemas import PDFProcessingOutput
            pdf_result = PDFProcessingOutput(**pdf_result_dict)
        else:
            pdf_result = pdf_result_dict
        
        print(f"✅ PDF Processing completed. Success: {pdf_result.success}")
        print(f"   - Images extracted: {len(pdf_result.extracted_images)}")
        print(f"   - URLs found: {len(pdf_result.extracted_urls)}")
        
        # Transform result back to main state
        return {
            "pdf_processing_result": pdf_result
        }
        
    except Exception as e:
        error_msg = f"PDF processing failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "errors": [error_msg],
            "pdf_processing_result": None
        }


def static_analysis_node(state: PDFHunterState) -> Dict[str, Any]:
    """
    Node that invokes the static analysis subgraph.
    
    Transforms the main state to forensic analysis input, invokes the subgraph,
    and transforms the result back to main state format.
    """
    try:
        print("🕵️ Starting Static Analysis subgraph...")
        
        # Transform main state to static analysis input (only needs file_path)
        forensic_input = ForensicCaseFileInput(
            file_path=state["pdf_path"]
        )
        
        # Invoke the static analysis subgraph
        forensic_result_dict = static_analysis_app.invoke(forensic_input.model_dump())
        
        # Debug: Print what we actually received
        print(f"🔍 Debug: Static analysis returned type: {type(forensic_result_dict)}")
        if isinstance(forensic_result_dict, dict):
            evidence = forensic_result_dict.get('evidence', {})
            # Handle both dict and EvidenceLocker object
            if hasattr(evidence, 'indicators_of_compromise'):
                # EvidenceLocker object
                iocs = evidence.indicators_of_compromise
                attack_chain = evidence.attack_chain
            else:
                # Dictionary
                iocs = evidence.get('indicators_of_compromise', [])
                attack_chain = evidence.get('attack_chain', [])
            print(f"🔍 Debug: IoCs in dict evidence: {len(iocs)}")
            print(f"🔍 Debug: Attack chain in dict evidence: {len(attack_chain)}")
            # Additional debug to see the actual IoC data
            if iocs:
                print(f"🔍 Debug: First IoC: {iocs[0]}")
        elif hasattr(forensic_result_dict, 'indicators_of_compromise'):
            print(f"🔍 Debug: IoCs in result: {len(forensic_result_dict.indicators_of_compromise)}")
        if hasattr(forensic_result_dict, 'attack_chain_length'):
            print(f"🔍 Debug: Attack chain length: {forensic_result_dict.attack_chain_length}")
        
        # Handle the result based on what LangGraph returns
        if isinstance(forensic_result_dict, dict):
            # The static analysis returns a ForensicCaseFile dict, we need to convert it to ForensicCaseFileOutput
            try:
                # First convert to ForensicCaseFile to get the full state
                case_file = ForensicCaseFile(**forensic_result_dict)
                
                # Debug the case_file IoCs
                print(f"🔍 Debug: case_file IoCs: {len(case_file.evidence.indicators_of_compromise)}")
                
                # Then convert to the output schema using the conversion function
                forensic_result = ForensicCaseFileOutput(
                    success=len(case_file.errors) == 0,
                    file_path=case_file.file_path,
                    file_hash_sha256=case_file.file_hash_sha256,
                    analysis_session_id=case_file.analysis_session_id,
                    verdict=case_file.verdict,
                    phase=case_file.phase,
                    current_hypothesis=case_file.current_hypothesis,
                    narrative_coherence_score=case_file.narrative_coherence.score,
                    total_interrogation_steps=case_file.interrogation_steps,
                    indicators_of_compromise=case_file.evidence.indicators_of_compromise,
                    attack_chain_length=len(case_file.evidence.attack_chain),
                    extracted_artifacts_count=len(case_file.evidence.extracted_artifacts),
                    final_report=case_file.final_report,
                    errors=case_file.errors
                )
                print(f"🔍 Debug: Converted dict to ForensicCaseFileOutput with {len(forensic_result.indicators_of_compromise)} IoCs and attack chain length {forensic_result.attack_chain_length}")
            except Exception as e:
                # If conversion fails, create a minimal output with error info
                forensic_result = ForensicCaseFileOutput(
                    success=False,
                    file_path=forensic_input.file_path,
                    analysis_session_id="conversion_failed",
                    verdict=Verdict.PRESUMED_INNOCENT,
                    phase=AnalysisPhase.TRIAGE, 
                    narrative_coherence_score=0.5,
                    total_interrogation_steps=0,
                    errors=[f"Failed to convert static analysis result: {str(e)}"]
                )
        elif isinstance(forensic_result_dict, ForensicCaseFileOutput):
            # LangGraph already converted it to ForensicCaseFileOutput due to output_schema
            forensic_result = forensic_result_dict
            print(f"🔍 Debug: Using direct ForensicCaseFileOutput object")
        else:
            # Fallback case - create a minimal output with error
            forensic_result = ForensicCaseFileOutput(
                success=False,
                file_path=forensic_input.file_path,
                analysis_session_id="unexpected_type",
                verdict=Verdict.PRESUMED_INNOCENT,
                phase=AnalysisPhase.TRIAGE,
                narrative_coherence_score=0.5,
                total_interrogation_steps=0,
                errors=[f"Unexpected result type from static analysis: {type(forensic_result_dict)}"]
            )
        
        print(f"✅ Static Analysis completed. Success: {forensic_result.success}")
        print(f"   - Verdict: {forensic_result.verdict.value}")
        print(f"   - IoCs found: {len(forensic_result.indicators_of_compromise)}")
        print(f"   - Attack chain length: {forensic_result.attack_chain_length}")
        
        # Transform result back to main state
        return {
            "static_analysis_result": forensic_result
        }
        
    except Exception as e:
        error_msg = f"Static analysis failed: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "errors": [error_msg],
            "static_analysis_result": None
        }


def final_aggregation_node(state: PDFHunterState) -> PDFHunterOutput:
    """
    Final aggregation node that combines results from both subgraphs 
    into the final output schema.
    """
    try:
        print("📊 Performing final aggregation...")
        
        # Get results from both subgraphs
        pdf_result = state.get("pdf_processing_result")
        forensic_result = state.get("static_analysis_result")
        main_errors = state.get("errors", [])
        
        # Determine overall success - handle both dict and object types
        if isinstance(pdf_result, dict):
            pdf_success = pdf_result.get("success", False)
        else:
            pdf_success = pdf_result.success if pdf_result else False
            
        if isinstance(forensic_result, dict):
            forensic_success = forensic_result.get("success", False)
        else:
            forensic_success = forensic_result.success if forensic_result else False
            
        overall_success = pdf_success and forensic_success and len(main_errors) == 0
        
        # Helper function to safely get attributes from dict or object
        def safe_get(obj, attr, default=None):
            if obj is None:
                return default
            if isinstance(obj, dict):
                return obj.get(attr, default)
            else:
                return getattr(obj, attr, default)
        
        # Helper function to safely get IoCs, ensuring they are properly serializable
        def safe_get_iocs(obj, default=None):
            if default is None:
                default = []
            iocs = safe_get(obj, "indicators_of_compromise", default)
            # If we got Pydantic objects, convert them to dicts and back to ensure compatibility
            if iocs and hasattr(iocs[0], 'model_dump'):
                from static_analysis.schemas import IndicatorOfCompromise
                return [IndicatorOfCompromise(**ioc.model_dump()) if hasattr(ioc, 'model_dump') else ioc for ioc in iocs]
            return iocs
        
        # Create comprehensive output
        output = PDFHunterOutput(
            success=overall_success,
            pdf_path=state["pdf_path"],
            
            # PDF Processing Results
            pdf_hash=safe_get(pdf_result, "pdf_hash"),
            page_count=safe_get(pdf_result, "page_count"),
            extracted_images=safe_get(pdf_result, "extracted_images", []),
            extracted_urls=safe_get(pdf_result, "extracted_urls", []),
            
            # Static Analysis Results
            forensic_verdict=safe_get(forensic_result, "verdict"),
            analysis_phase=safe_get(forensic_result, "phase"),
            forensic_hypothesis=safe_get(forensic_result, "current_hypothesis"),
            narrative_coherence_score=safe_get(forensic_result, "narrative_coherence_score"),
            indicators_of_compromise=safe_get_iocs(forensic_result, []),
            attack_chain_length=safe_get(forensic_result, "attack_chain_length"),
            extracted_artifacts_count=safe_get(forensic_result, "extracted_artifacts_count"),
            forensic_session_id=safe_get(forensic_result, "analysis_session_id"),
            
            # Error aggregation
            pdf_processing_errors=safe_get(pdf_result, "errors", []),
            forensic_analysis_errors=safe_get(forensic_result, "errors", []),
            
            # Timing will be set by the main processing function
            total_processing_time=None
        )
        
        print(f"✅ Final aggregation completed. Overall success: {overall_success}")
        
        return output
        
    except Exception as e:
        error_msg = f"Final aggregation failed: {str(e)}"
        print(f"❌ {error_msg}")
        
        # Return a failure result
        return PDFHunterOutput(
            success=False,
            pdf_path=state.get("pdf_path", "unknown"),
            pdf_processing_errors=safe_get(pdf_result, "errors", []) if 'pdf_result' in locals() else [],
            forensic_analysis_errors=safe_get(forensic_result, "errors", []) if 'forensic_result' in locals() else [],
            total_processing_time=None
        )


def create_pdf_hunter_graph() -> StateGraph:
    """
    Create the main PDF Hunter graph with subgraph composition.
    
    Graph Flow:
    START -> pdf_processing (subgraph) -> static_analysis (subgraph) -> final_aggregation -> END
    
    Input Schema: PDFHunterInput (user-facing fields only)
    Output Schema: PDFHunterOutput (comprehensive results)
    Internal State: PDFHunterState (manages subgraph results)
    
    Returns:
        Compiled StateGraph for comprehensive PDF analysis
    """
    # Create the state graph with explicit input and output schemas
    builder = StateGraph(
        state_schema=PDFHunterState,
        input_schema=PDFHunterInput,
        output_schema=PDFHunterOutput
    )
    
    # Add nodes - note that subgraphs are added as node functions, not directly
    builder.add_node("pdf_processing", pdf_processing_node)
    builder.add_node("static_analysis", static_analysis_node)
    builder.add_node("final_aggregation", final_aggregation_node)
    
    # Create the sequential flow
    builder.add_edge(START, "pdf_processing")
    builder.add_edge("pdf_processing", "static_analysis")
    builder.add_edge("static_analysis", "final_aggregation")
    builder.add_edge("final_aggregation", END)
    
    # Compile the graph
    return builder.compile()


def process_pdf_with_hunter(input_data: PDFHunterInput) -> PDFHunterOutput:
    """
    Process a PDF using the complete Hunter pipeline with both PDF processing and forensic analysis.
    
    Args:
        input_data: PDFHunterInput with validated input parameters
        
    Returns:
        PDFHunterOutput with comprehensive analysis results
        
    Example:
        >>> from pdf_hunter_main import process_pdf_with_hunter, PDFHunterInput
        >>> input_data = PDFHunterInput(
        ...     pdf_path="suspicious.pdf",
        ...     pages_to_process=2,
        ...     output_directory="./analysis_output"
        ... )
        >>> result = process_pdf_with_hunter(input_data)
        >>> print(f"Verdict: {result.forensic_verdict}")
        >>> print(f"Images extracted: {len(result.extracted_images)}")
        >>> print(f"Is suspicious: {result.is_suspicious()}")
    """
    print("🚀 Starting PDF Hunter Analysis Pipeline")
    print("=" * 60)
    print(f"📁 PDF: {input_data.pdf_path}")
    print(f"📄 Pages to process: {input_data.pages_to_process}")
    print(f"📂 Output directory: {input_data.output_directory or 'auto-generated'}")
    
    # Create the processing graph
    graph = create_pdf_hunter_graph()
    
    # Convert input to state format and execute
    start_time = time.time()
    
    initial_state = {
        "pdf_path": input_data.pdf_path,
        "pages_to_process": input_data.pages_to_process,
        "output_directory": input_data.output_directory,
        "pdf_processing_result": None,
        "static_analysis_result": None,
        "errors": []
    }
    
    # Execute the graph
    final_result = graph.invoke(initial_state)
    
    total_time = time.time() - start_time
    
    # Update the processing time in the result
    if isinstance(final_result, PDFHunterOutput):
        # Update the processing time
        result_dict = final_result.model_dump()
        result_dict.pop('total_processing_time', None)  # Remove existing value
        updated_result = PDFHunterOutput(
            **result_dict,
            total_processing_time=total_time
        )
    elif isinstance(final_result, dict):
        # Convert dict to PDFHunterOutput and add processing time
        final_result.pop('total_processing_time', None)  # Remove if exists
        updated_result = PDFHunterOutput(
            **final_result,
            total_processing_time=total_time
        )
    else:
        # Fallback handling
        updated_result = final_result
        if hasattr(updated_result, 'total_processing_time'):
            updated_result.total_processing_time = total_time
    
    print("=" * 60)
    print(f"🏁 PDF Hunter Analysis Complete!")
    print(f"⏱️  Total time: {total_time:.2f}s")
    print(f"✅ Success: {updated_result.success}")
    if updated_result.forensic_verdict:
        print(f"🔍 Verdict: {updated_result.forensic_verdict.value}")
    print(f"📊 Summary: {updated_result.get_summary()}")
    
    return updated_result


# Export the app for LangGraph Studio
app = create_pdf_hunter_graph()


def main():
    """Main function for testing the PDF Hunter graph."""
    print("PDF Hunter Main Graph - Test Execution")
    print("=" * 60)
    
    # Test configuration - use absolute path from project root
    pdf_path = "tests/test_mal_one.pdf"
    pdf_path = "tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    
    try:
        # Create validated input
        input_data = PDFHunterInput(
            pdf_path=pdf_path,
            pages_to_process=1,  # Process first page only for testing
            output_directory="./hunter_test_output"
        )
        
        print(f"✅ Input validation successful")
        print(f"   PDF Path: {input_data.pdf_path}")
        print(f"   Pages: {input_data.pages_to_process}")
        print(f"   Output: {input_data.output_directory}")
        
        # Process with the full hunter pipeline
        result = process_pdf_with_hunter(input_data)
        
        # Print comprehensive results
        print(f"\n=== Comprehensive PDF Analysis Results ===")
        print(f"Overall Success: {result.success}")
        print(f"Processing Time: {result.total_processing_time:.2f}s")
        
        print(f"\n--- PDF Processing Results ---")
        print(f"Page Count: {result.page_count}")
        print(f"Images Extracted: {len(result.extracted_images)}")
        print(f"URLs Found: {len(result.extracted_urls)}")
        if result.pdf_hash:
            print(f"PDF SHA1: {result.pdf_hash.sha1}")
        
        print(f"\n--- Forensic Analysis Results ---")
        print(f"Verdict: {result.forensic_verdict.value if result.forensic_verdict else 'N/A'}")
        print(f"Coherence Score: {result.narrative_coherence_score}")
        print(f"IoCs Found: {len(result.indicators_of_compromise)}")
        print(f"Attack Chain Length: {result.attack_chain_length or 0}")
        print(f"Artifacts: {result.extracted_artifacts_count or 0}")
        
        print(f"\n--- Analysis Summary ---")
        print(f"Is Suspicious: {result.is_suspicious()}")
        print(f"Has Artifacts: {result.has_artifacts()}")
        
        if result.pdf_processing_errors:
            print(f"\n--- PDF Processing Errors ---")
            for error in result.pdf_processing_errors:
                print(f"  - {error}")
                
        if result.forensic_analysis_errors:
            print(f"\n--- Forensic Analysis Errors ---")
            for error in result.forensic_analysis_errors:
                print(f"  - {error}")
        
        return result
        
    except Exception as e:
        print(f"\n❌ Test execution failed: {e}")
        return None


if __name__ == "__main__":
    main() 