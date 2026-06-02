import fitz
import re

pdf_files = [
    "input/2025_PV_impresso_D1_CD2.pdf",
    "input/2025_PV_impresso_D2_CD5.pdf",
    "input/2024_PV_impresso_D1_CD2.pdf",
    "input/2024_PV_impresso_D2_CD5.pdf"
]

def find_alternative_letter_line(lines, letter):
    pattern = re.compile(rf'^{letter}(?:\s+|\.|\)|$)')
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if pattern.match(stripped):
            return idx
    return -1

def detect_alternatives_robust(blocks):
    # Flatten all text blocks and their lines into a list of (block_idx, line_idx, line_text)
    flat_lines = []
    for b_idx, b in enumerate(blocks):
        if b.get("type") == 0:
            for l_idx, line in enumerate(b.get("lines", [])):
                line_text = "".join(span.get("text", "") for span in line.get("spans", []))
                flat_lines.append((b_idx, l_idx, line_text))
                
    # Search for "A"
    for i, (b_idx, l_idx, text) in enumerate(flat_lines):
        stripped = text.strip()
        if re.match(r'^A(?:\s+|\.|\)|$)', stripped):
            # We found a candidate start for "A"
            # Now let's see if we can find B, C, D, E sequentially in the remaining flat lines
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

# Test on PDFs
for filepath in pdf_files:
    doc = fitz.open(filepath)
    print(f"\nTesting {filepath}:")
    
    Q_PATTERN = re.compile(r'^QUEST[ÃÃã]O\s+(\d+)', re.IGNORECASE)
    current_q = None
    q_blocks = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        for b in blocks:
            if b.get("type") == 0:
                lines = ["".join(span["text"] for span in line.get("spans", [])) for line in b.get("lines", [])]
                full_text = "\n".join(lines).strip()
                match = Q_PATTERN.match(full_text)
                if match:
                    current_q = int(match.group(1))
                    q_blocks[current_q] = []
                if current_q is not None:
                    q_blocks[current_q].append(b)
            elif b.get("type") == 1 and current_q is not None:
                q_blocks[current_q].append(b)
                
    # Detect for each question
    unmatched = []
    for q, blocks_list in sorted(q_blocks.items()):
        found, positions = detect_alternatives_robust(blocks_list)
        if found:
            print(f"  Questão {q}: Found alternatives start at Block {positions['A'][0]} Line {positions['A'][1]}")
        else:
            print(f"  Questão {q}: NOT FOUND!")
            unmatched.append(q)
    if unmatched:
        print(f"Unmatched questions in {filepath}: {unmatched}")
    else:
        print(f"All questions in {filepath} matched perfectly!")
