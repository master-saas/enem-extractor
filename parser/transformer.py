import os
import json
import uuid
import re

BASE_DIR = "output/2024"
LOG_FILE = os.path.join(BASE_DIR, "parser_log.txt")
VERBOSE = False

def set_verbose(value):
    """Enable or disable verbose logging"""
    global VERBOSE
    VERBOSE = value

def log(msg):
    """Print and write to log file"""
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
    r'^ENEM2024ENEM2024ENEM2024ENEM2024ENEM2024ENEM2024ENEM2024',
    r'^[A-Z0-9]{5,}•\s*\d+$',
]

NOISE_REGEX = re.compile('|'.join(NOISE_PATTERNS), re.IGNORECASE)


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


def is_block_image(block):
    """Check if block is an image"""
    return block.get("type") == 1


def extract_block_text(block):
    """Extract text from a block preserving line structure"""
    if block.get("type") != 0:
        return ""
    
    if "lines" not in block:
        return ""
    
    lines = []
    for line in block["lines"]:
        line_text = ""
        for span in line.get("spans", []):
            text = span.get("text", "")
            if text:
                line_text += text
        if line_text:
            lines.append(line_text)
    
    return lines


def extract_text_with_markdown(block):
    """Extract text from block with markdown formatting based on span flags"""
    if block.get("type") != 0:
        return "", []
    
    if "lines" not in block:
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
                text_formatted = f"**{text}**"
            elif flags & 1:
                text_formatted = f"*{text}*"
            else:
                text_formatted = text
            
            line_parts.append(text_formatted)
        
        if line_parts:
            formatted_lines.append("".join(line_parts))
    
    return "\n".join(formatted_lines), formatted_lines


def extract_block_bbox(block):
    """Get bounding box of block"""
    return block.get("bbox", [0, 0, 0, 0])


def is_noise_text(text):
    if not text or len(text.strip()) < 3:
        return True
    text_trimmed = text.strip()[:30]
    return bool(NOISE_REGEX.match(text_trimmed)) if text_trimmed else False


def clean_question_header(text):
    """Remove corrupted QUESTÃO header garbage"""
    text = re.sub(r'^QUEST[A-ZÃà-öø-ÿ]+\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'^QUESTÃO\s*\d+\s*', '', text)
    text = re.sub(r'^\d+\s*', '', text)
    return text.strip()


def find_question_start(text, start_pos=0):
    """Find position where a new question starts"""
    match = re.search(r'QUESTÃO\s+(\d+)', text[start_pos:])
    if match:
        return start_pos + match.start()
    return -1


def find_first_alternative(text):
    """Find position of first alternative letter (A-E)"""
    pattern = r'\nA\t'
    match = re.search(pattern, text)
    if match:
        return match.start()
    pattern = r'^A\t'
    match = re.match(pattern, text)
    if match:
        return 0
    return -1


def split_context_and_intro(full_text):
    """Split the full question text into context and alternativesIntroduction"""
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
    
    context = '\n'.join(context_lines).strip()
    intro = '\n'.join(intro_text_parts).strip()
    
    return context, intro


def parse_alternatives(text):
    """Parse alternatives A-E from text"""
    alternatives = {}
    letters = ["A", "B", "C", "D", "E"]
    
    for letter in letters:
        alternatives[letter] = ""
    
    text = re.sub(r'([A-E])\t\n', r'\1\n', text)
    text = re.sub(r'\n([A-E])\t\n', r'\n\1\n', text)
    
    if text.startswith('A\t'):
        text = 'A ' + text[2:]
    else:
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
            letter = match.group(1)
            text_content = match.group(2).strip()
            
            if current_letter and current_text:
                alternatives[current_letter] = ' '.join(current_text).strip()
            
            current_letter = letter
            current_text = [text_content] if text_content else []
        else:
            if current_letter and stripped:
                current_text.append(stripped)
    
    if current_letter and current_text:
        alternatives[current_letter] = ' '.join(current_text).strip()
    
    return alternatives


def extract_question_content(question_blocks):
    """Extract question content from blocks with metadata"""
    context_parts = []
    alternatives_intro = ""
    alternatives_text = ""
    has_image = False
    phase = "context"
    last_context_line = ""
    
    for i, block in enumerate(question_blocks):
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
        
        if re.match(r'^QUESTÃO\s+\d+', full_block_text.strip()):
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
    """Format context with proper line breaks"""
    if not context_parts:
        return ""
    
    formatted_lines = []
    for part in context_parts:
        part = part.strip()
        if part:
            formatted_lines.append(part)
    
    return "\n\n".join(formatted_lines)


def extract_intro_from_context(context_text):
    """Extract alternativesIntroduction from context (text before alternatives)"""
    if not context_text:
        return ""
    
    context_text_clean = context_text.replace("![](img)", "")
    context_text_clean = re.sub(r'\s*\n+\s*', '\n', context_text_clean)
    context_text_clean = context_text_clean.strip()
    
    if '\nA\t' in context_text_clean or '\nA ' in context_text_clean:
        if '\nA\t' in context_text_clean:
            parts = context_text_clean.split('\nA\t')
        else:
            parts = context_text_clean.split('\nA ')
        return parts[0].strip()
    
    return ""


def clean_alternative_text(alt_text):
    """Clean alternative text"""
    if not alt_text:
        return ""
    
    lines = alt_text.split("\n")
    
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line and not is_noise_text(line):
            line = re.sub(r'^[A-E]\s+', '', line)
            cleaned_lines.append(line)
    
    return " ".join(cleaned_lines)


def build_question_new(q_num, page_data, gabarito):
    """Build question JSON from page data blocks"""
    blocks = page_data.get("blocks", [])
    
    log(f"\n>>> build_question_new called for Q{q_num}")
    
    question_blocks = []
    current_q = None
    buffer = []
    
    for block in blocks:
        if block.get("type") == 0:
            text = "\n".join(extract_block_text(block))
        else:
            text = ""
        
        if not text:
            question_blocks.append(block)
            continue
        
        match = re.match(r'^QUESTÃO\s+(\d+)', text.strip())
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
    
    alternatives_list = []
    for letter in ["A", "B", "C", "D", "E"]:
        alt_text = alternatives.get(letter, "")
        alt_text = clean_alternative_text(alt_text)
        
        alternatives_list.append({
            "letter": letter,
            "text": alt_text,
            "file": None,
            "isCorrect": gabarito.get(q_num) == letter
        })
    
    has_valid_alts = any(a["text"] for a in alternatives_list)
    if not has_valid_alts:
        for i, a in enumerate(alternatives_list):
            if a["letter"] == gabarito.get(q_num):
                alternatives_list[i]["isCorrect"] = True
                break
    
    files = ["![](img)"] if has_image else []
    
    return {
        "title": f"Questão {q_num} - ENEM 2024",
        "index": q_num,
        "year": 2024,
        "language": detect_language(q_num, False),
        "discipline": detect_discipline(q_num),
        "context": context,
        "files": files,
        "correctAlternative": gabarito.get(q_num),
        "alternativesIntroduction": intro_raw.strip(),
        "alternatives": alternatives_list
    }


def build_question(q_num, text_blocks, gabarito):
    """Legacy build_question for compatibility"""
    page_data = {
        "blocks": [],
        "page_num": 0,
        "is_two_column": True
    }
    
    for text in text_blocks:
        block = {
            "type": 0,
            "bbox": [0, 0, 0, 0],
            "lines": []
        }
        
        lines = text.split("\n")
        for line_text in lines:
            if line_text:
                span = {"text": line_text, "flags": 0}
                block["lines"].append({"spans": [span]})
        
        page_data["blocks"].append(block)
    
    return build_question_new(q_num, page_data, gabarito)


def build_question_with_language(q_num, text_blocks, gabarito, is_spanish_variant=False):
    """Build question with specific language variant"""
    q = build_question(q_num, text_blocks, gabarito)
    q["language"] = detect_language(q_num, is_spanish_variant)
    return q


def group_questions_by_number(all_pages):
    """Group blocks by question number"""
    questions_by_num = {}
    current_q = None
    current_blocks = []
    prev_page_num = None
    
    for page_data in all_pages:
        page_num = page_data.get("page_num", 0)
        blocks = page_data.get("blocks", [])
        
        for block in blocks:
            if block.get("type") == 0:
                text = "\n".join(extract_block_text(block))
            else:
                text = ""
            
            if not text:
                if block.get("type") == 1:
                    if current_q is not None:
                        current_blocks.append(block)
                continue
            
            match = re.match(r'^QUESTÃO\s+(\d+)', text.strip())
            
            if match:
                q_num = int(match.group(1))
                
                if current_q is not None and current_blocks:
                    questions_by_num[current_q] = current_blocks
                
                current_q = q_num
                current_blocks = [block]
            else:
                if current_q is not None:
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

    questions_by_num = {}
    question_page_images = {}
    current_q = None
    current_blocks = []
    current_page_images = []
    images_used_in_page = 0
    
    for page_data in data["pages"]:
        blocks = page_data.get("blocks", [])
        current_page_images = page_data.get("images", [])
        images_used_in_page = 0
        
        for block in blocks:
            if block.get("type") == 0:
                text = "\n".join(extract_block_text(block))
                
                text_clean = text.strip()
                if len(text_clean) > 0 and text_clean[:30]:
                    text_trimmed = text_clean[:30]
                    if is_noise_text(text_trimmed) and 'QUESTÃO' not in text_clean:
                        log(f"[NOISE BLOCK] {repr(text_trimmed)}")
                        continue
            else:
                text = ""
            
            if not text:
                if block.get("type") == 1 and current_q is not None:
                    current_blocks.append(block)
                    if images_used_in_page < len(current_page_images):
                        question_page_images.setdefault(current_q, []).append(
                            current_page_images[images_used_in_page]
                        )
                        images_used_in_page += 1
                continue
            
            match = re.match(r'^QUESTÃO\s+(\d+)', text.strip())
            
            if match:
                q_num = int(match.group(1))
                log(f"[FOUND] QUESTÃO {q_num} on page {page_data.get('page_num')}")
                
                if current_q is not None and current_blocks:
                    questions_by_num[current_q] = current_blocks
                
                current_q = q_num
                current_blocks = [block]
                images_used_in_page = 0
            else:
                if current_q is not None:
                    current_blocks.append(block)
    
    if current_q is not None and current_blocks:
        questions_by_num[current_q] = current_blocks

    log(f"\nFound {len(questions_by_num)} questions: {sorted(questions_by_num.keys())[:10]}...")

    questions_list = []
    for q_num in sorted(questions_by_num.keys()):
        blocks = questions_by_num[q_num]
        
        log(f"\n{'='*60}")
        log(f"PROCESSING QUESTION {q_num}")
        log(f"{'='*60}")
        
        log(f"\n[BLOCKS] Found {len(blocks)} blocks for Q{q_num}:")
        for i, block in enumerate(blocks):
            if block.get("type") == 1:
                log(f"  Block {i}: IMAGE")
            else:
                text = "\n".join(extract_block_text(block))
                log(f"  Block {i}: {repr(text[:100])}")
        
        page_data = {"blocks": blocks, "page_num": 0, "is_two_column": True}
        q_json = build_question_new(q_num, page_data, data["gabarito"])
        
        log(f"\n[RESULT] Q{q_num}:")
        log(f"  Context: {repr(q_json.get('context', '')[:80])}...")
        log(f"  Intro: {repr(q_json.get('alternativesIntroduction', '')[:80])}")
        log(f"  Alternatives: A={repr(q_json['alternatives'][0].get('text', '')[:40])}, B={repr(q_json['alternatives'][1].get('text', '')[:40])}")
        
        if q_num <= 5 and english_start and spanish_start:
            folder = os.path.join(q_dir, f"{q_num}-ingles")
        elif q_num <= 5:
            folder = os.path.join(q_dir, f"{q_num}-ingles")
        else:
            folder = os.path.join(q_dir, str(q_num))

        os.makedirs(folder, exist_ok=True)
        
        img_list = question_page_images.get(q_num, [])
        
        KNOWN_DAY1 = {1, 3, 4, 13, 15, 19, 20, 39, 48, 64, 79}
        if q_num > 90 or (1 <= q_num <= 90 and q_num not in KNOWN_DAY1):
            img_list = []
        
        for i, img in enumerate(img_list):
            img_filename = f"image-{i+1}.png"
            img_dest = os.path.join(folder, img_filename)
            try:
                if os.path.exists(img["path"]):
                    os.rename(img["path"], img_dest)
            except Exception as e:
                log(f"  [IMAGE ERROR] Failed to move image: {e}")
        
        context = q_json.get("context", "")
        if len(img_list) > 0:
            context = context.replace("![](img)", "")
            for i in range(len(img_list)):
                context += f"\n\n![](image-{i+1}.png)"
        
        q_json["context"] = context
        q_json["files"] = [f"image-{i+1}.png" for i in range(len(img_list))]
        
        with open(os.path.join(folder, "details.json"), "w", encoding="utf-8") as f:
            json.dump(q_json, f, ensure_ascii=False, indent=2)

        questions_list.append((q_num, q_json))

        if q_num <= 5:
            q_json_spanish = build_question_new(q_num, page_data, data["gabarito"])
            q_json_spanish["language"] = "espanhol"
            folder_espanhol = os.path.join(q_dir, f"{q_num}-espanhol")
            os.makedirs(folder_espanhol, exist_ok=True)
            for i in range(len(img_list)):
                img_filename = f"image-{i+1}.png"
                img_dest = os.path.join(folder_espanhol, img_filename)
                src_path = os.path.join(folder, img_filename)
                try:
                    if os.path.exists(src_path) and not os.path.exists(img_dest):
                        import shutil
                        shutil.copy2(src_path, img_dest)
                except Exception as e:
                    log(f"  [IMAGE ERROR] Failed to copy image for Spanish: {e}")
            context_es = q_json_spanish.get("context", "")
            context_es = context_es.replace("![](img)", "")
            for i in range(len(img_list)):
                context_es += f"\n\n![](image-{i}.png)"
            q_json_spanish["context"] = context_es
            q_json_spanish["files"] = [f"image-{i+1}.png" for i in range(len(img_list))]
            with open(os.path.join(folder_espanhol, "details.json"), "w", encoding="utf-8") as f:
                json.dump(q_json_spanish, f, ensure_ascii=False, indent=2)

    build_details_index(questions_list, data["gabarito"])

    return BASE_DIR


def save_question(q_num, text, gabarito, base_dir, is_spanish_variant=False):
    if is_spanish_variant:
        folder = os.path.join(base_dir, f"{q_num}-espanhol")
    elif q_num <= 5:
        folder = os.path.join(base_dir, f"{q_num}-ingles")
    else:
        folder = os.path.join(base_dir, str(q_num))

    os.makedirs(folder, exist_ok=True)

    q_json = build_question(q_num, [text], gabarito)

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
    for q_num, q_json in questions_list:
        questions_index.append({
            "title": f"Questão {q_num} - ENEM 2024",
            "index": q_num,
            "discipline": q_json.get("discipline"),
            "language": q_json.get("language")
        })

        if q_num <= 5:
            questions_index.append({
                "title": f"Questão {q_num} - ENEM 2024",
                "index": q_num,
                "discipline": "linguagens",
                "language": "espanhol"
            })

    details = {
        "title": "ENEM 2024",
        "year": 2024,
        "disciplines": disciplines,
        "languages": languages,
        "questions": questions_index
    }

    with open(os.path.join(BASE_DIR, "details.json"), "w", encoding="utf-8") as f:
        json.dump(details, f, ensure_ascii=False, indent=2)