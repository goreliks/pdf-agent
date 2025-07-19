# PDF Agent - Comprehensive PDF Analysis Platform

A LangGraph-powered forensic analysis platform for PDF documents that combines parallel data extraction, static analysis, and visual threat assessment.

**🔥 Current Status**: ✅ **Major Architecture Enhancement** - New composed multi-graph system with parallel processing capabilities on `preprocessing_connections` branch.

## Platform Overview

The PDF Agent has evolved into a comprehensive analysis platform with three specialized LangGraph applications:

### 🏗️ **New Architecture (Current Development)**

1. **📊 PDF Hunter Main Graph** - Master orchestrator that composes subgraphs for comprehensive analysis
2. **⚡ PDF Processing Graph** - Parallel extraction engine for images, URLs, and file hashes  
3. **🔍 Static Analysis Graph** - Forensic investigation workflow with proven malware detection
4. **👁️ Visual Analysis Components** - *In Development* - Visual deception detection (see `visual_agent` branch)

### 🆕 **Centralized LLM Configuration**

The platform now features a centralized configuration system (`src/config.py`) that provides:
- **Multi-Provider Support**: OpenAI, Azure, Anthropic, Google, Ollama, and Hugging Face
- **Role-Based LLM Assignment**: Different models for triage, analysis, technical tasks, and strategic review
- **Easy Model Switching**: Change providers across the entire platform from a single file
- **Development Flexibility**: Quickly test different models for different analysis roles

### 🎯 **LangGraph Studio Integration**

Three graphs are now available in LangGraph Studio:
- `pdf_hunter` - Master composed graph for end-to-end analysis
- `pdf_processing` - Dedicated data extraction workflow
- `agent` - Forensic analysis workflow (legacy name for static analysis)

## Key Features

### 🆕 **Latest Enhancements (preprocessing_connections branch)**

- **🔧 Composed Graph Architecture**: Master PDF Hunter graph orchestrates specialized subgraphs
- **⚡ Parallel Processing**: Simultaneous image extraction, URL extraction, and hash calculation
- **🛡️ Schema-First Design**: Full Pydantic validation for type safety across all workflows
- **🎨 LangGraph Studio Ready**: Clean interface showing only user-facing input fields
- **🔄 Modular Integration**: Independent subgraphs with clean state management

### 🏆 **Proven Capabilities**

- 🔧 **Centralized LLM Configuration**: Multi-provider support with role-based model assignment
- 🔍 **Enhanced Static Analysis**: Uses both `pdfid` and `pdf-parser` for comprehensive PDF structure analysis
- 🤖 **LLM-Powered Investigation**: Multi-provider LLM integration with "Dr. Evelyn Reed" forensic pathologist persona
- 📊 **Complete Forensic Workflow**: Multi-node investigation pipeline with triage → interrogation → strategic review → finalization
- 🔗 **Advanced State Management**: Complex investigation state tracking with artifact cataloging
- 📝 **Comprehensive Evidence Tracking**: Advanced artifact cataloging with file dump support
- 🛡️ **Vendor-Agnostic LLM**: Compatible with any LLM provider via centralized configuration
- 📋 **Detailed Reporting**: Structured analysis trails and comprehensive findings reports

## Recent Architecture Evolution

### From Single Graph to Composed Platform

**Previous Architecture (interrogation_node branch):**
- Single forensic analysis graph
- Manual preprocessing required
- Limited data extraction capabilities

**New Architecture (preprocessing_connections branch):**
- **Master orchestrator** (`pdf_hunter`) composes specialized subgraphs
- **Parallel data extraction** with automatic preprocessing
- **Type-safe interfaces** between all components
- **Clean separation** of extraction vs. analysis concerns

### Schema-Driven Development

All graphs now use comprehensive Pydantic schemas:
- **`PDFHunterInput/Output`** - User-facing interface for complete analysis
- **`PDFProcessingInput/Output`** - Data extraction workflow
- **`ForensicCaseFileInput/Output`** - Security analysis workflow

## Installation & Setup

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (for LLM features)

### Quick Setup

1. **Clone and switch to current development branch:**
   ```bash
   git clone <repository-url>
   cd pdf-agent
   git checkout preprocessing_connections
   ```

2. **Install with dependencies:**
   ```bash
   pip install -e .
   # Or for development:
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage Examples

### 🎯 **Comprehensive Analysis (Recommended)**

```python
from pdf_hunter_main import process_pdf_with_hunter, PDFHunterInput

# Complete analysis with all capabilities
input_data = PDFHunterInput(
    pdf_path="suspicious.pdf",
    pages_to_process=1,
    output_directory="./analysis_output"
)

result = process_pdf_with_hunter(input_data)

# Rich results from all analysis stages
print(f"Forensic Verdict: {result.forensic_verdict}")
print(f"Images Extracted: {len(result.extracted_images)}")
print(f"URLs Found: {len(result.extracted_urls)}")
print(f"IoCs Detected: {len(result.indicators_of_compromise)}")
print(f"Is Suspicious: {result.is_suspicious()}")
```

### ⚡ **Data Extraction Only**

```python
from pdf_processing import process_pdf_with_agent, PDFProcessingInput

# Fast parallel extraction without forensic analysis
input_data = PDFProcessingInput(
    pdf_path="document.pdf",
    pages_to_process=1
)

result = process_pdf_with_agent(input_data)
print(f"PDF Hash: {result.pdf_hash.sha1}")
print(f"Extracted: {len(result.extracted_images)} images, {len(result.extracted_urls)} URLs")
```

### 🔍 **Forensic Analysis Only**

```python
from static_analysis.graph import app
from static_analysis.schemas import ForensicCaseFileInput

# Deep forensic investigation
inputs = ForensicCaseFileInput(file_path="malware.pdf")
result = app.invoke(inputs.model_dump())
```

### 🎨 **LangGraph Studio**

```bash
langgraph dev
```

Access three specialized workflows:
- **pdf_hunter** - Complete analysis pipeline
- **pdf_processing** - Data extraction workflow  
- **agent** - Forensic analysis workflow

## Proven Performance Metrics

### 🏆 **Real-World Malware Detection (Static Analysis)**
- ✅ **Malicious PDF Analysis**: Successfully analyzed PDF with /Launch action attack vector
- ✅ **Efficient Investigation**: Completed in 8 steps (20% under the 10-step safety limit)
- ✅ **Complete Attack Chain**: Mapped OpenAction → Launch → PowerShell → malware download
- ✅ **Payload Extraction**: Decoded hex payload revealing Windows Defender bypass techniques
- ✅ **IoC Collection**: Identified malicious URL: `https://badreddine67.000webhostapp.com/Theme_Smart.scr`
- ✅ **Persistence Detection**: Discovered startup folder installation and VBS execution

### ⚡ **Processing Efficiency (Data Extraction)**
- **Parallel Processing**: Image extraction, URL extraction, and hashing run simultaneously
- **Type Safety**: Zero runtime errors through comprehensive Pydantic validation
- **Memory Efficiency**: Processes large PDFs with optimized resource usage
- **Error Resilience**: Graceful degradation with partial results on component failures

## Project Structure

```
pdf-agent/
├── src/
│   ├── config.py                     # 🆕 Centralized LLM configuration
│   ├── pdf_hunter_main/          # 🆕 Master orchestrator graph
│   │   ├── pdf_hunter_graph.py   # Composed workflow
│   │   ├── schemas.py            # Input/output types
│   │   └── README.md             # Architecture documentation
│   ├── pdf_processing/           # 🆕 Parallel data extraction
│   │   ├── pdf_agent.py          # LangGraph processing workflow
│   │   ├── agent_schemas.py      # Pydantic schemas
│   │   ├── image_extraction.py   # Image processing utilities
│   │   ├── url_extraction.py     # URL extraction utilities
│   │   └── README.md             # Processing documentation
│   ├── static_analysis/          # 🔍 Forensic investigation
│   │   ├── graph.py              # Investigation workflow
│   │   ├── schemas.py            # Forensic data models
│   │   ├── prompts.py            # LLM prompts and personas
│   │   └── tools/                # Analysis tools
│   └── visual_analysis/          # 👁️ Visual deception detection (WIP)
│       └── prompts.py            # Visual analysis prompts
├── notebooks/                    # Development notebooks
├── tests/                        # Test files and samples
├── langgraph.json               # 🆕 Multi-graph configuration
└── pyproject.toml               # Project dependencies
```

## Development Branches

### 🚀 **Current: preprocessing_connections**
- **Status**: Active development with major architecture enhancements
- **Features**: Composed graphs, parallel processing, full Pydantic validation
- **Ready For**: Production use with enhanced capabilities

### 🏆 **Stable: interrogation_node**
- **Status**: Production-ready forensic analysis
- **Features**: Complete forensic workflow with proven malware detection
- **Use Case**: Standalone forensic investigation

### 🎨 **Experimental: visual_agent**
- **Status**: Early development
- **Features**: Visual deception detection components
- **Goal**: HCI-focused visual analysis integration

## Advanced Configuration

### Environment Variables
```bash
OPENAI_API_KEY=your_api_key_here              # Required for LLM analysis
PDFPARSER_OPTIONS=--verbose                   # Optional PDF parser settings
```

### LLM Configuration

The platform uses a centralized configuration system in `src/config.py` for flexible LLM provider management:

#### **Supported Providers**
```python
# OpenAI (Default)
openai_4o = ChatOpenAI(model="gpt-4o", temperature=0)
openai_o3_mini = ChatOpenAI(model="o3-mini", temperature=0)

# Azure OpenAI
# azure_gpt_4o = ChatAzure(model="gpt-4o", temperature=0)

# Anthropic Claude
# anthropic_claude_3_5_sonnet = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0)

# Google Gemini
# google_gemini_1_5_flash = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0)

# Ollama (Local)
# ollama_llama3_8b = ChatOllama(model="llama3.8b", temperature=0)

# Hugging Face
# huggingface_qwen_vl = ChatHuggingFace(llm=hf_qwen_vl_pipeline)
```

#### **Role-Based Model Assignment**
The static analysis workflow uses specialized models for different analysis roles:
```python
# Static Analysis Configuration
STATIC_ANALYSIS_ANALYST_LLM = openai_4o        # Deep technical analysis
STATIC_ANALYSIS_TRIAGE_LLM = openai_4o         # Initial assessment
STATIC_ANALYSIS_TECHNICIAN_LLM = openai_4o     # Tool selection
STATIC_ANALYSIS_STRATEGIC_REVIEW_LLM = openai_4o  # High-level review

# Visual Analysis Configuration (Future)
VISUAL_ANALYSIS_ANALYST_LLM = openai_4o        # Visual deception detection
```

#### **Switching Providers**
To use different providers, simply uncomment the desired models and update the role assignments:
```python
# Example: Use Claude for analysis, GPT-4 for triage
STATIC_ANALYSIS_ANALYST_LLM = anthropic_claude_3_5_sonnet
STATIC_ANALYSIS_TRIAGE_LLM = openai_4o
```

### LangGraph Configuration
The platform now supports multiple graphs in `langgraph.json`:
```json
{
  "graphs": {
    "pdf_hunter": "./src/pdf_hunter_main/pdf_hunter_graph.py:app",
    "pdf_processing": "./src/pdf_processing/pdf_agent.py:app", 
    "agent": "./src/static_analysis/graph.py:app"
  }
}
```

## Future Roadmap

### 🎯 **Next Phase: Visual Analysis Integration**
- **Visual Deception Analyst**: HCI/UX security expert persona
- **Cross-Modal Analysis**: Compare visual appearance vs. technical reality
- **Psychological Tactics Detection**: Identify social engineering patterns
- **Brand Impersonation Detection**: Automated logo/design analysis

### 🔄 **Platform Enhancements**
- **Parallel Subgraph Execution**: Run extraction and analysis simultaneously
- **Result Caching**: Avoid reprocessing identical files
- **Batch Processing**: Handle multiple PDFs efficiently
- **Custom Analysis Pipelines**: User-configurable workflow composition

## Troubleshooting

### Architecture-Specific Issues

1. **Subgraph Import Errors**: Ensure all modules installed with `pip install -e .`
2. **Schema Validation Failures**: Check input types match Pydantic model requirements
3. **LangGraph Studio Graph Selection**: Use correct graph name (`pdf_hunter`, `pdf_processing`, or `agent`)

### Legacy Compatibility

- **Old static analysis usage**: Still supported via `static_analysis.graph:app`
- **Direct PDF processing**: Available via `pdf_processing.pdf_agent:app`
- **Migration path**: Use `pdf_hunter_main` for new implementations

## Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch from `preprocessing_connections`
3. Follow the composed graph architecture patterns
4. Add comprehensive Pydantic schemas for new components
5. Update relevant module READMEs
6. Submit pull request

### Code Standards
- **Schema-First**: All new components must use Pydantic validation
- **Type Safety**: Full type annotations required
- **Modular Design**: Maintain clean separation between extraction and analysis
- **Documentation**: Update module READMEs for architectural changes

---

**🏗️ Architecture Note**: The platform has evolved from a single-purpose forensic tool to a comprehensive PDF analysis platform. The `preprocessing_connections` branch represents a major architectural advancement with composed graphs, parallel processing, and enhanced type safety. For stability, use `interrogation_node`. For latest features, use `preprocessing_connections`. 