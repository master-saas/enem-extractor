d = open('pparser/transformer.py', 'rb').read()

fixes = [
    # noise check
    (
        b"noise_text(text_trimmed) and 'QUEST\xc3\x83O' not in text_clean:",
        b"noise_text(text_trimmed) and not re.search(r'QUEST', text_clean, re.IGNORECASE):"
    ),
    # re.match no-capture
    (
        b"re.match(r'^QUEST\xc3\x83O\\s+\\d+', full_block_text.strip()):",
        b"re.match(r'^QUEST[\xc3\x83\xc3\xa3]O\\s+\\d+', full_block_text.strip(), re.IGNORECASE):"
    ),
    # re.match with capture
    (
        b"re.match(r'^QUEST\xc3\x83O\\s+(\\d+)', text.strip())",
        b"re.match(r'^QUEST[\xc3\x83\xc3\xa3]O\\s+(\\d+)', text.strip(), re.IGNORECASE)"
    ),
]

for old, new in fixes:
    count = d.count(old)
    print(f"Replacing {count}x: {old[:30]}")
    d = d.replace(old, new)

open('pparser/transformer.py', 'wb').write(d)
print("Done")
