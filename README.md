# PDF Agent - Forensic PDF Analysis Tool

A LangGraph-powered forensic analysis tool for PDF documents that combines traditional static analysis with LLM-powered threat assessment.

## Features

- 🔍 **Static PDF Analysis**: Uses `pdfid` and custom tools to extract PDF structure
- 🤖 **LLM-Powered Triage**: GPT-4 integration for intelligent threat assessment
- 📊 **Forensic Workflow**: Structured investigation pipeline with evidence tracking
- 🔗 **LangGraph Integration**: Visual workflow management and execution
- 📝 **Comprehensive Reporting**: Detailed analysis trails and findings

## Installation

### Prerequisites

- Python 3.10 or higher
- OpenAI API key (for LLM features)

### Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd pdf-agent
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
# Run analysis on a PDF file
pdf-agent

# Or run directly with Python
python -m static_analysis.graph
```

### LangGraph Studio

The project includes LangGraph configuration for visual workflow management:

```bash
langgraph dev
```

### Programmatic Usage

```python
from static_analysis.graph import app
from static_analysis.schemas import ForensicCaseFileInput

# Analyze a PDF
inputs = ForensicCaseFileInput(file_path="path/to/suspicious.pdf")
result = app.invoke(inputs.model_dump())
print(result)
```

## Project Structure

```
pdf-agent/
├── src/
│   └── static_analysis/          # Main package
│       ├── graph.py             # LangGraph workflow definition
│       ├── schemas.py           # Pydantic models and data structures
│       ├── prompts.py           # LLM prompt templates
│       ├── utils.py             # Utility functions
│       ├── test_run.py          # Testing utilities
│       └── tools/               # Analysis tools
│           ├── pdf-parser.py    # PDF parsing utilities
│           └── pdfid.py         # PDF structure analysis
├── tests/                       # Test files and data
├── notebooks/                   # Jupyter notebooks for development
├── langgraph.json              # LangGraph configuration
├── pyproject.toml              # Project configuration
└── requirements.txt            # Dependencies
```

## Development

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
2. Create a feature branch
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

## License

[Add your license information here]

## Security Notice

This tool is designed for security research and forensic analysis. Always analyze suspicious PDFs in a controlled, isolated environment.

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you've installed the package with `pip install -e .`
2. **OpenAI API Issues**: Verify your API key is set in the `.env` file
3. **PDF Analysis Failures**: Check that the PDF file exists and is readable

### Getting Help

- Check the [Issues](issues) page for known problems
- Review the [Documentation](docs) for detailed usage guides
- Join our [Discussions](discussions) for community support 