import subprocess
import os
import sys

# Get the path to the pdfid.py script relative to this file
script_dir = os.path.dirname(os.path.abspath(__file__))
pdfid_path = os.path.join(script_dir, "tools", "pdfid.py")


def run_pdfid(pdf_filename: str):
    command_parts = [sys.executable, pdfid_path, "-d", "-f", pdf_filename]
    result = subprocess.run(command_parts, capture_output=True, text=True, timeout=60, check=False, env=os.environ.copy())
    pdfid_output = result.stdout
    return pdfid_output

if __name__ == "__main__":

    run_pdfid("tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf")

    # # Test 1: Show help to demonstrate the script is working
    # print("=== Testing pdfid.py help ===")
    # command_parts = [sys.executable, pdfid_path, "--help"]
    # result = subprocess.run(command_parts, capture_output=True, text=True, timeout=60, check=False, env=os.environ.copy())
    # print("Return code:", result.returncode)
    # print("STDOUT:", result.stdout)
    # if result.stderr:
    #     print("STDERR:", result.stderr)

    # print("\n" + "="*50 + "\n")

    # # Test 2: Example with actual PDF file from tests directory
    # print("=== Testing with PDF file from tests directory ===")
    # pdf_filename = "tests/87c740d2b7c22f9ccabbdef412443d166733d4d925da0e8d6e5b310ccfc89e13.pdf"
    # command_parts = [sys.executable, pdfid_path, "-d", "-f",pdf_filename]

    # # Get project root directory (two levels up from this script)
    # project_root = os.path.dirname(os.path.dirname(script_dir))
    # result = subprocess.run(command_parts, capture_output=True, text=True, timeout=60, check=False, env=os.environ.copy(), cwd=project_root)
    # print("Return code:", result.returncode)
    # print("STDOUT:", result.stdout)
    # if result.stderr:
    #     print("STDERR:", result.stderr)

    # print("\n=== Usage Notes ===")
    # print("✅ pdfid.py is now accessible via subprocess!")
    # print("📝 To use with an actual PDF file:")
    # print("   1. Place your PDF file in the project directory")
    # print("   2. Replace the pdf_filename variable with your actual PDF filename")
    # print("   3. The script will analyze the PDF structure and show statistics")