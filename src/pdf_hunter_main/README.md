# PDF Hunter Main Graph

A comprehensive PDF analysis pipeline that integrates PDF processing and forensic analysis as composed subgraphs using LangGraph.

## Overview

The PDF Hunter Main Graph is a composed LangGraph that orchestrates two specialized analysis workflows:

1. **PDF Processing Subgraph**: Parallel extraction of images, URLs, and file hashes
2. **Static Analysis Subgraph**: Forensic analysis for malicious content detection

## Architecture

### Subgraph Composition Pattern

This implementation follows LangGraph's **"Different State Schemas"** pattern for subgraph integration:

```
START 
  ↓
pdf_processing_node (invokes PDF processing subgraph)
  ↓
static_analysis_node (invokes static analysis subgraph)  
  ↓
final_aggregation_node (combines results)
  ↓
END
```

### Schema Design

- **`PDFHunterInput`**: User-facing input (pdf_path, pages_to_process, output_directory)
- **`PDFHunterState`**: Internal state management for subgraph coordination
- **`PDFHunterOutput`**: Comprehensive results from both analysis stages

### Subgraph Integration Details

#### PDF Processing Node
```python
def pdf_processing_node(state: PDFHunterState) -> Dict[str, Any]:
    # Transform main state → PDFProcessingInput
    pdf_input = PDFProcessingInput(
        pdf_path=state["pdf_path"],
        pages_to_process=state.get("pages_to_process", 1),
        output_directory=state.get("output_directory")
    )
    
    # Invoke subgraph
    pdf_result = pdf_processing_app.invoke(pdf_input.model_dump())
    
    # Transform result → main state
    return {"pdf_processing_result": pdf_result}
```

#### Static Analysis Node  
```python
def static_analysis_node(state: PDFHunterState) -> Dict[str, Any]:
    # Transform main state → ForensicCaseFileInput (only file_path needed)
    forensic_input = ForensicCaseFileInput(file_path=state["pdf_path"])
    
    # Invoke subgraph
    forensic_result = static_analysis_app.invoke(forensic_input.model_dump())
    
    # Transform result → main state
    return {"static_analysis_result": forensic_result}
```

## Usage

### Basic Usage

```python
from pdf_hunter_main import process_pdf_with_hunter, PDFHunterInput

# Create validated input
input_data = PDFHunterInput(
    pdf_path="suspicious.pdf",
    pages_to_process=1,  # Process first page only
    output_directory="./analysis_output"  # Optional: auto-generated if None
)

# Run comprehensive analysis
result = process_pdf_with_hunter(input_data)

# Access results from both stages
print(f"Verdict: {result.forensic_verdict}")
print(f"Images extracted: {len(result.extracted_images)}")
print(f"IoCs found: {len(result.indicators_of_compromise)}")
print(f"Is suspicious: {result.is_suspicious()}")
```

### LangGraph Studio Integration

The graph is exported as `app` for LangGraph Studio:

```python
# In pdf_hunter_main/pdf_hunter_graph.py
app = create_pdf_hunter_graph()
```

LangGraph Studio will show only the user-facing input fields:
- `pdf_path` (required)
- `pages_to_process` (optional, default: 1)  
- `output_directory` (optional, auto-generated if None)

### Direct Graph Usage

```python
from pdf_hunter_main import create_pdf_hunter_graph, PDFHunterInput

# Create the graph
graph = create_pdf_hunter_graph()

# Execute with validated input
input_data = PDFHunterInput(pdf_path="document.pdf")
result = graph.invoke(input_data.model_dump())
```

## Output Structure

The `PDFHunterOutput` provides comprehensive results from both analysis stages:

### PDF Processing Results
- `pdf_hash`: SHA1 and MD5 hashes
- `page_count`: Total pages in PDF
- `extracted_images`: List of extracted images with metadata
- `extracted_urls`: List of URLs found in PDF

### Forensic Analysis Results
- `forensic_verdict`: Analysis verdict (Presumed_Innocent, Suspicious, Malicious, Benign)
- `narrative_coherence_score`: Deception detection score (0.0 = deceptive, 1.0 = coherent)
- `indicators_of_compromise`: List of IoCs found
- `attack_chain_length`: Number of attack chain links
- `extracted_artifacts_count`: Number of forensic artifacts

### Utility Methods
```python
result.is_suspicious()  # Check if PDF is suspicious
result.has_artifacts()  # Check if forensic artifacts found
result.get_summary()   # Get comprehensive summary dict
```

## Error Handling

The composed graph provides robust error handling:

- **Independent Subgraph Failures**: If one subgraph fails, the other can still complete
- **Comprehensive Error Tracking**: Separate error lists for each analysis stage
- **Graceful Degradation**: Partial results returned even with failures

```python
result = process_pdf_with_hunter(input_data)

if not result.success:
    print("Analysis had errors:")
    for error in result.pdf_processing_errors:
        print(f"  PDF Processing: {error}")
    for error in result.forensic_analysis_errors:
        print(f"  Forensic Analysis: {error}")
```

## Benefits of This Architecture

### 1. **Clean Separation of Concerns**
- PDF processing handles data extraction
- Static analysis handles security analysis
- Main graph handles orchestration

### 2. **Type Safety**
- Full Pydantic validation throughout
- Clear input/output contracts
- IDE autocompletion support

### 3. **Modular Design**
- Subgraphs can be developed independently
- Easy to test individual components
- Reusable subgraphs for other compositions

### 4. **LangGraph Best Practices**
- Follows "different state schemas" pattern
- Proper subgraph integration
- Schema-based input/output validation

## Integration Requirements

### No Schema Changes Needed

Both existing subgraphs work as-is:

- **PDF Processing**: Already has proper input/output schemas
- **Static Analysis**: Already takes only `file_path` as input

### Dependencies

The main graph imports from both subgraph modules:

```python
from pdf_processing.pdf_agent import app as pdf_processing_app
from pdf_processing.agent_schemas import PDFProcessingInput

from static_analysis.graph import app as static_analysis_app  
from static_analysis.schemas import ForensicCaseFileInput
```

## Testing

Run the integration test:

```bash
cd src/pdf_hunter_main
python pdf_hunter_graph.py
```

This will execute both subgraphs sequentially and show comprehensive results.

## Future Enhancements

### Potential Improvements

1. **Parallel Subgraph Execution**: Run both analyses in parallel if they don't need interdependence
2. **Conditional Analysis**: Skip forensic analysis for clearly benign files
3. **Result Caching**: Cache results for identical files
4. **Progress Streaming**: Stream intermediate results during processing

### Adding New Subgraphs

To add additional analysis stages:

1. Create new subgraph with proper input/output schemas
2. Add transform node function 
3. Update `PDFHunterState` and `PDFHunterOutput`
4. Add to the graph flow

This architecture makes it easy to extend the analysis pipeline with additional specialized analysis tools. 