import fitz
import os
import re

def read_pdf(path):
    doc = fitz.open(path)
    pages = []

    for page_num, page in enumerate(doc):
        page_data = page.get_text("dict")
        blocks = page_data["blocks"]
        
        page_info = {
            "page_num": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "blocks": blocks,
            "is_two_column": _detect_column_layout(blocks, page.rect.width)
        }
        pages.append(page_info)

    return pages


def _detect_column_layout(blocks, page_width):
    """Detect if page uses 2 columns based on block x-coordinates"""
    x_positions = []
    
    for block in blocks:
        if block.get("type") == 0:
            x = block.get("bbox", [0, 0, 0, 0])[0]
            if x > 0:
                x_positions.append(x)
    
    if len(x_positions) < 10:
        return True
    
    x_positions.sort()
    median_x = x_positions[len(x_positions) // 2]
    
    left_threshold = page_width * 0.45
    right_threshold = page_width * 0.55
    
    left_count = sum(1 for x in x_positions if x < left_threshold)
    right_count = sum(1 for x in x_positions if x > right_threshold)
    
    if left_count > 3 and right_count > 3:
        return True
    
    return False


def extract_gabarito(path):
    doc = fitz.open(path)
    text = ""

    for page in doc:
        text += page.get_text()

    matches = re.findall(r"(\d+)\s+([A-E])", text)
    return {int(q): a for q, a in matches}


def detect_language_sections(all_pages):
    """Detect page numbers where English and Spanish sections start"""
    english_start = None
    spanish_start = None

    for page_data in all_pages:
        page_text = ""
        for block in page_data.get("blocks", []):
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        page_text += span.get("text", "")

        if "Questões de 01 a 05 (opção inglês)" in page_text:
            english_start = page_data["page_num"]
        if "Questões de 01 a 05 (opção espanhol)" in page_text:
            spanish_start = page_data["page_num"]

    return english_start, spanish_start


def extract_all(folder):
    files = os.listdir(folder)

    pv_files = [f for f in files if "PV" in f]
    gb_files = [f for f in files if "GB" in f]

    questions_raw = []
    gabarito = {}

    for pv in pv_files:
        pages = read_pdf(os.path.join(folder, pv))
        questions_raw.extend(pages)

    for gb in gb_files:
        gabarito.update(extract_gabarito(os.path.join(folder, gb)))

    english_start, spanish_start = detect_language_sections(questions_raw)

    return {
        "pages": questions_raw,
        "gabarito": gabarito,
        "english_start": english_start,
        "spanish_start": spanish_start
    }