import fitz
import re

def inspect_question(filepath, q_num, out_file):
    doc = fitz.open(filepath)
    Q_PATTERN = re.compile(r'^QUEST[ÃÃã]O\s+(\d+)', re.IGNORECASE)
    
    current_q = None
    blocks_list = []
    
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
                    if current_q == q_num:
                        blocks_list = []
                if current_q == q_num:
                    blocks_list.append((b, full_text))
            elif b.get("type") == 1 and current_q == q_num:
                blocks_list.append((b, "[IMAGE]"))
                
    out_file.write(f"\n=== INSPECTING Q{q_num} IN {filepath} ===\n")
    for idx, (b, text) in enumerate(blocks_list):
        out_file.write(f"Block {idx}: bbox={[round(x, 1) for x in b.get('bbox')]} Type={b.get('type')}\n")
        out_file.write(f"--- Content ---\n{text}\n---------------\n")

with open("scratch/inspect_output.txt", "w", encoding="utf-8") as f:
    inspect_question("input/2025_PV_impresso_D2_CD5.pdf", 164, f)
    inspect_question("input/2024_PV_impresso_D2_CD5.pdf", 169, f)
print("Done writing to scratch/inspect_output.txt")
