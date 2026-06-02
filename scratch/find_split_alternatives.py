import fitz
import re

pdf_files = [
    "input/2025_PV_impresso_D1_CD2.pdf",
    "input/2025_PV_impresso_D2_CD5.pdf"
]

Q_PATTERN = re.compile(r'^QUEST[ÃÃã]O\s+(\d+)', re.IGNORECASE)

for filepath in pdf_files:
    doc = fitz.open(filepath)
    print(f"\nAnalyzing {filepath}:")
    
    current_q = None
    q_blocks = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b.get("type") == 0:
                lines = ["".join(span["text"] for span in line.get("spans", [])) for line in b.get("lines", [])]
                full_text = "\n".join(lines).strip()
                match = Q_PATTERN.match(full_text)
                if match:
                    current_q = int(match.group(1))
                    q_blocks[current_q] = []
                if current_q is not None:
                    q_blocks[current_q].append(full_text)
                    
    # For each question, check if it has a block containing A, B, C, D, E
    for q, blocks_list in sorted(q_blocks.items()):
        found_grouped = False
        for text in blocks_list:
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            has_all = True
            for letter in "ABCDE":
                if not any(l.startswith(f"{letter} ") or l.startswith(f"{letter}\t") for l in lines):
                    has_all = False
                    break
            if has_all:
                found_grouped = True
                break
        if not found_grouped:
            print(f"  Questão {q}: Alternatives are NOT in a single block!")
