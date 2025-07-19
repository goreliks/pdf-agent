import hashlib
import re
from typing import List
import subprocess
import os
import sys
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser


import json
import subprocess
import sys
import os
import base64
from typing import List, Dict, Any
from pydantic import BaseModel
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import PydanticOutputParser

from static_analysis.schemas import ToolCallLog

# --- LLM Helper ---

def create_llm_chain(system_prompt: str, human_prompt: str, response_model: BaseModel, llm):
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
    # llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Create chain: prompt -> llm -> parser
    return prompt | llm | parser


def _extract_hex_from_string_tool(input_string: str) -> Dict[str, Any]:
    """Extracts a hexadecimal string from a line of text, removing delimiters."""
    # This regex finds hex strings that are often inside <...>
    match = re.search(r'<([a-fA-F0-9]+)>', input_string)
    if match:
        return {"stdout": match.group(1), "stderr": "", "return_code": 0}
    
    # Fallback for hex strings not in brackets
    match = re.search(r'[a-fA-F0-9]{40,}', input_string)
    if match:
        return {"stdout": match.group(0), "stderr": "", "return_code": 0}

    return {"stdout": "", "stderr": "ERROR: No hexadecimal string found.", "return_code": 1}


def _run_shell_command(command: List[str]) -> Dict[str, Any]:
    """A centralized, safe function to run shell commands and return structured output."""
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            encoding='utf-8',
            errors='ignore' # Ignore errors for weird binary output
        )
        return {
            "stdout": process.stdout.strip(),
            "stderr": process.stderr.strip(),
            "return_code": process.returncode
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "ERROR: Command timed out.", "return_code": -1}
    except FileNotFoundError:
        return {"stdout": "", "stderr": f"ERROR: Executable '{command[0]}' not found.", "return_code": -1}
    except Exception as e:
        return {"stdout": "", "stderr": f"ERROR: An unexpected error occurred: {e}", "return_code": -1}

def _base64_decode_tool(input_string: str) -> Dict[str, Any]:
    """A safe Python function to act as a tool, returning structured output."""
    try:
        # Remove potential newlines or whitespace
        cleaned_string = "".join(input_string.split())
        decoded_bytes = base64.b64decode(cleaned_string)
        # Try to decode as UTF-8 for readability, fall back to hex representation
        try:
            stdout = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            stdout = decoded_bytes.hex()
        return {"stdout": stdout, "stderr": "", "return_code": 0}
    except Exception as e:
        return {"stdout": "", "stderr": f"ERROR: Failed to decode Base64 string: {e}", "return_code": 1}

def _decode_hex_string_tool(input_string: str) -> Dict[str, Any]:
    """A safe Python function to decode a hex string."""
    try:
        cleaned_string = "".join(input_string.split())
        if len(cleaned_string) % 2 != 0:
            return {"stdout": "", "stderr": "ERROR: Hex string must have an even number of characters.", "return_code": 1}
        
        decoded_bytes = bytes.fromhex(cleaned_string)
        try:
            stdout = decoded_bytes.decode('utf-8')
        except UnicodeDecodeError:
            stdout = "Decoded binary content (non-UTF-8), showing hex representation: " + decoded_bytes.hex()
        return {"stdout": stdout, "stderr": "", "return_code": 0}
    except ValueError:
        return {"stdout": "", "stderr": "ERROR: Input contains non-hexadecimal characters.", "return_code": 1}
    except Exception as e:
        return {"stdout": "", "stderr": f"ERROR: Failed to decode hex string: {e}", "return_code": 1}


class ToolExecutor:
    """
    Loads the tool manifest and provides a safe, centralized way
    to execute the defined tools, returning a structured log.
    """
    def __init__(self, manifest: List[Dict[str, Any]]):
        self._tools = {tool['tool_name']: tool for tool in manifest}
        self._python_functions = {
            "base64_decode": _base64_decode_tool,
            "decode_hex_string": _decode_hex_string_tool,
            "extract_hex_from_string": _extract_hex_from_string_tool
        }

    def run(self, tool_name: str, arguments: Dict[str, Any]) -> ToolCallLog:
        if tool_name not in self._tools:
            return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str="", stdout="", stderr=f"ERROR: Tool '{tool_name}' not found in manifest.", return_code=-1)

        tool_def = self._tools[tool_name]
        command_str = f"{tool_name}({json.dumps(arguments)})" # Default for logging

        if tool_def.get("is_python_function"):
            func = self._python_functions.get(tool_name)
            if not func:
                return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str=command_str, stdout="", stderr=f"ERROR: Python function for tool '{tool_name}' not implemented.", return_code=-1)
            
            result = func(**arguments)
            return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str=command_str, **result)
        
        # Handle shell commands
        command_template = tool_def.get("command_template")
        if not command_template:
            return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str="", stdout="", stderr=f"ERROR: No command_template defined for tool '{tool_name}'.", return_code=-1)
            
        try:
            command_str_formatted = command_template.format(**arguments)
            # Use shlex for safer splitting, though simple split is fine for our templates
            command_parts = command_str_formatted.split() 
        except KeyError as e:
            return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str="", stdout="", stderr=f"ERROR: Missing required argument '{e}' for tool '{tool_name}'.", return_code=-1)
        except Exception as e:
            return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str="", stdout="", stderr=f"ERROR: Failed to format command for tool '{tool_name}': {e}", return_code=-1)

        result = _run_shell_command(command_parts)

        # This block checks if the dump tool ran successfully. If so, it creates our custom confirmation message for the Analyst agent to see.
        if tool_name == "dump_filtered_stream" and result["return_code"] == 0:
            object_id = arguments.get("object_id")
            output_file = arguments.get("output_file")
            result["stdout"] = f"Successfully dumped stream from object {object_id} to file: {output_file}"

        return ToolCallLog(tool_name=tool_name, arguments=arguments, command_str=command_str_formatted, **result)


def run_pdfid(pdf_filename: str) -> str:
    """Runs the pdfid.py tool with the correct flags."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Tools are in a subdirectory of the current module
    tools_dir = os.path.join(script_dir, "tools")
    pdfid_path = os.path.join(tools_dir, "pdfid.py")
    
    if not os.path.exists(pdfid_path):
        print(f"Warning: pdfid.py not found at {pdfid_path}. Using simulation.")
        raise FileNotFoundError(f"pdfid.py not found at {pdfid_path}")
        #         return "/OpenAction -> /oPENaCTION\n..."


    command_parts = [sys.executable, pdfid_path, "-e", "-f", pdf_filename]
    result = _run_shell_command(command_parts)
    return result['stdout'] or f"Tool executed with no output. Stderr: {result['stderr']}"


def run_pdf_parser_full_statistical_analysis(pdf_filename: str) -> str:
    """Runs the pdf-parser.py tool with -a flag."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Tools are in a subdirectory of the current module
    tools_dir = os.path.join(script_dir, "tools")
    pdf_parser_path = os.path.join(tools_dir, "pdf-parser.py")

    command_parts = [sys.executable, pdf_parser_path, "-a", "-O",pdf_filename]
    result = _run_shell_command(command_parts)
    return result['stdout'] or f"Tool executed with no output. Stderr: {result['stderr']}"


def get_file_hash(file_path: str) -> str:
    print(f"[*] SIMULATING hash calculation for: {file_path}")
    sha256_hash = hashlib.sha256()
    sha256_hash.update(file_path.encode('utf-8'))
    return sha256_hash.hexdigest()


def run_pdfid_simulation(file_path: str) -> str:
    print(f"[*] SIMULATING 'pdfid' on: {file_path}")
    return """
 PDF Header: %PDF-1.4
 obj                  10
 endobj                9
 stream                3
 endstream             3
 xref                  1
 trailer               1
 startxref             1
 /Page                 1
 /Encrypt              0
 /JS                   2
 /JavaScript           2
 /AA                   1
 /OpenAction           1
 /AcroForm             0
 /JBIG2Decode          0
 /RichMedia            0
 /Launch               1
 /EmbeddedFile         0
 /XFA                  0
 /Colors > 2^24        0
    """


def run_tool_simulation(tool_name: str, arguments: List[str], file_path: str) -> str:
    """Simulates running a command-line tool."""
    command = f"{tool_name} {' '.join(arguments)} {file_path}"
    print(f"[*] SIMULATING TOOL EXECUTION: `{command}`")
    if tool_name == "pdf-parser.py" and "--search" in arguments and "/OpenAction" in arguments:
        # Simulate finding the object ID for /OpenAction
        return """obj 6 0
  <<
    /Type /Catalog
    /Pages 3 0 R
    /OpenAction 7 0 R
  >>
"""
    return f"Simulated output for command: {command}"
