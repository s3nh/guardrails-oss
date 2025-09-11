import regex as re

def clean_text(text: str) -> str:
    # Convert literal escapes to real newlines
    text = text.replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')
    # Normalize newline variants to \n
    text = re.sub(r'\r\n?|\u0085|\u2028|\u2029', '\n', text)

    # Keep letters (L), combining marks (M), whitespace (\s), and commas
    text = re.sub(r'[^,\p{L}\p{M}\s]+', '', text)

    # Normalize whitespace (keep newlines, collapse other spaces)
    text = re.sub(r'[^\S\n]+', ' ', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

# pip install regex
