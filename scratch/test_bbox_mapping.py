import fitz

doc = fitz.open("input/2025_PV_impresso_D2_CD5.pdf")
page = doc[4] # Page 4

print("=== IMAGES FROM get_images() ===")
for img in page.get_images(full=True):
    xref = img[0]
    rects = page.get_image_rects(xref)
    print(f"xref={xref}: rects={[[round(coord, 1) for coord in rect] for rect in rects]}")

print("\n=== BLOCKS FROM get_text('dict') ===")
blocks = page.get_text("dict")["blocks"]
for idx, b in enumerate(blocks):
    if b.get("type") == 1:
        bbox = b.get("bbox")
        print(f"Block {idx} (type=1): bbox={[round(coord, 1) for coord in bbox]}")
    elif b.get("type") == 0:
        # print first line of text
        lines = b.get("lines", [])
        if lines:
            text = "".join(span["text"] for span in lines[0].get("spans", []))
            if "QUESTÃO" in text.upper():
                print(f"Block {idx} (type=0): {text.strip()} bbox={[round(coord, 1) for coord in b.get('bbox')]}")
