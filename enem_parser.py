import argparse
import os
from parser.extractor import extract_all
from parser.transformer import build_output, set_verbose
from parser.utils import zip_output

def main():
    parser = argparse.ArgumentParser(description="ENEM PDF → Structured ZIP")

    parser.add_argument("--input", required=True, help="Folder with PDFs")
    parser.add_argument("--output", default="enem.zip", help="Output zip file")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Show execution logs")

    args = parser.parse_args()

    set_verbose(args.verbose)

    print("Extracting PDF data...")
    data = extract_all(args.input)

    print("Converting to ENEM structure...")
    output_dir = build_output(data)

    print("Creating ZIP...")
    zip_output(output_dir, args.output)

    print(f"Done: {args.output}")

if __name__ == "__main__":
    main()