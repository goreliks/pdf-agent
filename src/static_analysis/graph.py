import json
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# Import our schemas, prompts, and utils
from static_analysis.schemas import (
    ForensicCaseFile, InvestigationTask, ForensicCaseFileInput, ForensicCaseFileOutput, TriageAnalysis,
    ToolAndTaskSelection, InterrogationAnalysis, AttackChainLink, StrategicReview, Verdict, AnalysisPhase
)
from static_analysis.prompts import (
    SYSTEM_PROMPT, TRIAGE_HUMAN_PROMPT, TECHNICIAN_HUMAN_PROMPT,
    ANALYST_HUMAN_PROMPT, STRATEGIC_REVIEW_HUMAN_PROMPT, TOOL_MANIFEST
)
from static_analysis.utils import create_llm_chain, run_pdfid, run_pdf_parser_full_statistical_analysis, ToolExecutor


# --- TOOL EXECUTOR INSTANTIATED ---
# Create a single, reusable instance of our tool executor
tool_executor = ToolExecutor(manifest=TOOL_MANIFEST)

# --- CONFIGURATION ---
MAX_INTERROGATION_STEPS = 12 # Circuit breaker for infinite loops



def triage_node(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    Runs the initial pdfid scan and performs triage to form a
    starting hypothesis and investigation plan.
    """
    print("\n--- Running Triage Node ---")
    pdfid_output = run_pdfid(state.file_path)
    stats_output = run_pdf_parser_full_statistical_analysis(state.file_path)
    triage_context = f"--- PDFID ANALYSIS ---\n{pdfid_output}\n\n--- STATISTICAL ANALYSIS ---\n{stats_output}"
    print(f"[*] Combined Triage Output:\n{triage_context}")
    chain = create_llm_chain(SYSTEM_PROMPT, TRIAGE_HUMAN_PROMPT, TriageAnalysis)

    print("[*] Dr. Reed is performing initial triage...")
    llm_response = chain.invoke({"triage_context": triage_context})

    # Create an initial EvidenceLocker
    initial_evidence = {
        "structural_summary": {"pdfid": pdfid_output, "pstats": stats_output}
    }

    initial_narrative = {
        "notes": llm_response.narrative_coherence_notes,
        "score": llm_response.coherence_score
    }
    
    return {
        "verdict": llm_response.verdict,
        "phase": llm_response.phase,
        "current_hypothesis": llm_response.hypothesis,
        "investigation_queue": llm_response.investigation_queue,
        "analysis_trail": [llm_response.analysis_trail],
        "evidence": initial_evidence,
        "narrative_coherence": initial_narrative,
    }


def interrogation_node(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    Selects and executes a single forensic tool, then analyzes the output
    to extract evidence and create new tasks.
    """
    print("\n--- Running Interrogation Node ---")
    # Increment the loop counter first
    current_steps = state.interrogation_steps + 1
    
    if not state.investigation_queue:
        return {"errors": ["Interrogation node called with an empty queue."], "interrogation_steps": current_steps}
    
    # Provide the agent with a lookahead of the next few tasks
    task_lookahead = state.investigation_queue[:5]
    
    print("[*] Dr. Reed is in instrumental mode (selecting task and tool)...")
    technician_chain = create_llm_chain(SYSTEM_PROMPT, TECHNICIAN_HUMAN_PROMPT, ToolAndTaskSelection)
    
    # This invoke call is now correct and includes the evidence_locker
    tool_selection = technician_chain.invoke({
        "hypothesis": state.current_hypothesis,
        "file_path": state.file_path,
        "task_lookahead": json.dumps([t.model_dump() for t in task_lookahead]),
        "tool_manifest": json.dumps(TOOL_MANIFEST),
        "evidence_locker": state.evidence.model_dump_json()
    })
    
    print(f"[*] Dr. Reed chose task: '{tool_selection.chosen_task.reason}'")
    
    # Use the tool executor to run the command safely
    tool_log_entry = tool_executor.run(tool_selection.tool_name, tool_selection.arguments)
    
    print(f"[*] Tool Command Executed: {tool_log_entry.command_str}")
    print(f"[*] Tool Output:\nSTDOUT: {tool_log_entry.stdout}\nSTDERR: {tool_log_entry.stderr}")

    print("[*] Dr. Reed is in analytical mode (interpreting tool output)...")
    analyst_chain = create_llm_chain(SYSTEM_PROMPT, ANALYST_HUMAN_PROMPT, InterrogationAnalysis)
    
    analysis = analyst_chain.invoke({
        "hypothesis": state.current_hypothesis,
        "task_reason": tool_selection.chosen_task.reason,
        "tool_log_entry": tool_log_entry.model_dump_json(),
        "initial_report": json.dumps(state.evidence.structural_summary),
        "tool_manifest": json.dumps(TOOL_MANIFEST)
    })
    
    # Remove the completed task from the queue and add any new ones
    remaining_tasks = [t for t in state.investigation_queue if t.task_id != tool_selection.chosen_task.task_id]
    new_queue = analysis.new_tasks + remaining_tasks
    
    # --- Process and Catalog New Evidence ---
    # Create a deep copy of the evidence to safely modify it
    updated_evidence = state.evidence.model_copy(deep=True)
    
    # Add any new attack chain links
    updated_evidence.attack_chain.extend(analysis.attack_chain_additions)
    
    # Add any new Indicators of Compromise
    updated_evidence.indicators_of_compromise.extend(analysis.new_indicators_of_compromise)
    
    # The analyst now returns a dictionary of artifacts keyed by their new artifact_id.
    # We iterate through this dictionary to add them to the evidence locker.
    if analysis.extracted_artifacts_additions:
        for artifact_id, artifact in analysis.extracted_artifacts_additions.items():
            # Ensure the artifact's ID from the dictionary key is stored in the object itself
            artifact.artifact_id = artifact_id
            # Use the unique artifact_id as the key in the evidence locker
            updated_evidence.extracted_artifacts[artifact_id] = artifact
    # --- End of Evidence Processing ---
    
    # Prepare the final state update
    updates = {
        "investigation_queue": new_queue,
        "last_finding": analysis.findings_summary,
        "analysis_trail": [f"Interrogated '{tool_selection.chosen_task.reason}'. Finding: {analysis.findings_summary}"],
        "evidence": updated_evidence,  # Use the fully updated evidence object
        "tool_log": [tool_log_entry],
        "interrogation_steps": current_steps,
        "completed_task_ids": {tool_selection.chosen_task.task_id},
    }
    
    return updates


def strategic_review_node(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    Performs the high-level strategic review of the investigation plan.
    """
    print("\n--- Running Strategic Review Node ---")
    
    # If there's no new finding, there's nothing to review.
    if not state.last_finding:
        return {}

    print("[*] Dr. Reed is reviewing the overall strategy...")
    review_chain = create_llm_chain(SYSTEM_PROMPT, STRATEGIC_REVIEW_HUMAN_PROMPT, StrategicReview)
    
    review = review_chain.invoke({
        "hypothesis": state.current_hypothesis,
        "last_finding": state.last_finding,
        "investigation_queue": json.dumps([t.model_dump() for t in state.investigation_queue]),
        "evidence": state.evidence.model_dump_json(),
        "recent_tool_log": json.dumps([log.model_dump() for log in state.tool_log[-5:]]),
        "recent_analysis_trail": "\n".join(f"- {trail}" for trail in state.analysis_trail[-5:]),
        "triage_notes": json.dumps(state.narrative_coherence.notes),
        "current_coherence_score": state.narrative_coherence.score,
    })

    # Safety net: Filter out any tasks that have already been completed.
    pruned_queue = [
        task for task in review.updated_queue 
        if task.task_id not in state.completed_task_ids
    ]
    
    print(f"[*] Review complete. Reasoning: {review.reasoning}")

    updated_narrative_coherence = state.narrative_coherence.model_copy(
        update={"score": review.updated_coherence_score}
    )

    return {
        "investigation_queue": pruned_queue,
        "current_hypothesis": review.updated_hypothesis,
        "analysis_trail": [f"Strategic Review: {review.reasoning}"],
        "narrative_coherence": updated_narrative_coherence,
    }


def conditional_router(state: ForensicCaseFile) -> str:
    """The final decision-making step after a strategic review."""
    print("\n--- Running Conditional Router (The Brain) ---")
    
    # Circuit breaker to prevent infinite loops
    if state.interrogation_steps >= MAX_INTERROGATION_STEPS:
        print(f"[*] Decision: Max interrogation steps ({MAX_INTERROGATION_STEPS}) reached. Finalizing.")
        return "finalize"

    if not state.investigation_queue:
        print("[*] Decision: Investigation complete.")
        return "finalize" # We will add reassessment logic here later
    else:
        print("[*] Decision: Continue interrogation.")
        return "interrogate"
    

def finalize_node(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    Finalizes the analysis, generates a summary report, and saves the final state.
    """
    print("\n--- Running Finalize Node ---")
    
    # Create a simple summary report
    final_report_summary = f"Analysis complete for file {state.file_path} (SHA256: {state.file_hash_sha256}).\n"
    final_report_summary += f"Final Verdict: {state.verdict.value}\n"
    final_report_summary += f"Working Hypothesis at Conclusion: {state.current_hypothesis}\n"
    final_report_summary += f"Total Interrogation Steps: {state.interrogation_steps}\n"
    final_report_summary += "See the full evidence locker and analysis trail in the saved report."
    
    # Save the final, complete state to a JSON file
    output_filename = f"analysis_report_{state.analysis_session_id}.json"
    print(f"[*] Saving final report to {output_filename}...")
    
    # Create a temporary copy of the state to add the report before saving
    final_state_with_report = state.model_copy(update={"final_report": final_report_summary})

    with open(output_filename, "w") as f:
        f.write(final_state_with_report.model_dump_json(indent=2))
    
    print("[*] Report saved successfully.")

    # Return the final report to be included in the state
    return {"final_report": final_report_summary}



    


# --- 5. Graph Definition and Execution ---

def create_app():
    """
    Create and return the compiled LangGraph application with explicit input/output schemas.
    
    Input Schema: ForensicCaseFileInput (user-facing, only requires file_path)
    Output Schema: ForensicCaseFileOutput (manually converted in process_pdf_with_forensic_agent)
    Internal State: ForensicCaseFile (complete forensic investigation state)
    """
    workflow = StateGraph(
        state_schema=ForensicCaseFile,
        input_schema=ForensicCaseFileInput
    )
    
    # Add all the nodes to the graph
    workflow.add_node("triage", triage_node)
    workflow.add_node("interrogate", interrogation_node)
    workflow.add_node("strategic_review", strategic_review_node)
    workflow.add_node("finalize", finalize_node)

    # Define the graph's flow
    workflow.set_entry_point("triage")
    workflow.add_edge("triage", "interrogate")
    workflow.add_edge("interrogate", "strategic_review")
    
    # The conditional router directs the flow after the strategic review
    workflow.add_conditional_edges(
        "strategic_review",
        conditional_router,
        {"interrogate": "interrogate", "finalize": "finalize"}
    )
    workflow.add_edge("finalize", END)
    
    return workflow.compile()

# Create the app instance for LangGraph CLI
app = create_app()

def convert_to_output_schema(state: ForensicCaseFile) -> ForensicCaseFileOutput:
    """
    Convert the internal ForensicCaseFile state to the ForensicCaseFileOutput schema.
    This provides a clean, user-facing output format for LangGraph Studio.
    """
    print(f"[*] Converting state with {len(state.evidence.indicators_of_compromise)} IoCs and {len(state.evidence.attack_chain)} attack chain links")
    
    output = ForensicCaseFileOutput(
        success=len(state.errors) == 0,
        file_path=state.file_path,
        file_hash_sha256=state.file_hash_sha256,
        analysis_session_id=state.analysis_session_id,
        verdict=state.verdict,
        phase=state.phase,
        current_hypothesis=state.current_hypothesis,
        narrative_coherence_score=state.narrative_coherence.score,
        total_interrogation_steps=state.interrogation_steps,
        indicators_of_compromise=state.evidence.indicators_of_compromise,
        attack_chain_length=len(state.evidence.attack_chain),
        extracted_artifacts_count=len(state.evidence.extracted_artifacts),
        final_report=state.final_report,
        errors=state.errors
    )
    
    print(f"[*] Output conversion complete: {len(output.indicators_of_compromise)} IoCs, attack chain length: {output.attack_chain_length}")
    return output

def process_pdf_with_forensic_agent(
    input_data: ForensicCaseFileInput
) -> ForensicCaseFileOutput:
    """
    Process a PDF using the LangGraph forensic agent with proper input/output schema handling.
    
    Args:
        input_data: ForensicCaseFileInput with validated input parameters
        
    Returns:
        ForensicCaseFileOutput with all forensic analysis results
        
    Example:
        >>> from static_analysis.schemas import ForensicCaseFileInput
        >>> input_data = ForensicCaseFileInput(file_path="suspicious.pdf")
        >>> result = process_pdf_with_forensic_agent(input_data)
        >>> print(f"Verdict: {result.verdict}")
        >>> print(f"IoCs found: {len(result.indicators_of_compromise)}")
    """
    # Input is already validated as ForensicCaseFileInput by function signature
    
    # Create the processing graph
    graph = create_app()
    
    # Execute the graph with the validated input
    # LangGraph will automatically handle schema conversion
    final_result = graph.invoke(input_data.model_dump())
    
    # The graph should return ForensicCaseFileOutput based on our output_schema
    # But let's ensure it's properly typed and converted
    if isinstance(final_result, dict):
        # Convert dictionary result to ForensicCaseFile first, then to output schema
        case_file = ForensicCaseFile(**final_result)
        return convert_to_output_schema(case_file)
    elif isinstance(final_result, ForensicCaseFileOutput):
        return final_result
    elif isinstance(final_result, ForensicCaseFile):
        return convert_to_output_schema(final_result)
    else:
        # Fallback - create minimal output
        return ForensicCaseFileOutput(
            success=False,
            file_path=input_data.file_path,
            analysis_session_id="conversion_error",
            verdict=Verdict.PRESUMED_INNOCENT,
            phase=AnalysisPhase.TRIAGE,
            narrative_coherence_score=0.5,
            total_interrogation_steps=0,
            errors=[f"Unexpected result type: {type(final_result)}"]
        )


def main():
    """Main function for running the forensic analysis."""
    print("--- Setting up Forensic Analysis Graph ---")
    
    # NOTE: Replace with the actual path to your test file
    pdf_to_analyze = "tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    inputs = ForensicCaseFileInput(file_path=pdf_to_analyze)
    
    print("\n--- Streaming Agent Execution ---")
    
    final_state_dict = None
    # Use stream with "values" mode to get accumulated state at each step
    for event in app.stream(inputs.model_dump(), stream_mode="values"):
        # In "values" mode, event is the complete accumulated state after each node
        print(f"--- Node completed, current accumulated state available ---")
        final_state_dict = event  # This will be the complete state, not just partial updates
        print("\n--------------------------------\n")

    print("--- Agent execution finished. Processing final state. ---")
    final_state = ForensicCaseFile(**final_state_dict)
    
    print("\n\n--- Final Graph State (also saved to file by finalize_node) ---")
    print(final_state.model_dump_json(indent=2))

if __name__ == "__main__":
    main()