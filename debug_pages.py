import fitz

doc = fitz.open("input/2025_PV_impresso_D1_CD2.pdf")
for page_num in range(1, 6):
    page = doc[page_num]
    print(f"=== PAGE {page_num} ===")
    print("Images count:", len(page.get_images()))
    text = page.get_text()
    lines = [l.strip() for l in text.split('\n') if l.strip()]
    print("First 5 lines:", lines[:5])
    print("Last 5 lines:", lines[-5:])
    # Print occurrences of QUESTÃO
    questoes = [l for l in lines if "QUESTÃO" in l.upper()]
    print("Questions mentioned:", questoes)
