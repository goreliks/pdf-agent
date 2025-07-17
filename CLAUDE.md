# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a LangGraph-powered forensic PDF analysis tool that combines traditional static analysis with LLM-powered threat assessment. The system implements a structured investigation workflow using GPT-4 for intelligent triage and interrogation of PDF documents.

**Current Development Status**: Active development on `interrogation_node` branch with working multi-node forensic workflow.

## Key Architecture Components

### Core Workflow (LangGraph)
- **Entry Point**: `triage_node` - Enhanced initial PDF analysis using both pdfid and pdf-parser statistical analysis
- **Main Loop**: `interrogation_node` -> `strategic_review_node` -> conditional routing
- **Circuit Breaker**: `MAX_INTERROGATION_STEPS = 10` to prevent infinite loops
- **State Management**: `ForensicCaseFile` Pydantic model tracks entire investigation
- **Finalization**: `finalize_node` generates comprehensive analysis reports

### LLM Integration Pattern
The system uses a consistent pattern for LLM interactions:
- **System Prompt**: Establishes "Dr. Evelyn Reed" persona with pathologist principles
- **Structured Output**: All LLM responses use Pydantic models for type safety
- **Chain Creation**: `create_llm_chain()` in `utils.py` standardizes prompt + model setup
- **Vendor Agnostic**: Uses `PydanticOutputParser` for compatibility with any LLM provider

### Tool Execution Framework
- **Tool Manifest**: `TOOL_MANIFEST` in `prompts.py` defines available PDF analysis tools
- **Tool Executor**: `ToolExecutor` class provides safe, logged tool execution
- **Tool Integration**: LLM selects tools dynamically based on investigation needs
- **File Dump Support**: Enhanced with automatic file dumping and artifact cataloging

## Recent Major Enhancements

### Enhanced Triage Analysis
- **Dual Analysis**: Combines both `pdfid` and `pdf-parser -a` statistical analysis for comprehensive initial assessment
- **Combined Context**: Triage node now provides richer context to Dr. Reed for better initial hypothesis formation
- **Improved Evidence Locker**: Initial evidence includes both pdfid and statistical analysis results

### Improved Artifact Handling
- **Artifact IDs**: Each extracted artifact gets a unique identifier for better tracking
- **File Path Support**: Artifacts can reference both in-memory content and dumped files
- **Evidence Cataloging**: Streamlined process for cataloging extracted content and indicators of compromise
- **Artifact References**: Tasks can now reference specific artifacts from the evidence locker

### Tool Manifest Refinements
- **Streamlined Tools**: Focused tool set for common PDF analysis workflows
- **Clear Descriptions**: Each tool has specific use cases and prerequisites
- **File Dump Integration**: `dump_filtered_stream` tool with automatic confirmation messages
- **Diagnostic Tools**: Specialized tools for handling hidden/compressed objects

## Common Development Commands

### Installation and Setup
```bash
# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install from requirements (alternative)
pip install -r requirements.txt
```

### Running the Application
```bash
# Command line entry point
pdf-agent

# Direct module execution
python -m static_analysis.graph

# LangGraph development server
langgraph dev
```

### Testing and Development
```bash
# Run linting tools (if available)
black src/
isort src/
flake8 src/

# Run tests (if available)
pytest tests/
```

## File Structure and Key Components

### Core Module (`src/static_analysis/`)
- `graph.py` - Main LangGraph workflow definition and node implementations
- `schemas.py` - Pydantic models for state management and LLM interactions
- `prompts.py` - LLM prompts, tool manifest, and Dr. Reed persona
- `utils.py` - LLM chain creation, tool execution, and helper functions
- `test_run.py` - Testing utilities and workflow validation

### Analysis Tools (`src/static_analysis/tools/`)
- `pdfid.py` - PDF structure analysis tool (Didier Stevens)
- `pdf-parser.py` - PDF parsing and object extraction tool (Didier Stevens)

### Configuration Files
- `langgraph.json` - LangGraph configuration pointing to main graph
- `pyproject.toml` - Python package configuration with dependencies
- `.env` - Environment variables (OpenAI API key required)

## Development Workflow Patterns

### Adding New Analysis Tools
1. Add tool definition to `TOOL_MANIFEST` in `prompts.py`
2. Implement tool function in `utils.py` or as external script
3. Test tool execution through `ToolExecutor`
4. Update LLM prompts to reference new tool capabilities

### Modifying Investigation Logic
1. Core investigation flow is in `graph.py` node functions
2. State transitions controlled by `conditional_router`
3. LLM decision-making prompts in `prompts.py`
4. State structure defined in `schemas.py`

### LLM Prompt Engineering
- All prompts use "Dr. Evelyn Reed" persona with pathologist principles
- Structured output ensures type safety and consistent parsing
- Tool selection prompts include manifest and task context
- Analysis prompts include hypothesis and evidence context

## Environment Setup

### Required Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here
```

### Optional Configuration
- `PDFPARSER_OPTIONS` - Global options for PDF parser tool
- Custom tool paths can be configured in `utils.py`

## Common Issues and Solutions

### Tool Execution Failures
- Check tool paths in `utils.py:run_pdfid()` and `run_pdf_parser_full_statistical_analysis()`
- Verify Python executable paths in tool commands
- Tool failures are logged and treated as evidence

### LLM API Issues
- Verify OpenAI API key in `.env` file
- Check rate limits and API quotas
- LLM errors are captured in investigation state

### State Management
- Investigation state is preserved in `ForensicCaseFile` model
- Use `analysis_trail` field to track investigation progress
- Tool execution logs stored in `tool_log` field
- Evidence artifacts cataloged in `evidence.extracted_artifacts`

## Security Considerations

This tool analyzes potentially malicious PDFs. Always:
- Run in isolated/sandboxed environment
- Never execute extracted content
- Treat all PDF analysis as forensic evidence collection
- Use test samples from `tests/` directory for development

## Integration Points

### LangGraph Studio
- Visual workflow editing available via `langgraph dev`
- Real-time state inspection during investigation
- Workflow debugging and step-through capabilities

### External Tools
- PDF analysis tools from Didier Stevens (pdfid, pdf-parser)
- OpenAI GPT-4 for intelligent analysis
- Pydantic for type safety and validation

## Solution: Vendor-Agnostic Structured Output with PydanticOutputParser

### Problem Solved
The original implementation used OpenAI's `with_structured_output` which caused schema validation errors:
```
Invalid schema for response_format 'ToolAndTaskSelection': In context=('properties', 'arguments'), 'additionalProperties' is required to be supplied and to be false.
```

### Vendor-Agnostic Solution
We replaced `with_structured_output` with `PydanticOutputParser` for vendor-agnostic structured output parsing:

#### Key Benefits:
1. **Vendor Agnostic**: Works with any LLM provider (OpenAI, Anthropic, Cohere, local models, etc.)
2. **No Schema Restrictions**: No OpenAI-specific schema validation requirements
3. **Consistent Interface**: Same API across all LLM providers
4. **Better Error Handling**: Clear error messages for parsing failures
5. **Future-Proof**: Not tied to any specific provider's structured output implementation

#### Implementation Details:
```python
def create_llm_chain(system_prompt: str, human_prompt: str, response_model: BaseModel):
    """Helper function to create a structured LLM chain using PydanticOutputParser."""
    
    # Create the parser
    parser = PydanticOutputParser(pydantic_object=response_model)
    
    # Add format instructions to the human prompt
    enhanced_human_prompt = human_prompt + "\n\n{format_instructions}"
    
    # Create the prompt template
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(enhanced_human_prompt)
    ])
    
    # Partially fill the format instructions
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    
    # Create LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Create chain: prompt -> llm -> parser
    return prompt | llm | parser
```

### Current Development Status
✅ **Complete Multi-Node Workflow**: Full forensic investigation pipeline implemented
✅ **Enhanced Triage**: Dual analysis with pdfid + pdf-parser statistics
✅ **Artifact Management**: Comprehensive evidence locker with file dump support
✅ **Tool Integration**: Streamlined tool manifest with specialized diagnostic capabilities
✅ **LLM Integration**: Vendor-agnostic structured output parsing
✅ **State Management**: Complete investigation state tracking and report generation

### Next Development Priorities
- Fine-tune artifact analysis and extraction logic
- Enhance file content analysis capabilities
- Implement additional PDF analysis tools as needed
- Optimize investigation queue management and task prioritization

This solution provides a robust, vendor-agnostic approach to structured output parsing that works with any LLM provider and supports the complete forensic analysis workflow.