import fitz
import re

doc = fitz.open("input/2025_PV_impresso_D1_CD2.pdf")
for page_num in range(len(doc)):
    page = doc[page_num]
    blocks = page.get_text("dict")["blocks"]
    for idx, b in enumerate(blocks):
        if b.get("type") == 0:
            lines = ["".join(span["text"] for span in line.get("spans", [])) for line in b.get("lines", [])]
            # Check if there is any line starting with A, and if there are subsequent lines starting with B, C, D, E
            full_text = "\n".join(lines).strip()
            lines_stripped = [l.strip() for l in lines if l.strip()]
            if len(lines_stripped) >= 5:
                # check if there are lines starting with A, B, C, D, E (with space or tab)
                starts = [l[0] for l in lines_stripped if len(l) > 1 and l[0] in "ABCDE"]
                # Check if A, B, C, D, E appear in order
                sequence = []
                for l in lines_stripped:
                    if len(l) > 1 and l[0] in "ABCDE" and (l[1] == " " or l[1] == "\t"):
                        if not sequence or (ord(l[0]) == ord(sequence[-1]) + 1):
                            if l[0] not in sequence:
                                sequence.append(l[0])
                if len(sequence) == 5 and sequence == ["A", "B", "C", "D", "E"]:
                    print(f"Page {page_num}, Block {idx}: Found full sequence in single block!")
                    print(f"Sample: {lines_stripped[0][:30]} ... {lines_stripped[-1][:30]}")
