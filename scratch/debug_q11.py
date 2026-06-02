import pparser.extractor as ex
import pparser.transformer as tr
import json

data = ex.extract_all("input", "output/2025/images")
print("Gabarito loaded:", bool(data["gabarito"]))

# Let's locate question 11 in pages
q_num = 11
question_blocks = []
current_q = None
buffer = []

for page_data in data["pages"]:
    blocks = page_data.get("blocks", [])
    for block in blocks:
        text = "\n".join(tr.extract_block_text(block)) if block.get("type") == 0 else ""
        if not text:
            continue
        match = tr.Q_PATTERN.match(text.strip())
        if match:
            if current_q == q_num:
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

if current_q == q_num and buffer:
    question_blocks.extend(buffer)

print("Found", len(question_blocks), "blocks for Questão 11")
for i, b in enumerate(question_blocks):
    print(f"Block {i}: type={b.get('type')}")
    if b.get('type') == 0:
        lines = tr.extract_block_text(b)
        for j, line in enumerate(lines):
            print(f"  Line {j}: {repr(line)}")

found, positions = tr.detect_alternatives_robust(question_blocks)
print("detect_alternatives_robust found:", found)
if found:
    print("positions:", positions)
