import fitz
import os
import re

pdf_files = [
    "input/2025_PV_impresso_D1_CD2.pdf",
    "input/2025_PV_impresso_D2_CD5.pdf"
]

Q_PATTERN = re.compile(r'^QUEST[ÃÃã]O\s+(\d+)', re.IGNORECASE)

def get_bbox_overlap(bbox1, bbox2):
    x0 = max(bbox1[0], bbox2[0])
    y0 = max(bbox1[1], bbox2[1])
    x1 = min(bbox1[2], bbox2[2])
    y1 = min(bbox1[3], bbox2[3])
    
    if x1 <= x0 or y1 <= y0:
        return 0.0
        
    intersect_area = (x1 - x0) * (y1 - y0)
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    
    if area1 <= 0 or area2 <= 0:
        return 0.0
        
    return intersect_area / min(area1, area2)

for filepath in pdf_files:
    if not os.path.exists(filepath):
        continue
    doc = fitz.open(filepath)
    print(f"\n=========================================\nTesting {filepath}\n=========================================")
    
    current_q = None
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Get page images
        page_images = []
        for img in page.get_images(full=True):
            xref = img[0]
            try:
                rects = page.get_image_rects(xref)
                if rects:
                    r = rects[0]
                    page_images.append({
                        "xref": xref,
                        "bbox": [r.x0, r.y0, r.x1, r.y1],
                        "width": img[2],
                        "height": img[3]
                    })
            except Exception:
                continue
                
        # 2. Get blocks
        blocks = page.get_text("dict")["blocks"]
        
        # We want to trace question transitions and see where images map
        for block in blocks:
            if block.get("type") == 0:
                # text block
                lines = block.get("lines", [])
                text_lines = []
                for line in lines:
                    text_lines.append("".join(span["text"] for span in line.get("spans", [])))
                full_text = "\n".join(text_lines).strip()
                
                match = Q_PATTERN.match(full_text)
                if match:
                    current_q = int(match.group(1))
                    
            elif block.get("type") == 1:
                # image block
                bbox = block.get("bbox")
                # Find matching extracted image
                best_overlap = 0.0
                best_img = None
                for img in page_images:
                    overlap = get_bbox_overlap(bbox, img["bbox"])
                    if overlap > best_overlap:
                        best_overlap = overlap
                        best_img = img
                
                if best_img and best_overlap > 0.5:
                    print(f"Page {page_num:02d}: Block bbox {[round(coord, 1) for coord in bbox]} matches image xref {best_img['xref']} (overlap {best_overlap:.2f}) -> QUESTÃO {current_q}")
                else:
                    pass # ignore decorative type=1 blocks
