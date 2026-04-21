# AGENTS.md

## Dependencies

```bash
pip install pymupdf
```

## Running

```bash
python enem_parser.py --input <folder-with-PDFs> --output enem.zip --verbose
```

- Input folder must contain `*PV*.pdf` (questions) and `*GB*.pdf` (gabarito/answer key)
- Output: ZIP file with structured JSON in `output/2024/questions/`

## Project Structure

- `enem_parser.py` - CLI entry point
- `parser/extractor.py` - PDF reading, gabarito extraction, language detection
- `parser/transformer.py` - Question JSON building, noise filtering
- `parser/utils.py` - ZIP creation