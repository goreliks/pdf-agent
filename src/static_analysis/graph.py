import json
from typing import Dict, Any

from langgraph.graph import StateGraph, END
from pydantic import BaseModel

# Import our schemas, prompts, and utils
from static_analysis.schemas import (
    ForensicCaseFile, InvestigationTask, ForensicCaseFileInput, TriageAnalysis,
    ToolAndTaskSelection, InterrogationAnalysis, AttackChainLink, StrategicReview
)
from static_analysis.prompts import (
    SYSTEM_PROMPT, TRIAGE_HUMAN_PROMPT, TECHNICIAN_HUMAN_PROMPT,
    ANALYST_HUMAN_PROMPT, STRATEGIC_REVIEW_HUMAN_PROMPT, TOOL_MANIFEST
)
from static_analysis.utils import create_llm_chain, run_pdfid, ToolExecutor


# --- TOOL EXECUTOR INSTANTIATED ---
# Create a single, reusable instance of our tool executor
tool_executor = ToolExecutor(manifest=TOOL_MANIFEST)

# --- CONFIGURATION ---
MAX_INTERROGATION_STEPS = 10 # Circuit breaker for infinite loops



def triage_node(state: ForensicCaseFile) -> Dict[str, Any]:
    """
    Runs the initial pdfid scan and performs triage to form a
    starting hypothesis and investigation plan.
    """
    print("\n--- Running Triage Node ---")
    pdfid_output = run_pdfid(state.file_path)
    print(f"[*] PDFID Output: {pdfid_output}")
    chain = create_llm_chain(SYSTEM_PROMPT, TRIAGE_HUMAN_PROMPT, TriageAnalysis)

    print("[*] Dr. Reed is performing initial triage...")
    llm_response = chain.invoke({"pdfid_output": pdfid_output})

    # Create an initial EvidenceLocker with the pdfid results
    initial_evidence = {
        "structural_summary": {"pdfid": pdfid_output}
    }
    
    return {
        "verdict": llm_response.verdict,
        "phase": llm_response.phase,
        "current_hypothesis": llm_response.hypothesis,
        "investigation_queue": llm_response.investigation_queue,
        "analysis_trail": [llm_response.analysis_trail],
        "evidence": initial_evidence,
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
    task_lookahead = state.investigation_queue[:3]
    
    print("[*] Dr. Reed is in instrumental mode (selecting task and tool)...")
    technician_chain = create_llm_chain(SYSTEM_PROMPT, TECHNICIAN_HUMAN_PROMPT, ToolAndTaskSelection)
    
    tool_selection = technician_chain.invoke({
        "hypothesis": state.current_hypothesis,
        "file_path": state.file_path,
        "task_lookahead": json.dumps([t.model_dump() for t in task_lookahead]),
        "tool_manifest": json.dumps(TOOL_MANIFEST)
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
    
    # Add any new Extracted Artifacts to the locker, using the source object ID as the key
    for artifact in analysis.extracted_artifacts_additions:
        updated_evidence.extracted_artifacts[artifact.source_object_id] = artifact
    # --- End of Evidence Processing ---
    
    # Prepare the final state update
    updates = {
        "investigation_queue": new_queue,
        "last_finding": analysis.findings_summary,
        "analysis_trail": [f"Interrogated '{tool_selection.chosen_task.reason}'. Finding: {analysis.findings_summary}"],
        "evidence": updated_evidence,  # Use the fully updated evidence object
        "tool_log": [tool_log_entry],
        "interrogation_steps": current_steps
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
        "investigation_queue": json.dumps([t.model_dump() for t in state.investigation_queue])
    }) # REAL CALL
    
    print(f"[*] Review complete. Reasoning: {review.reasoning}")

    return {
        "investigation_queue": review.reprioritized_queue,
        "current_hypothesis": review.updated_hypothesis,
        "analysis_trail": [f"Strategic Review: {review.reasoning}"]
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
    """Create and return the compiled LangGraph application."""
    workflow = StateGraph(ForensicCaseFile)
    
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

def main():
    """Main function for running the forensic analysis."""
    print("--- Setting up Forensic Analysis Graph ---")
    
    # NOTE: Replace with the actual path to your test file
    pdf_to_analyze = "tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    inputs = ForensicCaseFileInput(file_path=pdf_to_analyze)
    
    print("\n--- Streaming Agent Execution ---")
    
    final_state_dict = None
    # Use the stream to get real-time updates and capture the final state
    for event in app.stream(inputs.model_dump()):
        # The event is a dictionary where the key is the node name and the value is the full state
        # after that node has run. We print it for real-time viewing.
        for node_name, state_update in event.items():
            print(f"--- Output from node '{node_name}' ---")
            # The last state update we receive will be the final state of the graph
            final_state_dict = state_update
            # We don't need to print the full state here, the node prints are enough
            # print(json.dumps(final_state_dict, indent=2, default=str))
        print("\n--------------------------------\n")

    if final_state_dict:
        print("--- Agent execution finished. Processing final state. ---")
        # The final state is already captured in the dictionary
        final_state = ForensicCaseFile(**final_state_dict)
        
        print("\n\n--- Final Graph State (also saved to file by finalize_node) ---")
        print(final_state.model_dump_json(indent=2))
    else:
        print("--- Agent execution did not produce a final state. ---")

if __name__ == "__main__":
    main()