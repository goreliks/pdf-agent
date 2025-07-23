"""
Schemas for the PDF Hunter Main Graph

This module defines the state schemas for the composed LangGraph that integrates
PDF processing and static analysis as subgraphs.
"""

import operator
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from typing_extensions import Annotated, TypedDict

# Import schemas from subgraphs
from pdf_processing.agent_schemas import PDFProcessingOutput, PDFHashData, ExtractedImage, ExtractedURL
from static_analysis.schemas import ForensicCaseFileOutput, Verdict, AnalysisPhase, IndicatorOfCompromise
from visual_analysis.schemas import VisualAnalysisOutput, DeceptionTactic, BenignSignal, PrioritizedURL


class PDFHunterInput(BaseModel):
    """
    Input model for the PDF Hunter Main Graph.
    
    This is the user-facing input schema for the composed graph.
    """
    pdf_path: str = Field(..., description="Path to the PDF file to analyze", min_length=1)
    pages_to_process: Optional[int] = Field(
        1, 
        description="Number of pages to process from the beginning (1-based). Default is 1 (first page only)",
        ge=1
    )
    output_directory: Optional[str] = Field(
        None, 
        description="Directory to save extracted images. If not provided, will create './extracted_images_<timestamp>'"
    )
    
    @field_validator('pdf_path')
    @classmethod
    def validate_pdf_path(cls, v: str) -> str:
        """Validate PDF path format."""
        v = v.strip()
        if not v:
            raise ValueError('PDF path cannot be empty')
        
        from pathlib import Path
        path_obj = Path(v)
        if path_obj.suffix.lower() != '.pdf':
            raise ValueError('File must have .pdf extension')
        
        return v


class PDFHunterState(TypedDict):
    """
    State for the PDF Hunter Main Graph.
    
    This state manages the flow between PDF processing and static analysis subgraphs.
    """
    # Input parameters
    pdf_path: str
    pages_to_process: Optional[int]
    output_directory: Optional[str]
    
    # Results from PDF processing subgraph
    pdf_processing_result: Optional[PDFProcessingOutput]
    
    # Results from static analysis subgraph  
    static_analysis_result: Optional[ForensicCaseFileOutput]
    
    # Results from visual analysis subgraph
    visual_analysis_result: Optional[VisualAnalysisOutput]
    
    # Error tracking
    errors: Annotated[List[str], operator.add]


class PDFHunterOutput(BaseModel):
    """
    Output model for the PDF Hunter Main Graph.
    
    This combines results from both PDF processing and static analysis.
    """
    success: bool = Field(..., description="Whether the overall analysis was successful")
    pdf_path: str = Field(..., description="Path to the analyzed PDF file")
    
    # PDF Processing Results
    pdf_hash: Optional[PDFHashData] = Field(None, description="Hash data for the PDF file")
    page_count: Optional[int] = Field(None, description="Total number of pages in the PDF")
    extracted_images: List[ExtractedImage] = Field(
        default_factory=list, 
        description="Images extracted from pages"
    )
    extracted_urls: List[ExtractedURL] = Field(
        default_factory=list, 
        description="URLs extracted from PDF"
    )
    
    # Static Analysis Results
    forensic_verdict: Optional[Verdict] = Field(None, description="Forensic analysis verdict")
    analysis_phase: Optional[AnalysisPhase] = Field(None, description="Final analysis phase")
    forensic_hypothesis: Optional[str] = Field(None, description="Working hypothesis about threats")
    narrative_coherence_score: Optional[float] = Field(None, description="Coherence score (0.0 = deceptive, 1.0 = coherent)")
    indicators_of_compromise: List[IndicatorOfCompromise] = Field(
        default_factory=list, 
        description="Indicators of compromise found"
    )
    attack_chain_length: Optional[int] = Field(None, description="Number of attack chain links")
    extracted_artifacts_count: Optional[int] = Field(None, description="Number of forensic artifacts extracted")
    forensic_session_id: Optional[str] = Field(None, description="Forensic analysis session ID")
    
    # Visual Analysis Results
    visual_verdict: Optional[str] = Field(None, description="Visual analysis overall verdict")
    visual_confidence: Optional[float] = Field(None, description="Visual analysis confidence score")
    visual_pages_analyzed: Optional[int] = Field(None, description="Number of pages visually analyzed")
    visual_executive_summary: Optional[str] = Field(None, description="Visual analysis executive summary")
    visual_deception_tactics_count: Optional[int] = Field(None, description="Number of deception tactics detected")
    visual_benign_signals_count: Optional[int] = Field(None, description="Number of benign signals detected")
    visual_high_priority_urls_count: Optional[int] = Field(None, description="Number of high priority URLs found")
    
    # Combined Processing Info
    total_processing_time: Optional[float] = Field(None, description="Total processing time for all analysis stages")
    pdf_processing_errors: List[str] = Field(default_factory=list, description="Errors from PDF processing")
    forensic_analysis_errors: List[str] = Field(default_factory=list, description="Errors from forensic analysis")
    visual_analysis_errors: List[str] = Field(default_factory=list, description="Errors from visual analysis")
    
    # Convenience properties for visual analysis access
    @property
    def visual_analysis_result(self) -> Optional[VisualAnalysisOutput]:
        """Get the complete visual analysis result."""
        # This will be set in the state and accessible through the final result
        return getattr(self, '_visual_analysis_result', None)
    
    # Summary methods
    def get_summary(self) -> Dict[str, Any]:
        """Get a comprehensive summary of all analysis results."""
        return {
            "success": self.success,
            "pdf_file": self.pdf_path,
            "processing_time": self.total_processing_time,
            
            # PDF Processing Summary
            "pdf_processing": {
                "page_count": self.page_count,
                "images_extracted": len(self.extracted_images),
                "urls_found": len(self.extracted_urls),
                "has_hash": self.pdf_hash is not None,
                "processing_errors": len(self.pdf_processing_errors)
            },
            
            # Forensic Analysis Summary  
            "forensic_analysis": {
                "verdict": self.forensic_verdict.value if self.forensic_verdict else None,
                "coherence_score": self.narrative_coherence_score,
                "iocs_found": len(self.indicators_of_compromise),
                "attack_chain_length": self.attack_chain_length or 0,
                "artifacts_extracted": self.extracted_artifacts_count or 0,
                "analysis_errors": len(self.forensic_analysis_errors)
            },
            
            # Visual Analysis Summary
            "visual_analysis": {
                "available": self.visual_analysis_result is not None,
                "verdict": self.visual_analysis_result.overall_verdict if self.visual_analysis_result else None,
                "confidence": self.visual_analysis_result.overall_confidence if self.visual_analysis_result else None,
                "pages_analyzed": self.visual_analysis_result.total_pages_analyzed if self.visual_analysis_result else 0,
                "deception_tactics": len(self.visual_analysis_result.all_deception_tactics) if self.visual_analysis_result else 0,
                "benign_signals": len(self.visual_analysis_result.all_benign_signals) if self.visual_analysis_result else 0,
                "high_priority_urls": len(self.visual_analysis_result.high_priority_urls) if self.visual_analysis_result else 0,
                "analysis_errors": len(self.visual_analysis_errors)
            }
        }
    
    def is_suspicious(self) -> bool:
        """Check if the PDF is considered suspicious based on forensic analysis."""
        if not self.forensic_verdict:
            return False
        return self.forensic_verdict in [Verdict.SUSPICIOUS, Verdict.MALICIOUS]
    
    def has_artifacts(self) -> bool:
        """Check if any forensic artifacts were found."""
        return (self.extracted_artifacts_count or 0) > 0 or len(self.indicators_of_compromise) > 0 