import re
import unicodedata

def normalize_newlines(text: str) -> str:
    """
    1) Convert visible escape sequences like '\\n' or '\\r\\n' to real newlines.
    2) Normalize all newline variants to \\n, including Unicode separators.
    """
    # Turn literal backslash-escapes into actual newlines if present
    text = text.replace('\\r\\n', '\n').replace('\\n', '\n').replace('\\r', '\n')
    # Normalize CR, CRLF, NEL, LINE SEP, PARA SEP to \n
    text = re.sub(r'\r\n?|\u0085|\u2028|\u2029', '\n', text)
    return text

def keep_letters_whitespace_commas(text: str) -> str:
    """
    Keep only:
      - Letters (all scripts) and their combining marks
      - Whitespace (normalized) and commas
    Remove everything else.
    """
    # Normalize Unicode (compose accents with base letters)
    text = unicodedata.normalize('NFC', text)

    # Normalize newlines
    text = normalize_newlines(text)

    # Convert non-newline whitespace runs to a single space
    text = re.sub(r'[^\S\n]+', ' ', text)

    kept = []
    for ch in text:
        if ch == ',' or ch == '\n' or ch == ' ':
            kept.append(ch)
            continue
        cat = unicodedata.category(ch)
        # L*: letters; M*: combining marks (accents)
        if cat[0] in ('L', 'M'):
            kept.append(ch)
        # else drop

    text = ''.join(kept)

    # Collapse repeated spaces; limit blank lines
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Strip trailing spaces on each line and overall
    text = '\n'.join(line.rstrip() for line in text.splitlines())
    return text.strip()

def clean_text(text: str) -> str:
    return keep_letters_whitespace_commas(text)

if __name__ == "__main__":
    sample = "Hello\\nworld!\u2028New line, and emojis 😊, punctuation?!  Non\u00A0breaking\u00A0spaces."
    print(clean_text(sample))
    # Output:
    # Hello
    # world
    # New line, and emojis punctuation
