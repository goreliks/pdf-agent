"""
Utility functions for Visual Analysis LangGraph Agent

This module provides helper functions for the visual analysis workflow,
including LLM chain creation, image processing, and cross-modal analysis
between visual evidence and technical data.
"""

import json
import base64
from typing import Optional, Dict, Any, List
from io import BytesIO

from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.messages import HumanMessage

# Import schemas
from visual_analysis.schemas import (
    VisualAnalysisResults, ElementMap, DeceptionTactic, BenignSignal,
    DetailedFinding, PrioritizedURL
)
from pdf_processing.agent_schemas import ExtractedImage


def create_llm_chain(system_prompt: str, human_prompt: str, response_model: BaseModel, llm):
    """
    Helper function to create a structured LLM chain using PydanticOutputParser.
    
    This follows the same pattern as static_analysis.utils.create_llm_chain
    to maintain consistency across the codebase.
    """
    # Create the parser
    parser = PydanticOutputParser(pydantic_object=response_model)
    
    # Add format instructions to the human prompt
    enhanced_human_prompt = human_prompt + "\n\n{format_instructions}"
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(enhanced_human_prompt)
    ])
    
    # Partially fill the format instructions
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    
    # Create chain: prompt -> llm -> parser
    return prompt | llm | parser


def prepare_image_for_analysis(image: ExtractedImage) -> Optional[str]:
    """
    Prepare an extracted image for visual analysis.
    
    Args:
        image: ExtractedImage object with base64 data
        
    Returns:
        Base64 image data formatted for LLM analysis, or None if invalid
    """
    try:
        # Handle both dict and object formats
        base64_data = image["base64_data"] if isinstance(image, dict) else image.base64_data
        page_number = image["page_number"] if isinstance(image, dict) else image.page_number
        format_type = image["format"] if isinstance(image, dict) else image.format
        
        # Validate that we have base64 data
        if not base64_data:
            print(f"[!] No base64 data available for image on page {page_number}")
            return None
        
        # Ensure base64 data is properly formatted
        base64_data = base64_data.strip()
        
        # Add data URL prefix if not present (for LLM compatibility)
        if not base64_data.startswith('data:image/'):
            # Determine MIME type from format
            mime_type = f"image/{format_type.lower()}"
            if format_type.upper() == 'JPG':
                mime_type = "image/jpeg"
            base64_data = f"data:{mime_type};base64,{base64_data}"
        
        return base64_data
        
    except Exception as e:
        print(f"[!] Error preparing image for analysis: {str(e)}")
        return None


def create_element_map_json(element_map: Optional[ElementMap]) -> str:
    """
    Create a JSON representation of the element map for VDA analysis.
    
    Args:
        element_map: ElementMap with interactive elements data
        
    Returns:
        JSON string representation of the element map
    """
    if not element_map:
        return json.dumps({
            "page_number": 0,
            "interactive_elements": [],
            "note": "No interactive elements detected on this page"
        }, indent=2)
    
    # Convert to dictionary and ensure JSON serializable
    element_data = {
        "page_number": element_map.page_number,
        "interactive_elements": []
    }
    
    for element in element_map.interactive_elements:
        element_dict = {
            "type": element.get("type", "unknown"),
            "url": element.get("url", ""),
            "coordinates": element.get("coordinates"),
            "is_external": element.get("is_external", None)
        }
        element_data["interactive_elements"].append(element_dict)
    
    return json.dumps(element_data, indent=2)


def analyze_page_image(image: ExtractedImage, element_map: Optional[ElementMap], llm) -> VisualAnalysisResults:
    """
    Perform visual deception analysis on a single page image.
    
    Args:
        image: ExtractedImage with base64 image data
        element_map: ElementMap with technical data for cross-modal analysis
        llm: Language model instance for analysis
        
    Returns:
        VisualAnalysisResults with comprehensive analysis
    """
    try:
        # Prepare image for analysis
        image_data = prepare_image_for_analysis(image)
        # Handle both dict and object formats for error reporting
        page_number = image["page_number"] if isinstance(image, dict) else image.page_number
        if not image_data:
            return create_error_analysis(f"Failed to prepare image for page {page_number}")
        
        # Create element map JSON
        element_map_json = create_element_map_json(element_map)
        
        # Import the system prompt
        from visual_analysis.prompts import SYSTEM_PROMPT
        
        # Create the human prompt for this specific analysis
        human_prompt = """
        I need you to analyze this PDF page for visual deception tactics.

        **Visual Evidence:** Please examine the attached image of the PDF page.

        **Technical Blueprint (Element Map):**
        {element_map_json}

        Please perform your rigorous two-sided cross-examination as outlined in your instructions:

        **Part A: Hunting for Incoherence (Signs of Deception)**
        - Look for identity & brand impersonation
        - Identify psychological manipulation tactics
        - Check for interactive element deception
        - Assess structural deception patterns

        **Part B: Searching for Coherence (Signs of Legitimacy)**
        - Evaluate holistic consistency & professionalism
        - Assess visual-technical coherence
        - Look for transparency and good faith indicators

        Provide your analysis in the structured JSON format as specified in your instructions.
        """
        
        # Create LLM chain for structured output
        chain = create_llm_chain(SYSTEM_PROMPT, human_prompt, VisualAnalysisResults, llm)
        
        # Create message with image
        messages = [
            HumanMessage(
                content=[
                    {
                        "type": "text",
                        "text": human_prompt.format(element_map_json=element_map_json)
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data}
                    }
                ]
            )
        ]
        
        # Invoke the chain with the image and element map data
        try:
            result = chain.invoke({
                "element_map_json": element_map_json
            })
            
            # Validate the result is a VisualAnalysisResults instance
            if isinstance(result, VisualAnalysisResults):
                print(f"[*] Successfully analyzed page {page_number}: {result.visual_verdict}")
                return result
            else:
                print(f"[!] Unexpected result type: {type(result)}")
                return create_error_analysis(f"Unexpected analysis result format for page {page_number}")
                
        except Exception as chain_error:
            print(f"[!] LLM chain execution failed: {str(chain_error)}")
            return create_error_analysis(f"LLM analysis failed for page {page_number}: {str(chain_error)}")
        
    except Exception as e:
        print(f"[!] Error during page analysis: {str(e)}")
        return create_error_analysis(f"Analysis error for page {page_number}: {str(e)}")


def create_error_analysis(error_message: str) -> VisualAnalysisResults:
    """
    Create a minimal VisualAnalysisResults for error cases.
    
    Args:
        error_message: Description of the error
        
    Returns:
        VisualAnalysisResults with error information
    """
    return VisualAnalysisResults(
        visual_verdict="Suspicious",  # Default to suspicious on errors
        confidence_score=0.0,
        summary=f"Analysis failed: {error_message}",
        deception_tactics=[
            DeceptionTactic(
                tactic_type="Analysis Error",
                description=error_message,
                confidence=1.0,
                evidence=["Analysis could not be completed"]
            )
        ],
        benign_signals=[],
        detailed_findings=[],
        prioritized_urls=[]
    )


def validate_base64_image(base64_data: str) -> bool:
    """
    Validate that base64 data represents a valid image.
    
    Args:
        base64_data: Base64 encoded image data
        
    Returns:
        True if valid image data, False otherwise
    """
    try:
        # Remove data URL prefix if present
        if base64_data.startswith('data:'):
            base64_data = base64_data.split(',')[1]
        
        # Decode base64 data
        image_bytes = base64.b64decode(base64_data)
        
        # Check for common image headers
        # PNG signature
        if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return True
        
        # JPEG signature
        if image_bytes.startswith(b'\xff\xd8\xff'):
            return True
        
        # GIF signature
        if image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            return True
        
        # Basic validation passed - might be other image format
        return len(image_bytes) > 100  # Minimum reasonable image size
        
    except Exception:
        return False


def extract_urls_from_findings(detailed_findings: List[DetailedFinding]) -> List[str]:
    """
    Extract URLs from detailed findings for further analysis.
    
    Args:
        detailed_findings: List of detailed findings from analysis
        
    Returns:
        List of unique URLs found in the findings
    """
    urls = set()
    
    for finding in detailed_findings:
        if finding.technical_data and isinstance(finding.technical_data, dict):
            # Look for URL in technical data
            if 'url' in finding.technical_data:
                url = finding.technical_data['url']
                if url and isinstance(url, str):
                    urls.add(url.strip())
    
    return list(urls)


def calculate_overall_confidence(page_analyses: List[VisualAnalysisResults]) -> float:
    """
    Calculate overall confidence score from multiple page analyses.
    
    Args:
        page_analyses: List of analysis results for each page
        
    Returns:
        Overall confidence score (0.0-1.0)
    """
    if not page_analyses:
        return 0.0
    
    # Calculate weighted average based on verdict severity
    total_weight = 0
    weighted_confidence = 0
    
    for analysis in page_analyses:
        # Weight based on verdict (more suspicious verdicts get higher weight in average)
        if analysis.visual_verdict == "Highly Deceptive":
            weight = 3.0
        elif analysis.visual_verdict == "Suspicious":
            weight = 2.0
        else:  # Benign
            weight = 1.0
        
        weighted_confidence += analysis.confidence_score * weight
        total_weight += weight
    
    return weighted_confidence / total_weight if total_weight > 0 else 0.0


def aggregate_deception_tactics(page_analyses: List[VisualAnalysisResults]) -> List[DeceptionTactic]:
    """
    Aggregate and deduplicate deception tactics from multiple pages.
    
    Args:
        page_analyses: List of analysis results for each page
        
    Returns:
        Deduplicated list of deception tactics
    """
    all_tactics = []
    seen_tactics = set()
    
    for analysis in page_analyses:
        for tactic in analysis.deception_tactics:
            # Create a key for deduplication
            tactic_key = (tactic.tactic_type, tactic.description)
            
            if tactic_key not in seen_tactics:
                seen_tactics.add(tactic_key)
                all_tactics.append(tactic)
    
    # Sort by confidence (highest first)
    all_tactics.sort(key=lambda t: t.confidence, reverse=True)
    
    return all_tactics


def aggregate_benign_signals(page_analyses: List[VisualAnalysisResults]) -> List[BenignSignal]:
    """
    Aggregate and deduplicate benign signals from multiple pages.
    
    Args:
        page_analyses: List of analysis results for each page
        
    Returns:
        Deduplicated list of benign signals
    """
    all_signals = []
    seen_signals = set()
    
    for analysis in page_analyses:
        for signal in analysis.benign_signals:
            # Create a key for deduplication
            signal_key = (signal.signal_type, signal.description)
            
            if signal_key not in seen_signals:
                seen_signals.add(signal_key)
                all_signals.append(signal)
    
    # Sort by confidence (highest first)
    all_signals.sort(key=lambda s: s.confidence, reverse=True)
    
    return all_signals