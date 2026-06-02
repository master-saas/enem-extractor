import os
import json
import re

BASE_DIR = "output/2024"
LOG_FILE = os.path.join(BASE_DIR, "parser_log.txt")
VERBOSE = False
YEAR = 2024

def set_verbose(value):
    global VERBOSE
    VERBOSE = value

def set_year(year):
    global YEAR, BASE_DIR, LOG_FILE
    YEAR = year
    BASE_DIR = f"output/{year}"
    LOG_FILE = os.path.join(BASE_DIR, "parser_log.txt")

def log(msg):
    if VERBOSE:
        try:
            print(msg)
        except UnicodeEncodeError:
            print(msg.encode('cp1252', errors='replace').decode('cp1252'))
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass

NOISE_PATTERNS = [
    r'^REDAÇÃO\s*•',
    r'^CADERNO\s*\d',
    r'^AMARELO',
    r'^AZUL',
    r'^BRANCO',
    r'^ROSA',
    r'^\d+\s*º?\s*DIA',
    r'^\d+\s*º?\s*FASE',
    r'^Questões de \d+ a \d+',
    r'^Linguagens',
    r'^Humanas',
    r'^Natureza',
    r'^Matemática',
    r'^Ciências',
    r'^TECNOLOGIAS',
    r'^opção (inglês|espanhol)',
    r'^TEXTO\s*[IV]',
    r'^FIGURA\s*\d',
    r'^IMAGEM\s*\d',
    r'^GRÁFICO\s*\d',
    r'^TABELA\s*\d',
    r'^LINGUAGENS',
    r'^CIÊNCIAS',
    r'^MATEMÁTICA',
    r'^HUMANAS',
    r'^NATUREZA',
    r'^\*?\d+[A-Z0-9]{2,}\*?$',
    r'^ENEM\d+$',
    r'^ENEM\s*ENEM',
    r'^[A-Z0-9]{10,}$',
    r'^•\s*[A-ZÀ-ÖØ-öø-ÿ]+\s*,\s*[A-ZÀ-ÖØ-öø-ÿ]+',
    r'^1\s*º?\s*DIA',
    r'^2\s*º?\s*DIA',
    r'^LINGUAGENS, CÓDIGOS E SUAS TECNOLOGIAS',
    r'^CIÊNCIAS HUMANAS E SUAS TECNOLOGIAS',
    r'^CIÊNCIAS DA NATUREZA E SUAS TECNOLOGIAS',
    r'^MATEMÁTICA E SUAS TECNOLOGIAS',
    r'^ENEM\d{4}(?:ENEM\d{4})+',
    r'^[A-Z0-9]{5,}•\s*\d+$',
]

NOISE_REGEX = re.compile('|'.join(NOISE_PATTERNS), re.IGNORECASE)

Q_PATTERN = re.compile(r'^QUEST[ÃÃã]O\s+(\d+)', re.IGNORECASE)


def detect_discipline(q):
    if q <= 45:
        return "linguagens"
    elif q <= 90:
        return "ciencias-humanas"
    elif q <= 135:
        return "ciencias-natureza"
    return "matematica"


def detect_language(q_num, is_spanish_variant=False):
    if q_num <= 5:
        return "espanhol" if is_spanish_variant else "ingles"
    return None


def _get_bbox_overlap(bbox1, bbox2):
    if not bbox1 or not bbox2:
        return 0.0
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


def is_block_image(block):
    return block.get("type") == 1 and "matched_image" in block


def extract_block_text(block):
    if block.get("type") != 0 or "lines" not in block:
        return ""
    lines = []
    for line in block["lines"]:
        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
        if line_text:
            lines.append(line_text)
    return lines


def extract_text_with_markdown(block):
    if block.get("type") != 0 or "lines" not in block:
        return "", []
    formatted_lines = []
    for line in block["lines"]:
        line_parts = []
        for span in line.get("spans", []):
            text = span.get("text", "")
            flags = span.get("flags", 0)
            if not text:
                continue
            if flags & 2:
                text = f"**{text}**"
            elif flags & 1:
                text = f"*{text}*"
            line_parts.append(text)
        if line_parts:
            formatted_lines.append("".join(line_parts))
    return "\n".join(formatted_lines), formatted_lines


def extract_block_bbox(block):
    return block.get("bbox", [0, 0, 0, 0])


def is_noise_text(text):
    if not text or len(text.strip()) < 3:
        return True
    text_trimmed = text.strip()[:30]
    return bool(NOISE_REGEX.match(text_trimmed)) if text_trimmed else False


def clean_question_header(text):
    text = re.sub(r'^QUEST[A-ZÃà-öø-ÿ]+\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^QUESTÃO\s*\d+\s*', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    return text.strip()


def find_question_start(text, start_pos=0):
    match = re.search(r'QUEST[ÃÃã]O\s+(\d+)', text[start_pos:], re.IGNORECASE)
    if match:
        return start_pos + match.start()
    return -1


def find_first_alternative(text):
    match = re.search(r'\nA\t', text)
    if match:
        return match.start()
    match = re.match(r'^A\t', text)
    if match:
        return 0
    return -1


def split_context_and_intro(full_text):
    if not re.search(r'A\t', full_text):
        return full_text.strip(), ""
    lines = full_text.split('\n')
    context_lines = []
    intro_text_parts = []
    alternatives_started = False
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r'^([A-E])\t(.*)', stripped)
        if match:
            alternatives_started = True
            letter = match.group(1)
            rest = match.group(2).strip()
            if letter == 'A' and rest:
                intro_text_parts.append(rest)
            elif letter in ['B', 'C', 'D', 'E'] and rest:
                intro_text_parts.append(f"{letter} {rest}")
            continue
        if alternatives_started:
            intro_text_parts.append(stripped)
        else:
            context_lines.append(line)
    return '\n'.join(context_lines).strip(), '\n'.join(intro_text_parts).strip()


def parse_alternatives(text):
    alternatives = {l: "" for l in ["A", "B", "C", "D", "E"]}
    text = re.sub(r'([A-E])\t\n', r'\1\n', text)
    text = re.sub(r'\n([A-E])\t\n', r'\n\1\n', text)
    text = re.sub(r'^A\t', 'A ', text)
    text = re.sub(r'\t([A-Z])', r' \1', text)
    lines = text.split('\n')
    current_letter = None
    current_text = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r'^([A-E])\s+(.*)', stripped)
        if match:
            if current_letter and current_text:
                alternatives[current_letter] = ' '.join(current_text).strip()
            current_letter = match.group(1)
            current_text = [match.group(2).strip()] if match.group(2).strip() else []
        else:
            if current_letter and stripped:
                current_text.append(stripped)
    if current_letter and current_text:
        alternatives[current_letter] = ' '.join(current_text).strip()
    return alternatives


def find_alternative_letter_line(lines, letter):
    pattern = re.compile(rf'^{letter}(?:\s+|\.|\)|$)')
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if pattern.match(stripped):
            return idx
    return -1


def detect_alternatives_robust(blocks):
    flat_lines = []
    for b_idx, b in enumerate(blocks):
        if b.get("type") == 0:
            for l_idx, line in enumerate(b.get("lines", [])):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                flat_lines.append((b_idx, l_idx, line_text))
                
    for i, (b_idx, l_idx, text) in enumerate(flat_lines):
        stripped = text.strip()
        if re.match(r'^A(?:\s+|\.|\)|$)', stripped):
            expected = ["B", "C", "D", "E"]
            expected_idx = 0
            positions = {"A": (b_idx, l_idx)}
            
            for j in range(i + 1, len(flat_lines)):
                curr_b_idx, curr_l_idx, curr_text = flat_lines[j]
                curr_stripped = curr_text.strip()
                target_letter = expected[expected_idx]
                if re.match(rf'^{target_letter}(?:\s+|\.|\)|$)', curr_stripped):
                    positions[target_letter] = (curr_b_idx, curr_l_idx)
                    expected_idx += 1
                    if expected_idx == len(expected):
                        return True, positions
                        
    return False, None


def extract_question_content(question_blocks):
    found, positions = detect_alternatives_robust(question_blocks)
    if found:
        a_b_idx, a_l_idx = positions["A"]
        context_parts = []
        has_image = False
        alternatives_intro = ""
        
        # Collect context parts up to a_b_idx
        for idx in range(a_b_idx):
            block = question_blocks[idx]
            if is_block_image(block):
                has_image = True
                context_parts.append("![](img)")
            else:
                lines = extract_block_text(block)
                full_text = "\n".join(lines)
                if full_text.strip():
                    context_parts.append(full_text)
                    
        # Handle start block
        start_block = question_blocks[a_b_idx]
        start_lines = extract_block_text(start_block)
        
        if a_l_idx > 0:
            intro_lines = start_lines[:a_l_idx]
            intro_text = "\n".join(intro_lines).strip()
            if intro_text:
                context_parts.append(intro_text)
            alternatives_intro = intro_text
        else:
            alternatives_intro = ""
            for i in range(len(context_parts) - 1, -1, -1):
                if context_parts[i] != "![](img)" and context_parts[i].strip():
                    alternatives_intro = context_parts[i].strip()
                    break
                    
        # Build alternatives_text
        alternatives_text_parts = []
        for b_idx in range(a_b_idx, len(question_blocks)):
            block = question_blocks[b_idx]
            if is_block_image(block):
                has_image = True
                alternatives_text_parts.append("![](img)")
                continue
                
            lines = extract_block_text(block)
            for l_idx, line in enumerate(lines):
                if b_idx == a_b_idx and l_idx < a_l_idx:
                    continue
                    
                is_letter_line = False
                for letter in ["A", "B", "C", "D", "E"]:
                    if positions.get(letter) == (b_idx, l_idx):
                        stripped_line = line.strip()
                        text_without_prefix = re.sub(rf'^{letter}(?:\s+|\.|\)|$)', '', stripped_line).strip()
                        alternatives_text_parts.append(f"{letter} {text_without_prefix}")
                        is_letter_line = True
                        break
                        
                if not is_letter_line:
                    alternatives_text_parts.append(line.strip())
                    
        alternatives_text = "\n".join(alternatives_text_parts)
        return context_parts, alternatives_text, has_image, alternatives_intro

    # Fallback to legacy logic
    context_parts = []
    alternatives_intro = ""
    alternatives_text = ""
    has_image = False
    phase = "context"
    last_context_line = ""

    for block in question_blocks:
        if is_block_image(block):
            has_image = True
            if phase == "context":
                context_parts.append("![](img)")
            else:
                alternatives_text += "\n![](img)"
            continue

        text_lines = extract_block_text(block)
        if not text_lines:
            continue

        full_block_text = "\n".join(text_lines)

        if Q_PATTERN.match(full_block_text.strip()):
            continue

        if '\nA\t' in full_block_text:
            parts = full_block_text.split('\nA\t')
            if len(parts) > 1:
                alternatives_intro = parts[0].strip()
                alternatives_text = "A " + parts[1].strip()
                phase = "alternatives"
                continue

        if re.match(r'^A\t', full_block_text):
            alternatives_intro = last_context_line
            alternatives_text = "A " + full_block_text[2:].strip()
            phase = "alternatives"
            if context_parts:
                context_parts = context_parts[:-1]
            continue

        if phase == "context":
            if '\tA\t' not in full_block_text:
                context_parts.append(full_block_text)
                if full_block_text.strip():
                    last_context_line = full_block_text.strip()
        else:
            alternatives_text += "\n" + full_block_text

    if not alternatives_intro and context_parts:
        combined = "\n".join(context_parts)
        if '\nA\t' in combined:
            parts = combined.split('\nA\t')
            if len(parts) > 1:
                alternatives_intro = parts[0].strip()
                alternatives_text = "A " + parts[1].strip()
                context_parts = [parts[0].strip()]
        elif last_context_line:
            alternatives_intro = last_context_line
            context_parts = context_parts[:-1]

    return context_parts, alternatives_text, has_image, alternatives_intro


def format_context_text(context_parts):
    return "\n\n".join(p.strip() for p in context_parts if p.strip())


def extract_intro_from_context(context_text):
    if not context_text:
        return ""
    clean = re.sub(r'\s*\n+\s*', '\n', context_text.replace("![](img)", "")).strip()
    if '\nA\t' in clean:
        return clean.split('\nA\t')[0].strip()
    if '\nA ' in clean:
        return clean.split('\nA ')[0].strip()
    return ""


def clean_alternative_text(alt_text):
    if not alt_text:
        return ""
    lines = [re.sub(r'^[A-E]\s+', '', l.strip()) for l in alt_text.split("\n")
             if l.strip() and not is_noise_text(l.strip())]
    return " ".join(lines)


def get_correct_alternative(q_num, gabarito, language=None):
    if q_num <= 5 and language in ("ingles", "espanhol"):
        for key in [(q_num, language), f"{q_num}_{language}"]:
            if key in gabarito:
                return gabarito[key]
    return gabarito.get(q_num)


def _build_q_json(q_num, blocks, gabarito, language=None):
    page_data = {"blocks": blocks, "page_num": 0, "is_two_column": True}
    q_json = build_question_new(q_num, page_data, gabarito, language=language)
    if language is not None:
        q_json["language"] = language
    return q_json


def build_question_new(q_num, page_data, gabarito, language=None):
    blocks = page_data.get("blocks", [])
    log(f"\n>>> build_question_new called for Q{q_num}")

    question_blocks = []
    current_q = None
    buffer = []

    for block in blocks:
        text = "\n".join(extract_block_text(block)) if block.get("type") == 0 else ""
        if not text:
            question_blocks.append(block)
            continue
        match = Q_PATTERN.match(text.strip())
        if match:
            if current_q is not None and current_q == q_num and buffer:
                question_blocks.extend(buffer)
            current_q = int(match.group(1))
            buffer = [block]
        elif current_q == q_num:
            buffer.append(block)
        elif current_q is not None and current_q != q_num:
            if buffer:
                question_blocks.extend(buffer)
            buffer = []
            current_q = q_num
            buffer.append(block)
        elif current_q is None:
            buffer.append(block)

    if current_q == q_num and buffer:
        question_blocks.extend(buffer)

    context_parts, alternatives_text, has_image, alternatives_intro = extract_question_content(question_blocks)
    context = format_context_text(context_parts)
    intro_raw = alternatives_intro if alternatives_intro else extract_intro_from_context(context)
    alternatives = parse_alternatives(alternatives_text)

    correct_ans = get_correct_alternative(q_num, gabarito, language)

    alternatives_list = []
    for letter in ["A", "B", "C", "D", "E"]:
        alt_text = clean_alternative_text(alternatives.get(letter, ""))
        alternatives_list.append({
            "letter": letter,
            "text": alt_text,
            "file": None,
            "isCorrect": correct_ans == letter
        })

    if not any(a["text"] for a in alternatives_list):
        for a in alternatives_list:
            if a["letter"] == correct_ans:
                a["isCorrect"] = True
                break

    return {
        "title": f"Questão {q_num} - ENEM {YEAR}",
        "index": q_num,
        "year": YEAR,
        "language": language if language is not None else detect_language(q_num, False),
        "discipline": detect_discipline(q_num),
        "context": context,
        "files": ["![](img)"] if has_image else [],
        "correctAlternative": correct_ans,
        "alternativesIntroduction": intro_raw.strip(),
        "alternatives": alternatives_list
    }


def build_question(q_num, text_blocks, gabarito, language=None):
    page_data = {"blocks": [], "page_num": 0, "is_two_column": True}
    for text in text_blocks:
        block = {"type": 0, "bbox": [0, 0, 0, 0], "lines": []}
        for line_text in text.split("\n"):
            if line_text:
                block["lines"].append({"spans": [{"text": line_text, "flags": 0}]})
        page_data["blocks"].append(block)
    return build_question_new(q_num, page_data, gabarito, language=language)


def build_question_with_language(q_num, text_blocks, gabarito, is_spanish_variant=False):
    lang = detect_language(q_num, is_spanish_variant)
    q = build_question(q_num, text_blocks, gabarito, language=lang)
    q["language"] = lang
    return q


def group_questions_by_number(all_pages):
    questions_by_num = {}
    current_q = None
    current_blocks = []

    for page_data in all_pages:
        for block in page_data.get("blocks", []):
            text = "\n".join(extract_block_text(block)) if block.get("type") == 0 else ""
            if not text:
                if block.get("type") == 1 and current_q is not None:
                    current_blocks.append(block)
                continue
            match = Q_PATTERN.match(text.strip())
            if match:
                if current_q is not None and current_blocks:
                    questions_by_num[current_q] = current_blocks
                current_q = int(match.group(1))
                current_blocks = [block]
            elif current_q is not None:
                current_blocks.append(block)
        if current_q is not None and current_blocks:
            questions_by_num[current_q] = current_blocks

    return questions_by_num


def build_output(data):
    os.makedirs(BASE_DIR, exist_ok=True)
    q_dir = os.path.join(BASE_DIR, "questions")
    os.makedirs(q_dir, exist_ok=True)

    if os.path.exists(LOG_FILE):
        os.remove(LOG_FILE)

    english_start = data.get("english_start")
    spanish_start = data.get("spanish_start")

    log("\n" + "="*60)
    log("STARTING PARSER - Building questions from PDF blocks")
    log("="*60)

    # Separate buckets: regular questions, english 1-5, spanish 1-5
    questions_by_num = {}
    lang_blocks = {"ingles": {}, "espanhol": {}}
    question_page_images = {}        # key: q_num for regular, (q_num, lang) for 1-5

    current_q = None
    current_blocks = []
    current_lang = None  # None = not a language section, 'ingles', 'espanhol'
    images_used_in_page = 0

    for page_data in data["pages"]:
        page_num = page_data.get("page_num", 0)
        blocks = page_data.get("blocks", [])
        current_page_images = page_data.get("images", [])
        images_used_in_page = 0

        # Detect language section from page text
        page_text = ""
        for block in blocks:
            if block.get("type") == 0:
                page_text += "\n".join(extract_block_text(block) or [])

        # Determine current page language
        page_lang = current_lang
        if english_start is not None and spanish_start is not None:
            if english_start <= page_num < spanish_start:
                page_lang = "ingles"
            elif page_num >= spanish_start:
                if current_q is not None and current_q > 5:
                    page_lang = None
                else:
                    page_lang = "espanhol"

        if "opção inglês" in page_text.lower() or "(opção inglês)" in page_text.lower():
            page_lang = "ingles"
        elif "opção espanhol" in page_text.lower() or "(opção espanhol)" in page_text.lower():
            page_lang = "espanhol"

        if page_lang != current_lang:
            if current_q is not None and current_blocks:
                _store_blocks(current_q, current_blocks, current_lang,
                              questions_by_num, lang_blocks)
                current_blocks = []
                current_q = None
            current_lang = page_lang

        for block in blocks:
            if block.get("type") == 0:
                text = "\n".join(extract_block_text(block))
                text_clean = text.strip()
                if text_clean and is_noise_text(text_clean[:30]) and not re.search(r'QUEST', text_clean, re.IGNORECASE):
                    log(f"[NOISE BLOCK] {repr(text_clean[:30])}")
                    continue
            else:
                text = ""

            if not text:
                if block.get("type") == 1 and current_q is not None:
                    bbox = block.get("bbox")
                    best_overlap = 0.0
                    best_img = None
                    if bbox:
                        for img in current_page_images:
                            img_bbox = img.get("bbox")
                            if img_bbox:
                                overlap = _get_bbox_overlap(bbox, img_bbox)
                                if overlap > best_overlap:
                                    best_overlap = overlap
                                    best_img = img
                    
                    if best_img and best_overlap > 0.5:
                        block["matched_image"] = best_img
                        current_blocks.append(block)
                        img_key = (current_q, current_lang) if current_q is not None and current_q <= 5 and current_lang else current_q
                        question_page_images.setdefault(img_key, []).append(best_img)
                continue

            match = Q_PATTERN.match(text.strip())
            if match:
                q_num = int(match.group(1))

                # Save previous question with the lang it was collected under
                if current_q is not None and current_blocks:
                    _store_blocks(current_q, current_blocks, current_lang,
                                  questions_by_num, lang_blocks)

                # Once we move past q5, leave the language section
                if q_num > 5:
                    current_lang = None

                log(f"[FOUND] QUESTÃO {q_num} on page {page_num} lang={current_lang}")
                current_q = q_num
                current_blocks = [block]
                images_used_in_page = 0
            else:
                if current_q is not None:
                    current_blocks.append(block)

    if current_q is not None and current_blocks:
        _store_blocks(current_q, current_blocks, current_lang,
                      questions_by_num, lang_blocks)

    total = len(questions_by_num) + len(lang_blocks["ingles"]) + len(lang_blocks["espanhol"])
    log(f"\nFound {total} question groups")
    log(f"  Regular: {sorted(questions_by_num.keys())[:10]}")
    log(f"  Inglês 1-5: {sorted(lang_blocks['ingles'].keys())}")
    log(f"  Espanhol 1-5: {sorted(lang_blocks['espanhol'].keys())}")

    questions_list = []

    # Process language questions 1-5
    for lang in ("ingles", "espanhol"):
        for q_num in sorted(lang_blocks[lang].keys()):
            blocks = lang_blocks[lang][q_num]
            log(f"\n{'='*60}\nPROCESSING Q{q_num} ({lang})\n{'='*60}")

            q_json = _build_q_json(q_num, blocks, data["gabarito"], language=lang)
            folder = os.path.join(q_dir, f"{q_num}-{lang}")
            os.makedirs(folder, exist_ok=True)

            img_list = _get_images(q_num, question_page_images, lang)
            q_json = _finalize_question(q_json, img_list, folder)

            with open(os.path.join(folder, "details.json"), "w", encoding="utf-8") as f:
                json.dump(q_json, f, ensure_ascii=False, indent=2)

            if lang == "ingles":
                questions_list.append((q_num, q_json))

    # Process regular questions
    for q_num in sorted(questions_by_num.keys()):
        blocks = questions_by_num[q_num]
        log(f"\n{'='*60}\nPROCESSING Q{q_num}\n{'='*60}")

        q_json = _build_q_json(q_num, blocks, data["gabarito"])
        folder = os.path.join(q_dir, str(q_num))
        os.makedirs(folder, exist_ok=True)

        img_list = _get_images(q_num, question_page_images, None)
        q_json = _finalize_question(q_json, img_list, folder)

        with open(os.path.join(folder, "details.json"), "w", encoding="utf-8") as f:
            json.dump(q_json, f, ensure_ascii=False, indent=2)

        questions_list.append((q_num, q_json))

    build_details_index(questions_list, data["gabarito"])
    return BASE_DIR


def _store_blocks(q_num, blocks, lang, questions_by_num, lang_blocks):
    if q_num <= 5 and lang in ("ingles", "espanhol"):
        lang_blocks[lang][q_num] = list(blocks)
    else:
        questions_by_num[q_num] = list(blocks)


def _get_images(q_num, question_page_images, lang):
    if q_num <= 5 and lang in ("ingles", "espanhol"):
        raw_list = question_page_images.get((q_num, lang), [])
    else:
        raw_list = question_page_images.get(q_num, [])
    
    seen = set()
    deduped = []
    for img in raw_list:
        xref = img.get("xref")
        if xref not in seen:
            seen.add(xref)
            deduped.append(img)
    return deduped


def _finalize_question(q_json, img_list, folder):
    import shutil
    for i, img in enumerate(img_list):
        img_dest = os.path.join(folder, f"image-{i+1}.png")
        try:
            if os.path.exists(img["path"]):
                shutil.copy(img["path"], img_dest)
        except Exception as e:
            log(f"  [IMAGE ERROR] {e}")

    context = q_json.get("context", "").replace("![](img)", "")
    for i in range(len(img_list)):
        context += f"\n\n![](image-{i+1}.png)"
    q_json["context"] = context
    q_json["files"] = [f"image-{i+1}.png" for i in range(len(img_list))]
    return q_json


def save_question(q_num, text, gabarito, base_dir, is_spanish_variant=False):
    if is_spanish_variant:
        folder = os.path.join(base_dir, f"{q_num}-espanhol")
    elif q_num <= 5:
        folder = os.path.join(base_dir, f"{q_num}-ingles")
    else:
        folder = os.path.join(base_dir, str(q_num))
    os.makedirs(folder, exist_ok=True)
    lang = detect_language(q_num, is_spanish_variant)
    q_json = build_question(q_num, [text], gabarito, language=lang)
    with open(os.path.join(folder, "details.json"), "w", encoding="utf-8") as f:
        json.dump(q_json, f, ensure_ascii=False, indent=2)


def build_details_index(questions_list, gabarito):
    disciplines = [
        {"label": "Ciências Humanas e suas Tecnologias", "value": "humanas"},
        {"label": "Ciências da Natureza e suas Tecnologias", "value": "ciencias-natureza"},
        {"label": "Linguagens, Códigos e suas Tecnologias", "value": "linguagens"},
        {"label": "Matemática e suas Tecnologias", "value": "matematica"},
    ]
    languages = [
        {"label": "Espanhol", "value": "espanhol"},
        {"label": "Inglês", "value": "ingles"},
    ]

    questions_index = []
    seen = set()
    for q_num, q_json in sorted(questions_list, key=lambda x: (x[0], x[1].get("language") or "")):
        lang = q_json.get("language")
        key = (q_num, lang)
        if key in seen:
            continue
        seen.add(key)
        questions_index.append({
            "title": f"Questão {q_num} - ENEM {YEAR}",
            "index": q_num,
            "discipline": q_json.get("discipline"),
            "language": lang
        })
        if q_num <= 5 and lang == "ingles":
            questions_index.append({
                "title": f"Questão {q_num} - ENEM {YEAR}",
                "index": q_num,
                "discipline": "linguagens",
                "language": "espanhol"
            })

    details = {
        "title": f"ENEM {YEAR}",
        "year": YEAR,
        "disciplines": disciplines,
        "languages": languages,
        "questions": questions_index
    }

    with open(os.path.join(BASE_DIR, "details.json"), "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)
