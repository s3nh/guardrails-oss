import re

# Common Polish letters
PL_WORD = r"[A-Za-zĄĆĘŁŃÓŚŻŹąćęłńóśżź]"

# IBAN: capture alnum with optional spaces; start with two letters
IBAN_CANDIDATE = re.compile(r"\b([A-Z]{2}[0-9]{2}(?:[ -]?[A-Z0-9]){11,})\b", re.IGNORECASE)

# Card numbers 13-19 digits, allow spaces/dashes; starting digits 2-6 to reduce FP
CARD_CANDIDATE = re.compile(r"(?<!\d)(?:[2-6]\d(?:[ -]?\d)){12,18}\b")

# PESEL: 11 digits with optional separators
PESEL_CANDIDATE = re.compile(r"(?<!\d)(?:\d[ -]?){11}(?!\d)")

# NIP: 10 digits, separators allowed
NIP_CANDIDATE = re.compile(r"\b\d{3}[ -]?\d{3}[ -]?\d{2}[ -]?\d{2}\b")

# REGON: 9 or 14 digits, standalone
REGON9_CANDIDATE = re.compile(r"(?<!\d)\d{9}(?!\d)")
REGON14_CANDIDATE = re.compile(r"(?<!\d)\d{14}(?!\d)")

# Polish ID card: 3 letters + 6 digits, optional single space after letters
IDCARD_CANDIDATE = re.compile(r"\b([A-Z]{3})[ ]?(\d{6})\b")

# Postal code: NN-NNN
POSTAL_CODE = re.compile(r"\b\d{2}-\d{3}\b")

# UUID v1-5
UUID_CANDIDATE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")

# Transaction ID after keywords
TRANSACTION_BY_KEYWORD = re.compile(
    r"(?i)\b(?:id|identyfikator|transakcj\w*|nr|numer)\s*[:#]?\s*([A-Z0-9]{8,}|\b[0-9a-f]{16,}\b)",
)

# Long hex tokens (16-64) but standalone
LONG_HEX = re.compile(r"(?<![0-9a-fA-F])[0-9a-fA-F]{16,64}(?![0-9a-fA-F])")

# Address heuristics (street line)
ADDRESS_LINE = re.compile(
    r"(?i)\b(?:(ul\.|ulica|al\.|aleja|pl\.|plac|os\.|osiedle|rynek|rondo|bulwar|skwer))\s+"
    r"(" + PL_WORD + r"[^\n,;]{0,80}?)\s+"
    r"(\d+[A-Za-z]?(?:/\d+[A-Za-z]?)?)"
)

# Full name: Firstname Surname with possible hyphen, using Polish letters
FULL_NAME = re.compile(
    rf"\b({PL_WORD}{{2,}})\s+({PL_WORD}{{2,}}(?:-{PL_WORD}{{2,}})?)\b"
)

# Initial + Surname: "J. Kowalski"
INITIAL_SURNAME = re.compile(
    rf"\b([A-Z])\.\s*({PL_WORD}{{2,}}(?:-{PL_WORD}{{2,}})?)\b"
)

# Honorific + Name: "Pan Jan", "Pani Anna", capturing following capitalized word
HONORIFIC_NAME = re.compile(
    rf"(?i)\b(pan|pani)\s+({PL_WORD}{{2,}})\b"
)
