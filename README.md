# ENEM Extractor

Extracts ENEM (Exame Nacional do Ensino Médio) PDF question sheets and answer keys into structured JSON.

## Installation

```bash
pip install pymupdf
```

## Usage

```bash
python enem_parser.py --input <folder> --output enem.zip --verbose
```

### CLI Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `--input` | Yes | - | Path to folder containing PDFs |
| `--output` | No | `enem.zip` | Output ZIP file path |
| `--verbose`, `-v` | No | `false` | Show execution logs |

## Input Requirements

The input folder must contain:

- `*PV*.pdf` - Question sheets (Prova)
- `*GB*.pdf` - Answer key (Gabarito)

Example (from 2024 ENEM):
```
input/
├── 2024_PV_impresso_D1_CD2.pdf   # Day 1 questions
├── 2024_PV_impresso_D2_CD5.pdf   # Day 2 questions
├── 2024_GB_impresso_D1_CD2.pdf   # Day 1 answer key
└── 2024_GB_impresso_D2_CD5.pdf   # Day 2 answer key
```

Filename pattern: `YYYY_PV_impresso_D[N]_[CODE].pdf` for questions, `YYYY_GB_impresso_D[N]_[CODE].pdf` for gabarito.

## Output

Creates a ZIP file containing structured JSON in `output/2024/questions/`:

```
output/
├── 2024/
│   ├── details.json          # Index with all questions, disciplines, languages
│   └── questions/
│       ├── 1-ingles/
│       │   └── details.json
│       ├── 1-espanhol/
│       │   └── details.json
│       ├── 2/
│       │   └── details.json
│       ...
```

### Question JSON Schema

```json
{
  "title": "Questão 1 - ENEM 2024",
  "index": 1,
  "year": 2024,
  "language": "ingles" | "espanhol" | null,
  "discipline": "linguagens" | "ciencias-humanas" | "ciencias-natureza" | "matematica",
  "context": "Question text with images marked as ![](img)",
  "files": ["![](img)"],
  "correctAlternative": "A",
  "alternativesIntroduction": "Intro text before alternatives",
  "alternatives": [
    {"letter": "A", "text": "...", "file": null, "isCorrect": true},
    {"letter": "B", "text": "...", "file": null, "isCorrect": false},
    ...
  ]
}
```

### Details Index Schema

```json
{
  "title": "ENEM 2024",
  "year": 2024,
  "disciplines": [
    {"label": "Ciências Humanas e suas Tecnologias", "value": "humanas"},
    {"label": "Ciências da Natureza e suas Tecnologias", "value": "ciencias-natureza"},
    {"label": "Linguagens, Códigos e suas Tecnologias", "value": "linguagens"},
    {"label": "Matemática e suas Tecnologias", "value": "matematica"}
  ],
  "languages": [
    {"label": "Espanhol", "value": "espanhol"},
    {"label": "Inglês", "value": "ingles"}
  ],
  "questions": [
    {"title": "Questão 1 - ENEM 2024", "index": 1, "discipline": "linguagens", "language": "ingles"},
    ...
  ]
}
```

## Project Structure

```
enem-extractor/
├── enem_parser.py          # CLI entry point
├── parser/
│   ├── extractor.py     # PDF reading, gabarito extraction, language detection
│   ├── transformer.py   # Question JSON building, noise filtering
│   └── utils.py         # ZIP creation
└── output/              # Generated output (gitignored)
```

## Discipline Mapping

Questions are mapped by number:

| Question Range | Discipline |
|----------------|------------|
| 1-45 | Linguagens |
| 46-90 | Ciências Humanas |
| 91-135 | Ciências da Natureza |
| 136-180 | Matemática |

## Language Variants

Questions 1-5 have both English and Spanish variants. The parser detects these based on page markers:
- "Questões de 01 a 05 (opção inglês)" → English
- "Questões de 01 a 05 (opção espanhol)" → Spanish

## Noise Filtering

The transformer filters common PDF artifacts as noise (headers, footers, page numbers, subject labels, etc.). Run with `--verbose` to see filtered blocks in `output/2024/parser_log.txt`.