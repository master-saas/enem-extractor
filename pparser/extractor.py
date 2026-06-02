import fitz
import os
import re

DIMLIMIT = 0
ABSSIZE = 0
RELSIZE = 0


def _recoverpix(doc, item):
    xref = item[0]
    smask = item[1]

    if smask > 0:
        pix0 = fitz.Pixmap(doc.extract_image(xref)["image"])
        if pix0.alpha:
            pix0 = fitz.Pixmap(pix0, 0)
        mask = fitz.Pixmap(doc.extract_image(smask)["image"])

        try:
            pix = fitz.Pixmap(pix0, mask)
        except:
            pix = fitz.Pixmap(doc.extract_image(xref)["image"])

        if pix0.n > 3:
            ext = "pam"
        else:
            ext = "png"

        return {
            "ext": ext,
            "colorspace": pix.colorspace.n,
            "image": pix.tobytes(ext),
        }

    if "/ColorSpace" in doc.xref_object(xref, compressed=True):
        pix = fitz.Pixmap(doc, xref)
        pix = fitz.Pixmap(fitz.csRGB, pix)
        return {
            "ext": "png",
            "colorspace": 3,
            "image": pix.tobytes("png"),
        }
    return doc.extract_image(xref)


def _extract_page_images(doc, page_num, output_dir):
    if page_num == 0:
        return []
    
    total_pages = len(doc)
    if page_num == 18:
        return []
    if page_num >= total_pages - 1:
        return []
    
    page = doc.load_page(page_num)
    images = page.get_images(full=True)
    page_images = []

    MIN_WIDTH = 50
    MIN_HEIGHT = 50
    DIM_LIMIT = 0

    for img in images:
        xref = img[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            continue

        width = img[2]
        height = img[3]
        
        if min(width, height) <= DIM_LIMIT:
            continue

        try:
            image = _recoverpix(doc, img)
        except Exception:
            continue

        n = image["colorspace"]
        imgdata = image["image"]

        if len(imgdata) <= ABSSIZE:
            continue
        if len(imgdata) / (width * height * n) <= RELSIZE:
            continue
        if image["ext"] == "jb2":
            continue

        img_filename = f"img{page_num:05d}_{xref:05d}.png"
        img_path = os.path.join(output_dir, img_filename)

        with open(img_path, "wb") as f:
            f.write(imgdata)

        bbox = None
        if rects:
            r = rects[0]
            bbox = [r.x0, r.y0, r.x1, r.y1]

        page_images.append({
            "xref": xref,
            "width": width,
            "height": height,
            "filename": img_filename,
            "path": img_path,
            "bbox": bbox
        })

    return page_images


def read_pdf(path, img_output_dir=None):
    doc = fitz.open(path)
    pages = []

    for page_num, page in enumerate(doc):
        page_data = page.get_text("dict")
        blocks = page_data["blocks"]

        page_images = []
        if img_output_dir:
            os.makedirs(img_output_dir, exist_ok=True)
            page_images = _extract_page_images(doc, page_num, img_output_dir)

        page_info = {
            "page_num": page_num,
            "width": page.rect.width,
            "height": page.rect.height,
            "blocks": blocks,
            "images": page_images,
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

    # Split by any whitespace but keep non-empty tokens
    tokens = [t.strip() for t in text.split() if t.strip()]

    gabarito = {}
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.isdigit():
            q_num = int(token)
            # Check if this is a language question (1-5)
            if 1 <= q_num <= 5:
                # We expect two answers after it: English and Spanish
                if i + 2 < len(tokens):
                    ans1 = tokens[i+1]
                    ans2 = tokens[i+2]
                    valid_options = {"A", "B", "C", "D", "E", "Anulado"}
                    if ans1 in valid_options and ans2 in valid_options:
                        gabarito[f"{q_num}_ingles"] = ans1
                        gabarito[f"{q_num}_espanhol"] = ans2
                        gabarito[(q_num, "ingles")] = ans1
                        gabarito[(q_num, "espanhol")] = ans2
                        gabarito[q_num] = ans1
                        i += 3
                        continue
            # Otherwise, it's a regular question (or fallback if 1-5 didn't have 2 answers)
            if i + 1 < len(tokens):
                ans = tokens[i+1]
                valid_options = {"A", "B", "C", "D", "E", "Anulado"}
                if ans in valid_options:
                    gabarito[q_num] = ans
                    i += 2
                    continue
        i += 1
    return gabarito


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


def extract_all(input_path, img_output_dir=None):
    if os.path.isfile(input_path):
        all_files = [input_path]
        folder = os.path.dirname(input_path) or "."
    else:
        folder = input_path
        all_files = [os.path.join(folder, f) for f in os.listdir(folder)]

    pv_files = [f for f in all_files if "PV" in os.path.basename(f)]
    gb_files = [f for f in all_files if "GB" in os.path.basename(f)]

    # If no PV/GB markers, treat all PDFs as question files
    if not pv_files and not gb_files:
        pv_files = [f for f in all_files if f.lower().endswith(".pdf")]

    questions_raw = []
    gabarito = {}

    for pv in pv_files:
        pages = read_pdf(pv, img_output_dir)
        questions_raw.extend(pages)

    for gb in gb_files:
        gabarito.update(extract_gabarito(gb))

    english_start, spanish_start = detect_language_sections(questions_raw)

    return {
        "pages": questions_raw,
        "gabarito": gabarito,
        "english_start": english_start,
        "spanish_start": spanish_start
    }