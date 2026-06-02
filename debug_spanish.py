import fitz

doc = fitz.open('./input/2025_PV_impresso_D1_CD2.pdf')
for i, page in enumerate(doc):
    text = page.get_text()
    if 'espanhol' in text.lower() or 'español' in text.lower() or 'QUESTãO 01' in text or 'QUESTãO 1 ' in text:
        print(f'--- PAGE {i} ---')
        print(text[:1500])
        print()
    if i > 10:
        break
