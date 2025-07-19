"""
PDF Hunter Main - Composed LangGraph Agent

This module contains the main composed graph that integrates:
1. PDF Processing (parallel extraction of images, URLs, hashes)
2. Static Analysis (forensic analysis of the PDF)

The composed graph uses subgraph integration following LangGraph patterns.
"""

from .pdf_hunter_graph import (
    app,
    create_pdf_hunter_graph,
    process_pdf_with_hunter,
    PDFHunterInput,
    PDFHunterOutput
)

__version__ = "0.1.0"

__all__ = [
    "app",
    "create_pdf_hunter_graph", 
    "process_pdf_with_hunter",
    "PDFHunterInput",
    "PDFHunterOutput"
] 