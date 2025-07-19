"""
Static Analysis Module for PDF Forensic Analysis

This module provides LangGraph-based forensic analysis of PDF files with structured input/output schemas.
"""

from .graph import app, create_app, process_pdf_with_forensic_agent
from .schemas import (
    ForensicCaseFileInput, 
    ForensicCaseFileOutput, 
    ForensicCaseFile,
    Verdict,
    AnalysisPhase
)

__all__ = [
    "app",
    "create_app", 
    "process_pdf_with_forensic_agent",
    "ForensicCaseFileInput",
    "ForensicCaseFileOutput", 
    "ForensicCaseFile",
    "Verdict",
    "AnalysisPhase"
]
