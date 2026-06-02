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

def is_alternatives_start(block_idx, blocks):
    block = blocks[block_idx]
    if block.get("type") != 0:
        return False, None
    
    # Get block text lines
    lines = []
    for line in block.get("lines", []):
        line_text = "".join(span.get("text", "") for span in line.get("spans", []))
        lines.append(line_text)
    
    a_idx = find_alternative_letter_line(lines, "A")
    if a_idx == -1:
        return False, None
    
    # Check if B, C, D, E are in the same block
    b_idx = find_alternative_letter_line(lines[a_idx+1:], "B")
    c_idx = find_alternative_letter_line(lines[a_idx+1:], "C")
    d_idx = find_alternative_letter_line(lines[a_idx+1:], "D")
    e_idx = find_alternative_letter_line(lines[a_idx+1:], "E")
    
    if b_idx != -1 and c_idx != -1 and d_idx != -1 and e_idx != -1:
        # Grouped block!
        return True, "grouped"
    
    # Check subsequent blocks
    expected = ["B", "C", "D", "E"]
    expected_idx = 0
    
    for next_idx in range(block_idx + 1, len(blocks)):
        next_block = blocks[next_idx]
        if next_block.get("type") == 1: # Image
            continue
        # Text block
        next_lines = []
        for line in next_block.get("lines", []):
            line_text = "".join(span.get("text", "") for span in line.get("spans", []))
            next_lines.append(line_text)
        
        # Check if contains the current expected letter
        target_letter = expected[expected_idx]
        let_idx = find_alternative_letter_line(next_lines, target_letter)
        if let_idx != -1:
            expected_idx += 1
            if expected_idx == len(expected):
                return True, "split"
                
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
    for q, blocks_list in sorted(q_blocks.items()):
        found_start = False
        start_type = None
        start_idx = -1
        for idx, block in enumerate(blocks_list):
            is_start, s_type = is_alternatives_start(idx, blocks_list)
            if is_start:
                found_start = True
                start_type = s_type
                start_idx = idx
                break
        if found_start:
            print(f"  Questão {q}: Found alternatives start at block {start_idx} ({start_type})")
        else:
            print(f"  Questão {q}: NOT FOUND!")
