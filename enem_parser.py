import argparse
import os
import re
import shutil
from pparser.extractor import extract_all
from pparser.transformer import build_output, set_verbose, set_year

def detect_year(input_path):
    if os.path.isfile(input_path):
        candidates = [os.path.basename(input_path)]
    else:
        candidates = os.listdir(input_path) if os.path.isdir(input_path) else []
        candidates.append(os.path.basename(input_path))
    for name in candidates:
        m = re.search(r'(20\d{2})', name)
        if m:
            return int(m.group(1))
    return 2024

def main():
    parser = argparse.ArgumentParser(description="ENEM PDF → Structured folder")
    parser.add_argument("--input", required=True, help="PDF file or folder with PDFs")
    parser.add_argument("--output", default="result", help="Output folder")
    parser.add_argument("--verbose", "-v", action="store_true", default=False)
    args = parser.parse_args()

    year = detect_year(args.input)
    set_year(year)
    set_verbose(args.verbose)

    import pparser.transformer as t
    img_output_dir = os.path.join(t.BASE_DIR, "images")

    print(f"Year: {year}")
    print("Extracting PDF data...")
    data = extract_all(args.input, img_output_dir)

    print("Converting to ENEM structure...")
    output_dir = build_output(data)
    print(f"Saving to {args.output}...")
    if os.path.exists(args.output):
        if os.path.isdir(args.output):
            shutil.rmtree(args.output)
        else:
            os.remove(args.output)

    if args.output.endswith(".zip"):
        from pparser.utils import zip_output
        zip_output(output_dir, args.output)
        print(f"Done: {args.output}")
    else:
        shutil.copytree(output_dir, os.path.join(args.output, str(year)))
        print(f"Done: {args.output}/{year}/")

if __name__ == "__main__":
    main()