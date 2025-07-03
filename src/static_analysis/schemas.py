import operator
import uuid
import hashlib
import subprocess
from enum import Enum
from typing import List, Dict, Optional, Any, Union

from pydantic import BaseModel, Field
from typing_extensions import Annotated

from langgraph.graph import StateGraph, END

# --- 1. Pydantic State Models (Unchanged) ---
# The core state definition remains the same.

class Verdict(str, Enum):
    PRESUMED_INNOCENT = "Presumed_Innocent"
    SUSPICIOUS = "Suspicious"
    MALICIOUS = "Malicious"
    BENIGN = "Benign"

class AnalysisPhase(str, Enum):
    TRIAGE = "Triage"
    INTERROGATION = "Interrogation"
    FINALIZING = "Finalizing"

class InvestigationTask(BaseModel):
    object_id: int = Field(..., description="The PDF object number to investigate. Use 0 if unknown.")
    priority: int = Field(..., description="Priority of the task (1=Highest, 10=Lowest).")
    reason: str = Field(..., description="Why this object is being investigated (e.g., 'Contains /JS keyword').")

# ... (Other Pydantic models from the previous version remain unchanged) ...
class NarrativeCoherence(BaseModel):
    score: float = Field(1.0, description="Coherence score from 0.0 (deceptive) to 1.0 (coherent).")
    notes: List[str] = Field(default_factory=list, description="Observations that affect coherence.")

class AttackChainLink(BaseModel):
    source_object: int = Field(..., description="The PDF object that initiates the action.")
    action: str = Field(..., description="The relationship (e.g., 'Executes', 'References', 'Decodes').")
    target_object: int = Field(..., description="The PDF object that is the target of the action.")
    description: str = Field(..., description="Human-readable summary of the link.")

class ExtractedArtifact(BaseModel):
    source_object_id: int = Field(..., description="The PDF object from which this was extracted.")
    content_decoded: str = Field(..., description="The decoded/deobfuscated content.")
    analysis_notes: List[str] = Field(default_factory=list, description="Notes from the analysis of this artifact.")

class IndicatorOfCompromise(BaseModel):
    value: str = Field(..., description="The value of the indicator (e.g., the URL).")
    source_object_id: int = Field(..., description="The PDF object where this IoC was discovered.")
    context: str = Field(..., description="The line or code snippet where the IoC was found.")

class EvidenceLocker(BaseModel):
    structural_summary: Dict[str, Any] = Field(default_factory=dict, description="Raw, parsed output from the initial triage tool (e.g., pdfid).")
    attack_chain: List[AttackChainLink] = Field(default_factory=list)
    extracted_artifacts: Dict[int, ExtractedArtifact] = Field(default_factory=dict)
    indicators_of_compromise: List[IndicatorOfCompromise] = Field(default_factory=list)

class ForensicCaseFileInput(BaseModel):
    file_path: str = Field(..., description="The local path to the PDF file to be analyzed.")

class ForensicCaseFile(BaseModel):
    file_path: str
    file_hash_sha256: Optional[str] = None
    analysis_session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verdict: Verdict = Field(Verdict.PRESUMED_INNOCENT)
    phase: AnalysisPhase = Field(AnalysisPhase.TRIAGE)
    narrative_coherence: NarrativeCoherence = Field(default_factory=NarrativeCoherence)
    current_hypothesis: Optional[str] = Field(None, description="The current working theory of the primary threat vector.")
    investigation_queue: List[InvestigationTask] = Field(default_factory=list)
    evidence: EvidenceLocker = Field(default_factory=EvidenceLocker)
    analysis_trail: Annotated[List[str], operator.add] = Field(default_factory=list)
    errors: Annotated[List[str], operator.add] = Field(default_factory=list)
    final_report: Optional[str] = None


# --- 2. LLM Interaction Setup ---

class TriageAnalysis(BaseModel):
    """The required JSON structure for the LLM's triage analysis."""
    verdict: Verdict = Field(..., description="Your expert verdict on the file based on the triage data.")
    phase: AnalysisPhase = Field(..., description="The next analysis phase based on your verdict.")
    is_suspicious: bool = Field(..., description="A simple boolean flag indicating if the file warrants further investigation.")
    hypothesis: str = Field(..., description="A concise statement of your initial working hypothesis about the primary threat.")
    investigation_queue: List[InvestigationTask] = Field(..., description="A priority-ordered list of tasks for the next phase.")
    analysis_trail: str = Field(..., description="A single, concise log entry summarizing your findings and decision, written in your persona's voice.")
    narrative_coherence_notes: List[str] = Field(..., description="Notes on why the file's 'character' seems suspicious or benign.")