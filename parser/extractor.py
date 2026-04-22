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
            page.get_image_rects(xref)
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

        page_images.append({
            "xref": xref,
            "width": width,
            "height": height,
            "filename": img_filename,
            "path": img_path
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


def extract_all(folder, img_output_dir=None):
    files = os.listdir(folder)

    pv_files = [f for f in files if "PV" in f]
    gb_files = [f for f in files if "GB" in f]

    questions_raw = []
    gabarito = {}

    for pv in pv_files:
        pages = read_pdf(os.path.join(folder, pv), img_output_dir)
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