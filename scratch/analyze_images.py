import fitz
import os

pdf_files = [
    "input/2025_PV_impresso_D1_CD2.pdf",
    "input/2025_PV_impresso_D2_CD5.pdf"
]

for filepath in pdf_files:
    if not os.path.exists(filepath):
        print(f"File {filepath} does not exist.")
        continue
    doc = fitz.open(filepath)
    print(f"\nAnalyzing {filepath} (total pages: {len(doc)}):")
    for page_num in range(len(doc)):
        page = doc[page_num]
        images = page.get_images(full=True)
        blocks = page.get_text("dict")["blocks"]
        type1_blocks = [b for b in blocks if b.get("type") == 1]
        type0_blocks = [b for b in blocks if b.get("type") == 0]
        if len(images) > 0 or len(type1_blocks) > 0:
            print(f"  Page {page_num:02d}: get_images() count = {len(images)}, type=1 blocks count = {len(type1_blocks)}")
