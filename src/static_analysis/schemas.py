import operator
import uuid
from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from typing_extensions import Annotated
from datetime import datetime

# --- 1. Pydantic State Models (Unchanged) ---
# The core state definition remains the same.

class Verdict(str, Enum):
    """The overall assessment of the file."""
    PRESUMED_INNOCENT = "Presumed_Innocent"
    SUSPICIOUS = "Suspicious"
    MALICIOUS = "Malicious"
    BENIGN = "Benign"

class AnalysisPhase(str, Enum):
    """The current phase of the investigation."""
    TRIAGE = "Triage"
    INTERROGATION = "Interrogation"
    REASSESSMENT = "Reassessment"
    FINALIZING = "Finalizing"

class InvestigationTask(BaseModel):
    task_id: str = Field(default_factory=lambda: f"task_{uuid.uuid4().hex[:8]}", description="Unique identifier for the task.")
    object_id: Optional[int] = Field(None, description="The PDF object number to investigate, if the task is object-specific.")
    priority: int = Field(..., description="Priority of the task (1=Highest, 10=Lowest).")
    reason: str = Field(..., description="A clear, concise description of the investigative goal for this task.")
    context_data: Optional[str] = Field(None, description="Contextual data required to execute the task, used when an object_id is not applicable.")

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


class ToolCallLog(BaseModel):
    """A structured log for a single tool execution."""
    tool_name: str
    arguments: Dict[str, Any]
    command_str: str
    stdout: str
    stderr: str
    return_code: int
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class ForensicCaseFile(BaseModel):
    file_path: str
    file_hash_sha256: Optional[str] = None
    analysis_session_id: str = Field(default_factory=lambda: str(uuid.uuid4()) + "_" + datetime.now().strftime("%Y%m%d_%H%M%S"))
    verdict: Verdict = Field(Verdict.PRESUMED_INNOCENT)
    phase: AnalysisPhase = Field(AnalysisPhase.TRIAGE)
    narrative_coherence: NarrativeCoherence = Field(default_factory=NarrativeCoherence)
    current_hypothesis: Optional[str] = Field(None, description="The current working theory of the primary threat vector.")
    last_finding: Optional[str] = Field(None, description="A summary of the most recent finding to inform the strategic review.")
    investigation_queue: List[InvestigationTask] = Field(default_factory=list)
    evidence: EvidenceLocker = Field(default_factory=EvidenceLocker)
    analysis_trail: Annotated[List[str], operator.add] = Field(default_factory=list)
    errors: Annotated[List[str], operator.add] = Field(default_factory=list)
    final_report: Optional[str] = None
    tool_log: Annotated[List[ToolCallLog], operator.add] = Field(default_factory=list, description="A detailed audit trail of all tool calls made.")
    interrogation_steps: int = Field(0, description="A counter to prevent infinite loops.")



# --- 2. LLM Interaction Schemas ---

class TriageAnalysis(BaseModel):
    """The required JSON structure for the LLM's triage analysis."""
    verdict: Verdict = Field(..., description="Your expert verdict on the file based on the triage data.")
    phase: AnalysisPhase = Field(..., description="The next analysis phase based on your verdict.")
    is_suspicious: bool = Field(..., description="A simple boolean flag indicating if the file warrants further investigation.")
    hypothesis: str = Field(..., description="A concise statement of your initial working hypothesis about the primary threat.")
    investigation_queue: List[InvestigationTask] = Field(..., description="A priority-ordered list of tasks for the next phase.")
    analysis_trail: str = Field(..., description="A single, concise log entry summarizing your findings and decision, written in your persona's voice.")
    narrative_coherence_notes: List[str] = Field(..., description="Notes on why the file's 'character' seems suspicious or benign.")


class ToolAndTaskSelection(BaseModel):
    """Schema for selecting the next task and the right tool."""
    chosen_task: InvestigationTask = Field(..., description="The single most logical task to execute right now from the provided list.")
    tool_name: str = Field(..., description="The single best tool to use from the provided manifest for the chosen task.")
    arguments: Dict[str, Any] = Field(..., description="A dictionary of arguments for the selected tool, matching its input schema.")
    reasoning: str = Field(..., description="A brief justification for your choice of task and tool.")


class InterrogationAnalysis(BaseModel):
    """Schema for interpreting tool output."""
    findings_summary: str = Field(..., description="A concise summary of what the tool output reveals.")
    new_tasks: List[InvestigationTask] = Field(..., description="A list of new, specific, high-priority follow-up tasks discovered during this analysis.")
    attack_chain_additions: List[AttackChainLink] = Field(..., description="Any new links to add to the attack chain map.")
    extracted_artifacts_additions: List[ExtractedArtifact] = Field(default_factory=list, description="A list of substantive data blocks (scripts, payloads, etc.) found in the output to be added to the evidence locker.")
    new_indicators_of_compromise: List[IndicatorOfCompromise] = Field(default_factory=list, description="A list of new, concrete IoCs (URLs, domains, etc.) found in the output.")



class StrategicReview(BaseModel):
    """Schema for the strategic review of the investigation plan."""
    reprioritized_queue: List[InvestigationTask] = Field(..., description="The original list of tasks, re-ordered by priority.")
    updated_hypothesis: str = Field(..., description="Your updated working hypothesis, reflecting the new findings.")
    reasoning: str = Field(..., description="A brief summary of why you are or are not changing the plan.")