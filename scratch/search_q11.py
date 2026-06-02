import fitz
import re

doc = fitz.open("input/2025_PV_impresso_D1_CD2.pdf")
print(f"Total pages: {len(doc)}")
for page_num in range(len(doc)):
    page = doc[page_num]
    text = page.get_text()
    if re.search(r'QUEST[A-ZÃãO\s]+11', text, re.IGNORECASE):
        print(f"Found 'QUESTÃO 11' on page {page_num}")
    if "Dalton" in text:
        print(f"Found 'Dalton' on page {page_num}")
