# PDF Agent - Forensic PDF Analysis Tool

A LangGraph-powered forensic analysis tool for PDF documents that combines traditional static analysis with LLM-powered threat assessment. 

**🚀 Current Status**: Active development on `interrogation_node` branch with a complete multi-node forensic investigation workflow.

## Features

- 🔍 **Enhanced Static Analysis**: Uses both `pdfid` and `pdf-parser` for comprehensive PDF structure analysis
- 🤖 **LLM-Powered Investigation**: GPT-4 integration with "Dr. Evelyn Reed" forensic pathologist persona
- 📊 **Complete Forensic Workflow**: Multi-node investigation pipeline with triage → interrogation → strategic review → finalization
- 🔗 **LangGraph Integration**: Visual workflow management and real-time execution monitoring
- 📝 **Comprehensive Evidence Tracking**: Advanced artifact cataloging with file dump support
- 🛡️ **Vendor-Agnostic LLM**: Compatible with any LLM provider via PydanticOutputParser
- 📋 **Detailed Reporting**: Structured analysis trails and comprehensive findings reports

## Recent Enhancements

### Enhanced Triage Analysis
- **Dual Analysis Engine**: Combines `pdfid` structure analysis with `pdf-parser` statistical analysis
- **Richer Context**: Provides comprehensive initial assessment for better hypothesis formation
- **Improved Evidence Collection**: Enhanced evidence locker with multiple analysis sources

### Advanced Artifact Management
- **Unique Artifact IDs**: Each extracted element gets tracked with unique identifiers
- **File Dump Integration**: Automatic dumping and cataloging of decoded stream content
- **Flexible References**: Artifacts can reference both in-memory content and saved files
- **Task-Artifact Linking**: Investigation tasks can target specific artifacts from evidence locker

### Streamlined Tool Framework
- **Focused Tool Set**: Optimized collection of PDF analysis tools for common forensic workflows
- **Diagnostic Capabilities**: Specialized tools for handling compressed/hidden objects
- **Safe Execution**: Comprehensive error handling and logging for all tool operations

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (for LLM features)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pdf-agent
   # Switch to the active development branch
   git checkout interrogation_node
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -e .
   # OR for development:
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

## Usage

### Command Line

```bash
# Run complete forensic analysis on a PDF file
pdf-agent

# Or run directly with Python
python -m static_analysis.graph
```

### LangGraph Studio

The project includes LangGraph configuration for visual workflow management:

```bash
langgraph dev
```

This opens a web interface where you can:
- Visualize the complete investigation workflow
- Monitor real-time execution progress
- Inspect state transitions and decision points
- Debug investigation logic

### Programmatic Usage

```python
from static_analysis.graph import app
from static_analysis.schemas import ForensicCaseFileInput

# Analyze a PDF with complete forensic workflow
inputs = ForensicCaseFileInput(file_path="path/to/suspicious.pdf")

# Stream execution for real-time monitoring
for event in app.stream(inputs.model_dump()):
    for node_name, state_update in event.items():
        print(f"--- Node '{node_name}' completed ---")
        # Full state available in state_update

# Or get final result directly
result = app.invoke(inputs.model_dump())
print(result)
```

## Investigation Workflow

The tool implements a complete forensic investigation pipeline:

1. **Triage Node**: Enhanced dual analysis using pdfid + pdf-parser statistics
2. **Interrogation Node**: Dynamic tool selection and execution based on LLM decisions
3. **Strategic Review Node**: Investigation plan optimization and evidence assessment
4. **Conditional Router**: Intelligent continuation/termination decisions
5. **Finalize Node**: Comprehensive report generation and evidence compilation

## Project Structure

```
pdf-agent/
├── src/
│   └── static_analysis/          # Main package
│       ├── graph.py             # LangGraph workflow definition
│       ├── schemas.py           # Pydantic models and data structures
│       ├── prompts.py           # LLM prompt templates and tool manifest
│       ├── utils.py             # Utility functions and tool execution
│       ├── test_run.py          # Testing utilities
│       └── tools/               # Analysis tools
│           ├── pdf-parser.py    # PDF parsing utilities (Didier Stevens)
│           └── pdfid.py         # PDF structure analysis (Didier Stevens)
├── tests/                       # Test files and malicious PDF samples
├── notebooks/                   # Jupyter notebooks for development
├── langgraph.json              # LangGraph configuration
├── pyproject.toml              # Project configuration
└── requirements.txt            # Dependencies
```

## Development

### Development Branch

Active development occurs on the `interrogation_node` branch:
- Latest features and improvements
- Multi-node workflow implementation
- Enhanced artifact handling
- Comprehensive testing

### Installing Development Dependencies

```bash
pip install -e ".[dev]"
```

### Code Quality

The project uses standard Python development tools:

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **pytest**: Testing

### Contributing

1. Fork the repository
2. Create a feature branch from `interrogation_node`
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Required for LLM-powered analysis
- `PDFPARSER_OPTIONS`: Optional global options for PDF parser

### LangGraph Configuration

The `langgraph.json` file configures the workflow:

```json
{
    "dependencies": ["."],
    "graphs": {
      "agent": "./src/static_analysis/graph.py:app"
    },
    "env": ".env"
}
```

### Analysis Reports

The tool generates comprehensive JSON reports containing:
- Complete investigation timeline
- Evidence locker with all artifacts
- Tool execution logs
- Final assessment and recommendations

## Security Notice

This tool is designed for security research and forensic analysis. Always analyze suspicious PDFs in a controlled, isolated environment:

- Use dedicated analysis VMs
- Never execute extracted content
- Treat all PDF analysis as forensic evidence collection
- Use provided test samples for development

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you've installed the package with `pip install -e .`
2. **OpenAI API Issues**: Verify your API key is set in the `.env` file
3. **PDF Analysis Failures**: Check that the PDF file exists and is readable
4. **Tool Path Issues**: Verify PDF analysis tools are present in `src/static_analysis/tools/`

### Development Support

- Check the [CLAUDE.md](CLAUDE.md) file for detailed development guidance
- Review the [Issues](issues) page for known problems
- Join our [Discussions](discussions) for community support

## License

[Add your license information here]

---

**Note**: This project is under active development. The `interrogation_node` branch contains the latest features and improvements. For stable releases, check the `master` branch. 