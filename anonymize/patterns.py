import re

# Common Polish letters
PL_WORD = r"[A-Za-zĄĆĘŁŃÓŚŻŹąćęłńóśżź]"

# IBAN: capture alnum with optional whitespace/dashes between chars; start with two letters
IBAN_CANDIDATE = re.compile(r"\b([A-Z]{2}[0-9]{2}(?:[\s-]?[A-Z0-9]){11,})\b", re.IGNORECASE)

# Card numbers 13-19 digits, allow whitespace/dashes; starting digits 2-6 to reduce FP
CARD_CANDIDATE = re.compile(r"(?<!\d)(?:[2-6]\d(?:[\s-]?\d)){12,18}\b")

# PESEL: 11 digits with optional separators (space or hyphen)
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

# Address heuristics (street line) — improved
ADDRESS_LINE = re.compile(
    r"""(?ix)
    \b
    (?:
        ul\.|ulica|al\.|aleja|pl\.|plac|os\.|osiedle|rynek|rondo|bulwar|skwer|droga|deptak
    )
    \s+
    (                           # street name
        """ + PL_WORD + r"""[A-Za-zĄĆĘŁŃÓŚŻŹąćęłńóśżź\.\- ]{0,60}?
        (?:\bI{1,3}\b|\bIV\b|\bV\b|\bVI\b|\bVII\b|\bVIII\b|\bIX\b|\bX\b)?   # optional Roman numeral
    )
    \s+
    (                           # house/building and optional unit
        \d+[A-Za-z]?            # number with optional letter
        (?:\s*(?:/\s*|\s+)(?:\d+[A-Za-z]?))?   # optional apartment like /37 or space 37
        (?:\s*(?:m\.|lok\.)\s*\d+[A-Za-z]?)?   # optional m./lok. marker
    )
    (?:\s*,\s*
        (\d{2}-\d{3})           # optional postal code
        \s+
        ([A-ZĄĆĘŁŃÓŚŻŹ][A-Za-zĄĆĘŁŃÓŚŻŹąćęłńóśżź\- ]{1,40})  # optional city
    )?
    """,
)

# Full name: Firstname + Surname (supports multi-part hyphenated surnames)
FULL_NAME = re.compile(
    rf"\b({PL_WORD}{{2,}})\s+({PL_WORD}{{2,}}(?:-{PL_WORD}{{2,}})*?)\b"
)

# Initial + Surname: "J. Kowalski" (surname can be hyphenated)
INITIAL_SURNAME = re.compile(
    rf"\b([A-Z])\.\s*({PL_WORD}{{2,}}(?:-{PL_WORD}{{2,}})*)\b"
)

# Honorific + Name: "Pan Jan", "Pani Anna"
HONORIFIC_NAME = re.compile(
    rf"(?i)\b(pan|pani)\s+({PL_WORD}{{2,}})\b"
)

# Phone numbers (Polish)
PHONE_KEYWORD = re.compile(
    r"""(?ix)
    \b
    (?:tel(?:efon)?|kom\.?|mobile|kontakt(?:\s+tel\.)?)
    \s*[:\-]?\s*
    (?P<num>
        (?:\+?\s*48[\s\-.]?)?
        (?:
            \(\s*\d{2}\s*\)[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}
            |
            \d{2}[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}
            |
            \d{3}[\s\-.]?\d{3}[\s\-.]?\d{3}
        )
    )
    \b
    """
)

PHONE_GENERAL = re.compile(
    r"""(?ix)
    (?<!\d)
    (?P<num>
        (?:\+?\s*48[\s\-.]?)?
        (?:
            \(\s*\d{2}\s*\)[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}
            |
            \d{2}[\s\-.]?\d{3}[\s\-.]?\d{2}[\s\-.]?\d{2}
            |
            \d{3}[\s\-.]?\d{3}[\s\-.]?\d{3}
        )
    )
    (?!\d)
    """
)

# Generic long numbers (solid)
LONG_NUMBER = re.compile(r"(?<!\d)\d{9,}(?!\d)")

# Generic long numbers split by whitespace: count digits and ensure total >= 9
LONG_NUMBER_WS = re.compile(r"(?<!\d)(?:\d+\s+){1,}\d+(?!\d)")

# Standalone hyphenated surname token (e.g., "Doe-Świerczewska") — dictionary-gated in detectors
HYPHENATED_SURNAME_ONLY = re.compile(rf"\b({PL_WORD}{{2,}}(?:-{PL_WORD}{{2,}})+)\b")
