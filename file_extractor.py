import os

def get_all_python_files(directory: str):
    python_files = []
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith(".py"):
                full_path = os.path.join(root, file)
                python_files.append(full_path)
    return python_files

def extract_code_from_file(filepath: str) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"# Failed to read {filepath}: {e}"

def extract_all_code_with_headers(directory: str) -> str:
    python_files = get_all_python_files(directory)
    output = []

    for path in python_files:
        code = extract_code_from_file(path)
        header = f"{'#' * 80}\n# FILE: {path}\n{'#' * 80}\n"
        output.append(header + code + "\n\n")

    return "\n".join(output)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract Python code with file headers.")
    parser.add_argument("directory", help="Directory to search for Python files")
    parser.add_argument("--output", help="File to save the output", default="extracted_code.txt")
    args = parser.parse_args()

    final_output = extract_all_code_with_headers(args.directory)

    with open(args.output, "w", encoding="utf-8") as out_file:
        out_file.write(final_output)

    print(f"✅ Python code extracted and saved to {args.output}")

