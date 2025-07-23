"""
Visual Analysis LangGraph Agent

This module implements a LangGraph workflow for Visual Deception Analysis (VDA)
of PDF pages. It performs cross-modal analysis combining visual evidence
(rendered PDF page images) with technical data (URLs, interactive elements)
to identify deception tactics and social engineering attempts.

The graph follows the validation → processing → aggregation pattern established
in other agents, with specialized nodes for visual analysis.
"""

import json
import time
from datetime import datetime
import pathlib
from typing import Dict, Any, List

from langgraph.graph import StateGraph, END, START
from pydantic import BaseModel

# Import our schemas, prompts, and utils
from visual_analysis.schemas import (
    VisualAnalysisInput, VisualAnalysisOutput, VisualAnalysisState,
    VisualAnalysisResults, ElementMap, DeceptionTactic, BenignSignal,
    DetailedFinding, PrioritizedURL
)
from visual_analysis.prompts import SYSTEM_PROMPT

# Import centralized LLM configuration
from config import VISUAL_ANALYSIS_ANALYST_LLM

# Import PDF processing capability for when PDF path is provided
from pdf_processing.pdf_agent import process_pdf_with_agent
from pdf_processing.agent_schemas import PDFProcessingInput
from pdf_processing.utils import ensure_output_directory


def validation_node(state: VisualAnalysisState) -> Dict[str, Any]:
    """
    Validates input and prepares data for visual analysis.
    If PDF path is provided, processes PDF to extract images and URLs.
    """
    print("\n--- Running Visual Analysis Validation Node ---")
    
    # Check if we have direct inputs or need to process PDF
    if not state.get("extracted_images") and state.get("pdf_path"):
        print("[*] Processing PDF to extract images and URLs...")
        
        # Process PDF using the pdf_processing agent
        pdf_input = PDFProcessingInput(
            pdf_path=state["pdf_path"],
            pages_to_process=state.get("pages_to_process", 1),
            output_directory=state.get("output_directory")
        )
        
        try:
            pdf_result = process_pdf_with_agent(pdf_input)
            
            if not pdf_result.success:
                return {
                    "errors": [f"PDF processing failed: {'; '.join(pdf_result.errors)}"],
                    "extracted_images": [],
                    "extracted_urls": [],
                    "total_pages": 0
                }
            
            return {
                "extracted_images": pdf_result.extracted_images,
                "extracted_urls": pdf_result.extracted_urls,
                "total_pages": len(pdf_result.extracted_images) if pdf_result.extracted_images else 0,
                "pdf_path": pdf_result.pdf_path
            }
            
        except Exception as e:
            return {
                "errors": [f"PDF processing error: {str(e)}"],
                "extracted_images": [],
                "extracted_urls": [],
                "total_pages": 0
            }
    
    # Use direct inputs
    extracted_images = state.get("extracted_images", [])
    extracted_urls = state.get("extracted_urls", [])
    
    if not extracted_images:
        return {
            "errors": ["No images available for visual analysis"],
            "total_pages": 0
        }
    
    print(f"[*] Validated {len(extracted_images)} images and {len(extracted_urls)} URLs for analysis")
    
    return {
        "extracted_images": extracted_images,
        "extracted_urls": extracted_urls,
        "total_pages": len(extracted_images)
    }


def element_mapping_node(state: VisualAnalysisState) -> Dict[str, Any]:
    """
    Creates structured element maps for each page, combining visual and technical data.
    """
    print("\n--- Running Element Mapping Node ---")
    
    extracted_images = state.get("extracted_images", [])
    extracted_urls = state.get("extracted_urls", [])
    
    if not extracted_images:
        return {"errors": ["No images available for element mapping"]}
    
    # Create element maps for each page
    element_maps = []
    pages_with_images = set(img["page_number"] if isinstance(img, dict) else img.page_number for img in extracted_images)
    
    for page_number in sorted(pages_with_images):
        try:
            element_map = ElementMap.from_extracted_data(extracted_urls, page_number)
            element_maps.append(element_map)
            print(f"[*] Created element map for page {page_number} with {len(element_map.interactive_elements)} elements")
        except Exception as e:
            print(f"[!] Error creating element map for page {page_number}: {str(e)}")
            return {"errors": [f"Element mapping failed for page {page_number}: {str(e)}"]}
    
    return {"element_maps": element_maps}


def visual_analysis_node(state: VisualAnalysisState) -> Dict[str, Any]:
    """
    Performs visual deception analysis using the VDA system.
    Analyzes each page image with its corresponding element map.
    """
    print("\n--- Running Visual Analysis Node ---")
    
    extracted_images = state.get("extracted_images", [])
    element_maps = state.get("element_maps", [])
    
    if not extracted_images:
        return {"errors": ["No images available for visual analysis"]}
    
    # Import utils here to avoid circular imports
    from visual_analysis.utils import create_llm_chain, analyze_page_image
    
    page_analyses = []
    
    # Group images by page and analyze each page
    images_by_page = {}
    for img in extracted_images:
        page_num = img["page_number"] if isinstance(img, dict) else img.page_number
        if page_num not in images_by_page:
            images_by_page[page_num] = []
        images_by_page[page_num].append(img)
    
    # Find corresponding element map for each page
    element_maps_by_page = {em.page_number: em for em in element_maps}
    
    for page_number in sorted(images_by_page.keys()):
        print(f"[*] Analyzing page {page_number}...")
        
        try:
            # Get the first (main) image for this page
            page_images = images_by_page[page_number]
            main_image = page_images[0]  # Use first image as primary
            
            # Get element map for this page
            element_map = element_maps_by_page.get(page_number)
            
            # Perform visual analysis for this page
            page_analysis = analyze_page_image(
                image=main_image,
                element_map=element_map,
                llm=VISUAL_ANALYSIS_ANALYST_LLM
            )
            
            page_analyses.append(page_analysis)
            print(f"[*] Completed analysis for page {page_number}: {page_analysis.visual_verdict}")
            
        except Exception as e:
            error_msg = f"Visual analysis failed for page {page_number}: {str(e)}"
            print(f"[!] {error_msg}")
            
            # Create a minimal error result for this page
            error_analysis = VisualAnalysisResults(
                visual_verdict="Suspicious",  # Default to suspicious on error
                confidence_score=0.0,
                summary=f"Analysis failed: {str(e)}"
            )
            page_analyses.append(error_analysis)
            
            return {"errors": [error_msg]}
    
    return {"page_analyses": page_analyses}


def aggregation_node(state: VisualAnalysisState) -> Dict[str, Any]:
    """
    Aggregates analysis results across all pages and generates final output.
    """
    print("\n--- Running Aggregation Node ---")
    
    page_analyses = state.get("page_analyses", [])
    extracted_images = state.get("extracted_images", [])
    
    if not page_analyses:
        return {"errors": ["No page analyses available for aggregation"]}
    
    print(f"[*] Aggregating results from {len(page_analyses)} pages...")
    
    # Aggregate all findings
    all_deception_tactics = []
    all_benign_signals = []
    high_priority_urls = []
    
    for analysis in page_analyses:
        all_deception_tactics.extend(analysis.deception_tactics)
        all_benign_signals.extend(analysis.benign_signals)
        # Only include high priority URLs (priority 1-3)
        high_priority_urls.extend([url for url in analysis.prioritized_urls if url.priority <= 3])
    
    # Determine overall verdict based on page analyses
    verdicts = [analysis.visual_verdict for analysis in page_analyses]
    
    if "Highly Deceptive" in verdicts:
        overall_verdict = "Highly Deceptive"
    elif "Suspicious" in verdicts:
        overall_verdict = "Suspicious"
    else:
        overall_verdict = "Benign"
    
    # Calculate overall confidence as weighted average
    if page_analyses:
        overall_confidence = sum(analysis.confidence_score for analysis in page_analyses) / len(page_analyses)
    else:
        overall_confidence = 0.0
    
    # Generate executive summary
    executive_summary = f"Visual analysis of {len(page_analyses)} pages revealed {overall_verdict.lower()} characteristics. "
    executive_summary += f"Found {len(all_deception_tactics)} deception tactics and {len(all_benign_signals)} benign signals. "
    executive_summary += f"Identified {len(high_priority_urls)} high-priority URLs requiring further investigation."
    
    print(f"[*] Overall verdict: {overall_verdict} (confidence: {overall_confidence:.2f})")
    print(f"[*] Found {len(all_deception_tactics)} deception tactics, {len(all_benign_signals)} benign signals")
    print(f"[*] Identified {len(high_priority_urls)} high-priority URLs")
    
    # Create the final output object
    final_output = VisualAnalysisOutput(
        success=len(state.get("errors", [])) == 0,
        pdf_path=state.get("pdf_path"),
        total_pages_analyzed=len(page_analyses),
        overall_verdict=overall_verdict,
        overall_confidence=overall_confidence,
        executive_summary=executive_summary,
        page_analyses=page_analyses,
        all_deception_tactics=all_deception_tactics,
        all_benign_signals=all_benign_signals,
        high_priority_urls=high_priority_urls,
        errors=state.get("errors", [])
    )
    
    # Save the results to a JSON file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"visual_analysis_report_{timestamp}.json"
    
    # Handle output directory
    output_directory = state.get("output_directory")
    if output_directory and output_directory.strip():
        # Save in specified output directory
        output_path = pathlib.Path(output_directory) / output_filename
        ensure_output_directory(output_path)
        print(f"[*] Saving visual analysis report to {output_path}...")
    else:
        # Save in current directory (like static analysis does)
        output_path = pathlib.Path(output_filename)
        print(f"[*] Saving visual analysis report to {output_path}...")
    
    try:
        with open(output_path, "w") as f:
            f.write(final_output.model_dump_json(indent=2))
        print("[*] Visual analysis report saved successfully.")
    except Exception as e:
        print(f"[!] Failed to save visual analysis report: {str(e)}")
        # Don't fail the entire process if saving fails
    
    return {
        "final_output": final_output
    }


def create_app():
    """
    Create and return the compiled LangGraph application for visual analysis.
    
    Input Schema: VisualAnalysisInput (user-facing interface)
    Output Schema: VisualAnalysisOutput (comprehensive analysis results)
    Internal State: VisualAnalysisState (complete processing state)
    """
    workflow = StateGraph(
        state_schema=VisualAnalysisState,
        input_schema=VisualAnalysisInput
    )
    
    # Add all the nodes to the graph
    workflow.add_node("validation", validation_node)
    workflow.add_node("element_mapping", element_mapping_node)
    workflow.add_node("visual_analysis", visual_analysis_node)
    workflow.add_node("aggregation", aggregation_node)
    
    # Define the graph's flow: validation → element_mapping → visual_analysis → aggregation
    workflow.set_entry_point("validation")
    workflow.add_edge("validation", "element_mapping")
    workflow.add_edge("element_mapping", "visual_analysis")
    workflow.add_edge("visual_analysis", "aggregation")
    workflow.add_edge("aggregation", END)
    
    return workflow.compile()


# Create the app instance for LangGraph CLI
app = create_app()


def convert_to_output_schema(state: VisualAnalysisState) -> VisualAnalysisOutput:
    """
    Convert the internal VisualAnalysisState to the VisualAnalysisOutput schema.
    This provides a clean, user-facing output format for LangGraph Studio.
    """
    # If final_output already exists, return it
    if "final_output" in state and isinstance(state["final_output"], VisualAnalysisOutput):
        return state["final_output"]
    
    # Create minimal output from available state
    page_analyses = state.get("page_analyses", [])
    errors = state.get("errors", [])
    
    return VisualAnalysisOutput(
        success=len(errors) == 0,
        pdf_path=state.get("pdf_path"),
        total_pages_analyzed=len(page_analyses),
        overall_verdict="Benign" if len(errors) == 0 and page_analyses else "Suspicious",
        overall_confidence=0.5,
        executive_summary="Visual analysis completed with available data.",
        page_analyses=page_analyses,
        errors=errors
    )


def process_pdf_with_visual_agent(input_data: VisualAnalysisInput) -> VisualAnalysisOutput:
    """
    Process PDF images using the Visual Analysis LangGraph agent.
    
    Args:
        input_data: VisualAnalysisInput with validated input parameters
        
    Returns:
        VisualAnalysisOutput with comprehensive visual analysis results
        
    Example:
        >>> from visual_analysis.schemas import VisualAnalysisInput
        >>> input_data = VisualAnalysisInput(pdf_path="suspicious.pdf")
        >>> result = process_pdf_with_visual_agent(input_data)
        >>> print(f"Verdict: {result.overall_verdict}")
        >>> print(f"High priority URLs: {len(result.high_priority_urls)}")
    """
    print(f"[*] Starting visual analysis with input: {input_data.model_dump()}")
    
    # Record start time
    start_time = time.time()
    
    # Create the processing graph
    graph = create_app()
    
    try:
        # Execute the graph with the validated input
        final_result = graph.invoke(input_data.model_dump())
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Extract the final output
        if isinstance(final_result, dict):
            # Look for final_output in the result
            if "final_output" in final_result and isinstance(final_result["final_output"], VisualAnalysisOutput):
                output = final_result["final_output"]
                output.total_processing_time = processing_time
                return output
            else:
                # Convert dictionary result to VisualAnalysisState first, then to output
                state = final_result
                output = convert_to_output_schema(state)
                output.total_processing_time = processing_time
                return output
        elif isinstance(final_result, VisualAnalysisOutput):
            final_result.total_processing_time = processing_time
            return final_result
        else:
            # Fallback - create minimal output
            return VisualAnalysisOutput(
                success=False,
                total_pages_analyzed=0,
                overall_verdict="Suspicious",
                overall_confidence=0.0,
                executive_summary="Visual analysis failed due to unexpected result format.",
                total_processing_time=processing_time,
                errors=[f"Unexpected result type: {type(final_result)}"]
            )
            
    except Exception as e:
        processing_time = time.time() - start_time
        print(f"[!] Visual analysis failed: {str(e)}")
        
        return VisualAnalysisOutput(
            success=False,
            total_pages_analyzed=0,
            overall_verdict="Suspicious",
            overall_confidence=0.0,
            executive_summary=f"Visual analysis failed: {str(e)}",
            total_processing_time=processing_time,
            errors=[str(e)]
        )


def main():
    """Main function for running the visual analysis."""
    print("--- Setting up Visual Analysis Graph ---")
    
    # Example usage with test file - use absolute path to avoid path issues
    import os
    # Get the project root directory (go up from src/visual_analysis/ to project root)
    current_file = os.path.abspath(__file__)
    visual_analysis_dir = os.path.dirname(current_file)  # src/visual_analysis/
    src_dir = os.path.dirname(visual_analysis_dir)       # src/
    project_root = os.path.dirname(src_dir)              # project root
    test_pdf = os.path.join(project_root, "tests", "test_mal_one.pdf")
    
    # Option 1: Analyze from PDF path
    pdf_input = VisualAnalysisInput(pdf_path=test_pdf, pages_to_process=1)
    
    print("\n--- Processing PDF with Visual Analysis Agent ---")
    result = process_pdf_with_visual_agent(pdf_input)
    
    print(f"\n--- Final Results ---")
    print(f"Success: {result.success}")
    print(f"Overall Verdict: {result.overall_verdict}")
    print(f"Confidence: {result.overall_confidence:.2f}")
    print(f"Pages Analyzed: {result.total_pages_analyzed}")
    print(f"Deception Tactics: {len(result.all_deception_tactics)}")
    print(f"Benign Signals: {len(result.all_benign_signals)}")
    print(f"High Priority URLs: {len(result.high_priority_urls)}")
    print(f"Processing Time: {result.total_processing_time:.2f}s")
    
    if result.errors:
        print(f"Errors: {result.errors}")
    
    print(f"\nExecutive Summary: {result.executive_summary}")


if __name__ == "__main__":
    main()