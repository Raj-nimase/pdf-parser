import sys
import os
from pathlib import Path

# Add app directory to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.deterministic_math_converter import convert_markdown_file

def main():
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        # Default input file in workspace root
        input_file = os.path.join(os.path.dirname(__file__), "..", "attention_is_all_you_need_extracted.md")

    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else:
        output_file = input_file

    input_path = os.path.abspath(input_file)
    output_path = os.path.abspath(output_file)

    print(f"[DeterministicMathConverter] Reading: {input_path}")
    convert_markdown_file(input_path, output_path)
    print(f"[DeterministicMathConverter] Wrote math-converted LaTeX output to: {output_path}")

if __name__ == "__main__":
    main()
