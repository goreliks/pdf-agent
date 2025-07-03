from typing import Dict, Any
from static_analysis.schemas import ForensicCaseFile, InvestigationTask, Verdict, AnalysisPhase, ForensicCaseFileInput
from static_analysis.utils import get_file_hash, run_pdfid_simulation
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from static_analysis.prompts import TRIAGE_PROMPT_TEMPLATE
from static_analysis.schemas import TriageAnalysis
from static_analysis.test_run import run_pdfid


def triage_node_llm(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    This node uses an LLM to perform triage instead of manual rules.
    """
    file_path = state.file_path
    print("\n--- Running LLM-Powered Triage Node ---")

    # 1. Perform initial actions
    file_hash = get_file_hash(file_path)
    pdfid_output = run_pdfid(file_path)

    # 2. Set up the LLM chain
    # NOTE: To run for real, you need an OPENAI_API_KEY in your environment
    # and to install langchain-openai (`pip install langchain-openai`)
    prompt = ChatPromptTemplate.from_template(TRIAGE_PROMPT_TEMPLATE)
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(TriageAnalysis)
    chain = prompt | structured_llm

    # 3. Invoke the LLM
    print("[*] Asking LLM (Dr. Reed) for analysis...")
    llm_response = chain.invoke({"pdfid_output": pdfid_output}) # <-- REAL LLM CALL

    # --- MOCKED LLM CALL FOR RUNNABLE EXAMPLE ---
    # mock_response_json = {
    #     "verdict": "Suspicious",
    #     "phase": "Interrogation",
    #     "is_suspicious": True,
    #     "investigation_queue": [
    #         {"object_id": 0, "priority": 1, "reason": "Contains /JS and /JavaScript keywords, indicating active content."},
    #         {"object_id": 0, "priority": 2, "reason": "Contains /OpenAction and /AA keywords, suggesting automatic execution."},
    #         {"object_id": 0, "priority": 3, "reason": "Contains /Launch keyword, a highly suspicious capability."}
    #     ],
    #     "analysis_trail": "Initial scan reveals high-potential for action via JavaScript and auto-execution triggers. The file's character is suspect. Suspending innocence and proceeding to interrogation.",
    #     "narrative_coherence_notes": ["File contains multiple high-risk keywords (/JS, /OpenAction, /Launch) that are incoherent with a simple document's purpose."]
    # }
    # llm_response = TriageAnalysis(**mock_response_json)
    # --- END MOCK ---

    print(f"[*] LLM analysis received. Verdict: {llm_response.verdict}")

    # 4. Prepare state updates from the LLM's structured response
    updates = {
        "file_hash_sha256": file_hash,
        "analysis_trail": [
            f"Triage started for {file_path} (SHA256: {file_hash[:12]}...).",
            llm_response.analysis_trail # Append the LLM's own log entry
        ],
        "verdict": llm_response.verdict,
        "phase": llm_response.phase,
        "current_hypothesis": llm_response.hypothesis,
    }

    if llm_response.is_suspicious:
        updates["investigation_queue"] = llm_response.investigation_queue
    
    # Update nested models correctly
    updated_evidence = state.evidence.model_copy(deep=True)
    updated_evidence.structural_summary = {
        line.split()[0]: int(line.split()[1])
        for line in pdfid_output.strip().split('\n')
        if line.split() and line.split()[0].startswith('/') and line.split()[1].isdigit()
    }

    updated_coherence = state.narrative_coherence.model_copy(deep=True)
    if llm_response.is_suspicious:
        updated_coherence.score = 0.5 # Lower score for suspicious files
        updated_coherence.notes.extend(llm_response.narrative_coherence_notes)
    
    updates["evidence"] = updated_evidence
    updates["narrative_coherence"] = updated_coherence
    
    return updates

# --- 5. Graph Definition and Execution ---

def create_app():
    """Create and return the compiled LangGraph application."""
    workflow = StateGraph(ForensicCaseFile)
    workflow.add_node("triage", triage_node_llm)
    workflow.set_entry_point("triage")
    workflow.add_edge("triage", END)
    return workflow.compile()

# Create the app instance for LangGraph CLI
app = create_app()

def main():
    """Main function for running the forensic analysis."""
    print("--- Setting up Forensic Analysis Graph ---")
    
    pdf_to_analyze = "tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    inputs = ForensicCaseFileInput(file_path=pdf_to_analyze)
    
    final_state_dict = app.invoke(inputs.model_dump())
    final_state = ForensicCaseFile(**final_state_dict)

    print("\n\n--- Final Graph State ---")
    print(final_state.model_dump_json(indent=2))

if __name__ == "__main__":
    main()