import fitz
doc = fitz.open("input/2025_PV_impresso_D2_CD5.pdf")
page = doc[3]
with open("scratch/page3_output.txt", "w", encoding="utf-8") as f:
    f.write("=== PAGE 3 ===\n")
    blocks = page.get_text("dict")["blocks"]
    for idx, b in enumerate(blocks):
        if b.get("type") == 0:
            lines = []
            for line in b.get("lines", []):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                lines.append(line_text)
            full_block = "\n".join(lines)
            f.write(f"Block {idx}: bbox={[round(x, 1) for x in b.get('bbox')]}\n")
            f.write(f"--- Content ---\n{full_block}\n---------------\n")
print("Wrote page 3 output to scratch/page3_output.txt")
