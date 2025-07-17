import operator
import uuid
from enum import Enum
from typing import List, Dict, Optional, Any, Set
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
    artifact_id: Optional[str] = Field(None, description="The ID of a specific artifact from the evidence locker to be analyzed.")
    priority: int = Field(..., description="Priority of the task (1=Highest, 10=Lowest).")
    reason: str = Field(..., description="A clear, concise description of the investigative goal for this task.")
    context_data: Optional[str] = Field(None, description="Contextual data for tasks not related to a specific artifact (e.g., a keyword search).")

class NarrativeCoherence(BaseModel):
    score: float = Field(1.0, description="Incoherence score from 0.0 (coherent) to 1.0 (deceptive).")
    notes: List[str] = Field(default_factory=list, description="Observations that affect coherence.")

class AttackChainLink(BaseModel):
    source: str = Field(..., description="The identifier for the source of the action (e.g., 'Object 7', 'Artifact <id>').")
    action: str = Field(..., description="The relationship (e.g., 'Executes', 'References', 'DownloadsFrom').")
    target: str = Field(..., description="The identifier for the target of the action (e.g., 'Object 12', 'Operating System', a URL, or a filename).")
    description: str = Field(..., description="Human-readable summary of the link.")

class ExtractedArtifact(BaseModel):
    artifact_id: str = Field(default_factory=lambda: f"art_{uuid.uuid4().hex[:8]}", description="Unique identifier for this artifact.")
    source_object_id: int = Field(..., description="The PDF object from which this was extracted.")
    content_decoded: Optional[str] = Field(None, description="The decoded/deobfuscated content, if in memory.")
    file_path: Optional[str] = Field(None, description="The path to the file where this artifact is stored, if dumped to disk.")
    encoding: str = Field(..., description="A classification of the content's apparent encoding. If the data appears intentionally obscured, label its type. This classification dictates the next analytical step.")
    analysis_notes: List[str] = Field(default_factory=list, description="Notes from the analysis of this artifact.")

class IndicatorOfCompromise(BaseModel):
    value: str = Field(..., description="The value of the indicator (e.g., the URL).")
    source_object_id: int = Field(..., description="The PDF object where this IoC was discovered.")
    context: str = Field(..., description="The line or code snippet where the IoC was found.")

class EvidenceLocker(BaseModel):
    structural_summary: Dict[str, Any] = Field(default_factory=dict, description="Raw, parsed output from the initial triage tool (e.g., pdfid).")
    attack_chain: List[AttackChainLink] = Field(default_factory=list)
    extracted_artifacts: Dict[str, ExtractedArtifact] = Field(default_factory=dict)
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
    completed_task_ids: Annotated[Set[str], operator.ior] = Field(default_factory=set, description="A set of task IDs that have already been completed to prevent re-execution.")
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
    coherence_score: float = Field(..., description="Your initial assessment of the file's coherence from 0.0 (highly deceptive/incoherent) to 1.0 (perfectly coherent and benign).")


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
    extracted_artifacts_additions: Dict[str, ExtractedArtifact] = Field(default_factory=dict, description="A dictionary of new substantive data blocks (scripts, payloads, etc.) keyed by their new artifact_id.")
    new_indicators_of_compromise: List[IndicatorOfCompromise] = Field(default_factory=list, description="A list of new, concrete IoCs (URLs, domains, etc.) found in the output.")



class StrategicReview(BaseModel):
    """Schema for the strategic review of the investigation plan."""
    updated_queue: List[InvestigationTask] = Field(..., description="The investigation queue, updated to reflect the latest finding. This involves removing completed or now-irrelevant tasks, refining existing tasks, and adding new ones as needed.")
    updated_hypothesis: str = Field(..., description="Your updated working hypothesis, reflecting the new findings.")
    reasoning: str = Field(..., description="A brief summary of why you are changing the plan, describing the strategic shift. (e.g., 'Pruning redundant data-finding tasks now that the primary payload has been identified. Refining focus to post-exploitation analysis.')")
    updated_coherence_score: float = Field(..., description="The new coherence score, adjusted based on the latest finding.")