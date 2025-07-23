"""
Schemas for the Visual Analysis LangGraph Agent

This module defines the state schemas and data models for the LangGraph agent
that performs visual deception analysis on PDF page images using cross-modal
analysis with technical data from PDF processing.

The Visual Deception Analyst (VDA) combines visual analysis of rendered PDF pages
with technical data about URLs and interactive elements to identify potential
deception tactics and social engineering attempts.
"""

import operator
from typing import List, Dict, Optional, Literal, Any
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated, TypedDict

# Import schemas from pdf_processing for type consistency
from pdf_processing.agent_schemas import ExtractedImage, ExtractedURL


class VisualAnalysisInput(BaseModel):
    """
    Input model for the Visual Analysis Agent.
    
    This model defines the minimal interface for visual analysis, accepting
    either images and URLs directly, or a PDF path for processing.
    """
    # Option 1: Direct visual analysis inputs (preferred for independent usage)
    extracted_images: Optional[List[ExtractedImage]] = Field(
        None, 
        description="List of extracted images with base64 data and metadata"
    )
    extracted_urls: Optional[List[ExtractedURL]] = Field(
        None,
        description="List of extracted URLs with coordinates and metadata"
    )
    
    # Option 2: PDF processing inputs (for full pipeline integration)
    pdf_path: Optional[str] = Field(
        None,
        description="Path to PDF file (if visual analysis should extract images/URLs first)"
    )
    pages_to_process: Optional[int] = Field(
        1,
        description="Number of pages to process from the beginning (1-based)",
        ge=1
    )
    output_directory: Optional[str] = Field(
        None,
        description="Directory to save analysis results"
    )
    
    @field_validator('pdf_path')
    @classmethod
    def validate_pdf_path(cls, v: Optional[str]) -> Optional[str]:
        """Validate PDF path format if provided."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError('PDF path cannot be empty')
            path_obj = Path(v)
            if path_obj.suffix.lower() != '.pdf':
                raise ValueError('File must have .pdf extension')
        return v
    
    def model_post_init(self, __context: Any) -> None:
        """Validate that either direct inputs or PDF path is provided."""
        has_direct_inputs = (self.extracted_images is not None and 
                           len(self.extracted_images) > 0) or (
                           self.extracted_urls is not None and 
                           len(self.extracted_urls) > 0)
        has_pdf_path = self.pdf_path is not None
        
        if not has_direct_inputs and not has_pdf_path:
            raise ValueError(
                "Must provide either direct inputs (extracted_images/extracted_urls) "
                "or pdf_path for processing"
            )


class DeceptionTactic(BaseModel):
    """Information about a detected deception tactic."""
    tactic_type: str = Field(..., description="Type of deception tactic identified")
    description: str = Field(..., description="Detailed description of the tactic")
    confidence: float = Field(..., description="Confidence in detection (0.0-1.0)", ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list, description="Supporting evidence for this tactic")


class BenignSignal(BaseModel):
    """Information about a detected benign/legitimate signal."""
    signal_type: str = Field(..., description="Type of benign signal identified")
    description: str = Field(..., description="Detailed description of the signal")
    confidence: float = Field(..., description="Confidence in assessment (0.0-1.0)", ge=0.0, le=1.0)


class DetailedFinding(BaseModel):
    """A specific finding from visual-technical cross-examination."""
    element_type: str = Field(..., description="Type of element (link, button, logo, etc.)")
    page_number: int = Field(..., description="Page number where finding was observed", ge=0)
    visual_description: str = Field(..., description="Description of visual appearance")
    technical_data: Optional[Dict[str, Any]] = Field(None, description="Related technical data (URL, coordinates, etc.)")
    assessment: str = Field(..., description="Assessment of this finding")
    significance: Literal["low", "medium", "high"] = Field(..., description="Significance level of this finding")


class PrioritizedURL(BaseModel):
    """URL marked for deeper analysis by downstream agents."""
    url: str = Field(..., description="URL requiring analysis")
    priority: int = Field(..., description="Priority level (1=highest)", ge=1, le=10)
    reason: str = Field(..., description="Reason for high priority assessment")
    page_number: int = Field(..., description="Page number where URL was found", ge=0)


class VisualAnalysisResults(BaseModel):
    """Comprehensive results from visual deception analysis."""
    # Overall Assessment
    visual_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"] = Field(
        ..., description="Final visual trustworthiness judgment"
    )
    confidence_score: float = Field(
        ..., description="Confidence in verdict (0.0-1.0)", ge=0.0, le=1.0
    )
    summary: str = Field(
        ..., description="Concise summary explaining conclusion and evidence weighting"
    )
    
    # Detected Patterns
    deception_tactics: List[DeceptionTactic] = Field(
        default_factory=list, description="Identified deception techniques"
    )
    benign_signals: List[BenignSignal] = Field(
        default_factory=list, description="Identified legitimacy indicators"
    )
    
    # Detailed Analysis
    detailed_findings: List[DetailedFinding] = Field(
        default_factory=list, description="Specific cross-modal analysis findings"
    )
    
    # Strategic Output
    prioritized_urls: List[PrioritizedURL] = Field(
        default_factory=list, description="URLs requiring deeper analysis"
    )


class ElementMap(BaseModel):
    """Structured representation of interactive elements for VDA analysis."""
    page_number: int = Field(..., description="Page number", ge=0)
    interactive_elements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of interactive elements with bounding boxes, text, and URLs"
    )
    
    @classmethod
    def from_extracted_data(cls, extracted_urls: List[ExtractedURL], page_number: int) -> "ElementMap":
        """Create ElementMap from extracted URL data for a specific page."""
        # Handle both dict and object formats (defensive programming)
        page_urls = []
        for url in extracted_urls:
            url_page_num = url["page_number"] if isinstance(url, dict) else url.page_number
            if url_page_num == page_number:
                page_urls.append(url)
        
        elements = []
        for url_data in page_urls:
            # Handle both dict and object formats
            element = {
                "type": url_data["url_type"] if isinstance(url_data, dict) else url_data.url_type,
                "url": url_data["url"] if isinstance(url_data, dict) else url_data.url,
                "coordinates": url_data["coordinates"] if isinstance(url_data, dict) else url_data.coordinates,
                "is_external": url_data["is_external"] if isinstance(url_data, dict) else url_data.is_external
            }
            elements.append(element)
        
        return cls(page_number=page_number, interactive_elements=elements)


class VisualAnalysisState(TypedDict):
    """
    State for the Visual Analysis LangGraph Agent.
    
    This state manages the visual deception analysis process including:
    - Image preparation and validation
    - Cross-modal analysis with technical data
    - Results aggregation and reporting
    """
    
    # Input parameters (from VisualAnalysisInput)
    extracted_images: List[ExtractedImage]  # Images to analyze
    extracted_urls: List[ExtractedURL]  # URL data for cross-modal analysis
    pdf_path: Optional[str]  # Original PDF path if available
    output_directory: Optional[str]  # Output directory for results
    
    # Processing state
    current_page: Optional[int]  # Current page being processed
    total_pages: int  # Total number of pages to process
    element_maps: List[ElementMap]  # Structured element data for each page
    
    # Analysis results (aggregated across pages)
    page_analyses: List[VisualAnalysisResults]  # Results for each analyzed page
    
    # Final output (from aggregation node)
    final_output: Optional['VisualAnalysisOutput']  # Complete analysis results for subgraph return
    
    # Error tracking
    errors: Annotated[List[str], operator.add]  # List of errors encountered during processing


class VisualAnalysisOutput(BaseModel):
    """
    Output model for the Visual Analysis Agent.
    
    This model provides a clean, user-facing output format with comprehensive
    visual deception analysis results across all processed pages.
    """
    success: bool = Field(..., description="Whether the overall analysis was successful")
    pdf_path: Optional[str] = Field(None, description="Path to the analyzed PDF file")
    total_pages_analyzed: int = Field(..., description="Number of pages analyzed", ge=0)
    
    # Aggregated Results
    overall_verdict: Literal["Benign", "Suspicious", "Highly Deceptive"] = Field(
        ..., description="Overall verdict across all pages"
    )
    overall_confidence: float = Field(
        ..., description="Overall confidence score (0.0-1.0)", ge=0.0, le=1.0
    )
    executive_summary: str = Field(
        ..., description="Executive summary of visual analysis findings"
    )
    
    # Per-page Analysis
    page_analyses: List[VisualAnalysisResults] = Field(
        default_factory=list, description="Detailed analysis results for each page"
    )
    
    # Aggregated Findings
    all_deception_tactics: List[DeceptionTactic] = Field(
        default_factory=list, description="All deception tactics found across pages"
    )
    all_benign_signals: List[BenignSignal] = Field(
        default_factory=list, description="All benign signals found across pages"
    )
    high_priority_urls: List[PrioritizedURL] = Field(
        default_factory=list, description="URLs requiring immediate attention"
    )
    
    # Processing metadata
    total_processing_time: Optional[float] = Field(
        None, description="Total time taken for analysis", ge=0.0
    )
    errors: List[str] = Field(
        default_factory=list, description="List of errors encountered during processing"
    )
    
    @field_validator('pdf_path')
    @classmethod
    def validate_pdf_path(cls, v: Optional[str]) -> Optional[str]:
        """Ensure PDF path is not empty if provided."""
        if v is not None and not v.strip():
            raise ValueError('PDF path cannot be empty')
        return v.strip() if v else None
    
    def get_analysis_summary(self) -> Dict[str, Any]:
        """Get a summary of analysis results."""
        return {
            "success": self.success,
            "overall_verdict": self.overall_verdict,
            "overall_confidence": self.overall_confidence,
            "pages_analyzed": self.total_pages_analyzed,
            "deception_tactics_found": len(self.all_deception_tactics),
            "benign_signals_found": len(self.all_benign_signals),
            "high_priority_urls": len(self.high_priority_urls),
            "processing_time": self.total_processing_time,
            "errors_count": len(self.errors)
        }
    
    def to_json_summary(self) -> str:
        """Get a JSON summary of key metrics."""
        import json
        return json.dumps(self.get_analysis_summary(), indent=2)