import fitz
from pparser.transformer import build_question_new, Q_PATTERN, extract_question_content

doc = fitz.open("input/2024_PV_impresso_D1_CD2.pdf")
# Find Q11
blocks_list = []
current_q = None

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
                if current_q == 11:
                    blocks_list = []
            if current_q == 11:
                blocks_list.append(b)

print(f"Blocks found for Q11 in 2024: {len(blocks_list)}")

# Run extract_question_content
context_parts, alternatives_text, has_image, alternatives_intro = extract_question_content(blocks_list)
print("--- context_parts ---")
for cp in context_parts:
    print(repr(cp))
print("--- alternatives_text ---")
print(repr(alternatives_text))
print("--- alternatives_intro ---")
print(repr(alternatives_intro))
