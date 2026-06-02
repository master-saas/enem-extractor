import fitz

doc = fitz.open("input/2025_PV_impresso_D1_CD2.pdf")
page = doc[4] # PAGE 4 (0-indexed is page 4, which is 5th page)
page_data = page.get_text("dict")
blocks = page_data["blocks"]
print("Total blocks on page 4:", len(blocks))
for idx, block in enumerate(blocks):
    btype = block.get("type")
    bbox = block.get("bbox")
    print(f"Block {idx}: type={btype}, bbox={[round(x, 1) for x in bbox]}")
    if btype == 0:
        lines = []
        for line in block["lines"]:
            lines.append("".join(span["text"] for span in line["spans"]))
        print("  Text:", " | ".join(lines[:3]))
