# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **comprehensive PDF analysis platform** powered by LangGraph that combines parallel data extraction, forensic investigation, and visual threat assessment. The platform has evolved from a single-purpose forensic tool into a composed multi-graph system with specialized analysis workflows.

**🔥 Current Development Status**: ✅ **Major Architecture Enhancement** - Complete composed graph system with parallel processing capabilities on `preprocessing_connections` branch.

## Recent Major Architecture Evolution

### 🏗️ **New Composed Graph Architecture (preprocessing_connections branch)**

**Latest Commits (Jul 19, 2025):**
- `767517c` - "fixed output schemas full output" - Final schema validation and output formatting
- `429625a` - "updated working schemas" - Enhanced Pydantic schemas across all modules
- `86617b5` - "working version of url and image extraction graph" - Parallel processing implementation

The platform now consists of **three specialized LangGraph applications**:

1. **📊 PDF Hunter Main Graph** (`src/pdf_hunter_main/`) - Master orchestrator using subgraph composition
2. **⚡ PDF Processing Graph** (`src/pdf_processing/`) - Parallel data extraction engine  
3. **🔍 Static Analysis Graph** (`src/static_analysis/`) - Forensic investigation workflow
4. **👁️ Visual Analysis Components** (`src/visual_analysis/`) - *In Development* - Visual deception detection

### 🎯 **LangGraph Configuration Evolution**

**New `langgraph.json` (Multi-Graph Setup):**
```json
{
  "graphs": {
    "pdf_hunter": "./src/pdf_hunter_main/pdf_hunter_graph.py:app",     // Master composer
    "pdf_processing": "./src/pdf_processing/pdf_agent.py:app",         // Data extraction  
    "agent": "./src/static_analysis/graph.py:app"                      // Forensic analysis
  }
}
```

This enables **three distinct workflows** in LangGraph Studio with clean input/output interfaces.

## Key Architecture Components

### 🆕 **Master Orchestrator (PDF Hunter Main)**

**File**: `src/pdf_hunter_main/pdf_hunter_graph.py`

Implements LangGraph's **"Different State Schemas"** pattern for subgraph composition:

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

**Schema Architecture:**
- **`PDFHunterInput`**: User-facing interface (pdf_path, pages_to_process, output_directory)
- **`PDFHunterState`**: Internal state management between subgraphs
- **`PDFHunterOutput`**: Comprehensive results from all analysis stages

### ⚡ **Parallel Processing Engine (PDF Processing)**

**File**: `src/pdf_processing/pdf_agent.py`

Implements **validation-first then parallel processing** pattern:

```
START → validation → [image_extraction, url_extraction] → aggregation → END
```

**Key Features:**
- **Schema-First Design**: Full Pydantic validation for type safety
- **Parallel Node Execution**: Image extraction, URL extraction, and hashing run simultaneously
- **LangGraph Studio Ready**: Clean interface showing only user-facing input fields
- **Error Resilience**: Graceful degradation with partial results

**Schemas:**
- **`PDFProcessingInput`**: Validates all input parameters with field validators
- **`PDFProcessingOutput`**: Type-safe output structure  
- **`PDFProcessingState`**: Internal TypedDict for LangGraph state management

### 🔍 **Forensic Investigation Workflow (Static Analysis)**

**File**: `src/static_analysis/graph.py`

**Production-Ready Status**: ✅ Complete forensic workflow with proven malware detection capabilities.

**Core Workflow (LangGraph):**
- **Entry Point**: `triage_node` - Enhanced initial PDF analysis using both pdfid and pdf-parser
- **Main Loop**: `interrogation_node` -> `strategic_review_node` -> conditional routing
- **Circuit Breaker**: `MAX_INTERROGATION_STEPS = 10` to prevent infinite loops
- **State Management**: `ForensicCaseFile` Pydantic model tracks entire investigation
- **Finalization**: `finalize_node` generates comprehensive analysis reports

### 🛡️ **LLM Integration Pattern**

**Vendor-Agnostic Implementation:**
All graphs use consistent LLM integration via `PydanticOutputParser`:

```python
def create_llm_chain(system_prompt: str, human_prompt: str, response_model: BaseModel):
    """Helper function to create a structured LLM chain using PydanticOutputParser."""
    
    parser = PydanticOutputParser(pydantic_object=response_model)
    enhanced_human_prompt = human_prompt + "\n\n{format_instructions}"
    
    prompt = ChatPromptTemplate.from_messages([
        SystemMessagePromptTemplate.from_template(system_prompt),
        HumanMessagePromptTemplate.from_template(enhanced_human_prompt)
    ])
    
    prompt = prompt.partial(format_instructions=parser.get_format_instructions())
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    return prompt | llm | parser
```

**Benefits:**
- **Vendor Agnostic**: Works with any LLM provider
- **No Schema Restrictions**: No OpenAI-specific validation requirements
- **Consistent Interface**: Same API across all providers
- **Better Error Handling**: Clear parsing failure messages

## Recent Performance Metrics

### 🏆 **Real-World Malware Detection Success (Static Analysis)**
- ✅ Successfully analyzed malicious PDF with /Launch action attack vector
- ✅ Completed full investigation in **8 interrogation steps** (well under 10-step limit)
- ✅ **100% attack chain mapping** - traced OpenAction → Launch → PowerShell → malware download
- ✅ **Complete payload extraction** - decoded hex payload revealing Windows Defender bypass
- ✅ **IoC identification** - extracted malicious URL and persistence mechanisms
- ✅ **Perfect autonomy detection** - identified /OpenAction and /AcroForm deception patterns

### ⚡ **Processing Efficiency (Data Extraction)**
- **Parallel Processing**: Image extraction, URL extraction, and hashing run simultaneously
- **Type Safety**: Zero runtime errors through comprehensive Pydantic validation  
- **Memory Efficiency**: Processes large PDFs with optimized resource usage
- **Error Resilience**: Graceful degradation with partial results on component failures

## Common Development Commands

### Installation and Setup
```bash
# Install in development mode with current architecture
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Install from requirements (alternative)
pip install -r requirements.txt
```

### Running the Application

#### 🎯 **Master Orchestrator (Recommended)**
```bash
# Complete analysis pipeline
python -c "from pdf_hunter_main import process_pdf_with_hunter, PDFHunterInput; print('Ready for comprehensive analysis')"
```

#### ⚡ **Data Extraction Only**
```bash
# Fast parallel processing
python -c "from pdf_processing import process_pdf_with_agent, PDFProcessingInput; print('Ready for data extraction')"
```

#### 🔍 **Forensic Analysis Only**
```bash  
# Deep security analysis
python -m static_analysis.graph
```

#### 🎨 **LangGraph Studio (All Graphs)**
```bash
# Launch with multi-graph support
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

### 🆕 **Master Orchestrator (`src/pdf_hunter_main/`)**
- `pdf_hunter_graph.py` - Composed workflow definition with subgraph integration
- `schemas.py` - Input/output schemas for user-facing interface
- `README.md` - Architecture documentation and usage examples

### ⚡ **Parallel Processing (`src/pdf_processing/`)**
- `pdf_agent.py` - LangGraph processing workflow with parallel nodes
- `agent_schemas.py` - Comprehensive Pydantic schemas for validation
- `image_extraction.py` - Base64 encoding, perceptual hashing, SHA1-based saving
- `url_extraction.py` - URL extraction from annotations and text content
- `hashing.py` - SHA1 and MD5 hash calculation utilities
- `example_agent_usage.py` - Usage examples and integration patterns
- `test_schema_validation.py` - Schema validation testing
- `README.md` - Processing documentation

### 🔍 **Forensic Investigation (`src/static_analysis/`)**
- `graph.py` - Main LangGraph workflow definition and node implementations
- `schemas.py` - Pydantic models for state management and LLM interactions
- `prompts.py` - LLM prompts, tool manifest, and Dr. Reed persona
- `utils.py` - LLM chain creation, tool execution, and helper functions
- `test_run.py` - Testing utilities and workflow validation
- `tools/` - PDF analysis tools (pdfid.py, pdf-parser.py)

### 👁️ **Visual Analysis (`src/visual_analysis/`)**
- `prompts.py` - Visual analysis prompts and persona definitions *(Work in Progress)*

### 📋 **Configuration Files**
- `langgraph.json` - **🆕 Multi-graph configuration** with three specialized workflows
- `pyproject.toml` - Python package configuration with dependencies
- `.env` - Environment variables (OpenAI API key required)

## Development Workflow Patterns

### Adding New Analysis Components
1. **Schema-First Design**: Define Pydantic schemas for inputs/outputs/state
2. **Node Implementation**: Create processing nodes with error handling
3. **Graph Integration**: Add to appropriate graph or create new subgraph
4. **Validation**: Add comprehensive type checking and validation
5. **Documentation**: Update module README with usage examples

### Modifying Investigation Logic
1. **Subgraph Selection**: Choose appropriate graph (hunter/processing/static)
2. **State Management**: Update relevant Pydantic schemas
3. **Node Updates**: Modify node functions with proper type annotations
4. **Testing**: Validate with schema validation tests
5. **Integration**: Test subgraph composition if using hunter main

### Subgraph Composition Patterns
1. **Different State Schemas**: Each subgraph maintains independent state
2. **Transform Functions**: Convert between subgraph input/output formats
3. **Error Isolation**: Subgraph failures don't affect other components
4. **Type Safety**: Full Pydantic validation at all interfaces

## Environment Setup

### Required Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here              # Required for LLM analysis
```

### Optional Configuration
```bash
PDFPARSER_OPTIONS=--verbose                   # Global options for PDF parser tools
```

## Common Issues and Solutions

### Architecture-Specific Issues

#### Subgraph Import Errors
```python
# Ensure proper module installation
pip install -e .

# Check import paths for subgraphs
from pdf_processing.pdf_agent import app as pdf_processing_app
from static_analysis.graph import app as static_analysis_app
```

#### Schema Validation Failures
```python
# Use proper Pydantic input models
from pdf_hunter_main.schemas import PDFHunterInput
from pdf_processing.agent_schemas import PDFProcessingInput
from static_analysis.schemas import ForensicCaseFileInput

# Validate before processing
try:
    input_data = PDFHunterInput(pdf_path="test.pdf")
except ValidationError as e:
    print(f"Validation error: {e}")
```

#### LangGraph Studio Graph Selection
- **pdf_hunter**: Complete analysis pipeline (recommended)
- **pdf_processing**: Data extraction only
- **agent**: Forensic analysis only

### Legacy Compatibility
- **Old static analysis**: Still available via `static_analysis.graph:app`
- **Direct PDF processing**: Available via `pdf_processing.pdf_agent:app`  
- **Migration path**: Use `pdf_hunter_main` for new implementations

## Integration Points

### LangGraph Studio
- **Multi-Graph Support**: Three specialized workflows in single interface
- **Clean Input Interfaces**: Only user-facing fields shown for each graph
- **Visual Workflow Management**: Real-time state inspection and debugging
- **Subgraph Visualization**: See composed workflow interactions

### External Tools
- **PDF Analysis Tools**: Didier Stevens tools (pdfid, pdf-parser)
- **OpenAI GPT-4**: Intelligent analysis via vendor-agnostic interface
- **Pydantic**: Comprehensive type safety and validation
- **LangGraph**: Advanced workflow orchestration and composition

## Security Considerations

This platform analyzes potentially malicious PDFs. Always:
- **Isolated Environment**: Run in sandboxed/VM environment
- **Never Execute**: Don't execute extracted content
- **Forensic Evidence**: Treat all analysis as evidence collection
- **Test Samples**: Use files from `tests/` directory for development

## Current Development Priorities

### ✅ **Completed (preprocessing_connections branch)**
1. **Composed Graph Architecture**: Master orchestrator with subgraph integration
2. **Parallel Processing Engine**: Simultaneous data extraction operations
3. **Schema-First Design**: Full Pydantic validation across all workflows
4. **Multi-Graph LangGraph Configuration**: Three specialized workflows
5. **Type Safety**: Comprehensive error handling and validation

### 🎯 **Next Phase: Visual Analysis Integration**

**Goal**: Introduce Visual Deception Analyst Agent for rendered PDF appearance analysis.

**Key Components:**
- **Visual Analysis Expert Persona**: HCI/UX Security and Cognitive Psychology expertise
- **Cross-Modal Analysis**: Compare visual appearance vs. technical reality  
- **Psychological Tactics Detection**: Identify social engineering patterns
- **Structured Feature Extraction**: Comprehensive visual analysis reports

**Integration Pattern:**
- Add as fourth subgraph to PDF Hunter Main composition
- Maintain schema-first design with visual analysis input/output models
- Preserve parallel processing capabilities where possible

### 🔄 **Platform Enhancements**
1. **Parallel Subgraph Execution**: Run extraction and analysis simultaneously when independent
2. **Result Caching**: Implement hash-based caching for identical files
3. **Batch Processing**: Multi-file analysis workflows
4. **Custom Pipelines**: User-configurable workflow composition

## Branch Strategy

### 🚀 **Current Active: preprocessing_connections**
- **Status**: Major architecture enhancement with production-ready features
- **Features**: Composed graphs, parallel processing, full schema validation
- **Use For**: New development and production deployments

### 🏆 **Stable Reference: interrogation_node**  
- **Status**: Production-ready single-graph forensic analysis
- **Features**: Complete investigation workflow with proven malware detection
- **Use For**: Reference implementation and fallback

### 🎨 **Experimental: visual_agent**
- **Status**: Early development of visual analysis components
- **Features**: Basic visual analysis prompts and persona definitions
- **Use For**: Visual analysis development and experimentation

### Current Development Status Summary

**Architecture Evolution Complete**: ✅
- Composed graph system with subgraph integration
- Parallel processing engine with type safety
- Multi-graph LangGraph Studio configuration
- Schema-first design across all components

**Production Capabilities**: ✅
- Complete PDF data extraction (images, URLs, hashes)
- Proven forensic malware detection workflow
- Vendor-agnostic LLM integration
- Comprehensive error handling and validation

**Ready for Visual Analysis Integration**: ✅
- Extensible architecture for additional subgraphs
- Established patterns for cross-modal analysis
- Type-safe interfaces for new analysis components
