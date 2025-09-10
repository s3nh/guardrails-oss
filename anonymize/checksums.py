import string

def luhn_valid(num: str) -> bool:
    s = ''.join(ch for ch in num if ch.isdigit())
    if not 13 <= len(s) <= 19:
        return False
    total = 0
    reverse = s[::-1]
    for i, ch in enumerate(reverse):
        d = ord(ch) - 48
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def pesel_valid(pesel: str) -> bool:
    s = ''.join(ch for ch in pesel if ch.isdigit())
    if len(s) != 11:
        return False
    weights = [1, 3, 7, 9, 1, 3, 7, 9, 1, 3]
    control = sum(int(s[i]) * weights[i] for i in range(10))
    control = (10 - (control % 10)) % 10
    return control == int(s[10])

def nip_valid(nip: str) -> bool:
    s = ''.join(ch for ch in nip if ch.isdigit())
    if len(s) != 10:
        return False
    weights = [6, 5, 7, 2, 3, 4, 5, 6, 7]
    control = sum(int(s[i]) * weights[i] for i in range(9)) % 11
    if control == 10:
        return False
    return control == int(s[9])

def regon_valid(regon: str) -> bool:
    s = ''.join(ch for ch in regon if ch.isdigit())
    if len(s) == 9:
        weights = [8, 9, 2, 3, 4, 5, 6, 7]
        control = sum(int(s[i]) * weights[i] for i in range(8)) % 11
        if control == 10:
            control = 0
        return control == int(s[8])
    elif len(s) == 14:
        # Validate base 9 first
        if not regon_valid(s[:9]):
            return False
        weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5, 6]
        control = sum(int(s[i]) * weights[i] for i in range(13)) % 11
        if control == 10:
            control = 0
        return control == int(s[13])
    else:
        return False

def polish_id_card_valid(doc: str) -> bool:
    # Format: 3 letters + 6 digits; 4th char (index 3) is check digit
    # Validation: positions [0,1,2,4,5,6,7,8] with weights [7,3,1,7,3,1,7,3]
    # Letters map A=10..Z=35
    s = ''.join(ch for ch in doc if ch.isalnum()).upper()
    if len(s) != 9:
        return False
    if not (s[:3].isalpha() and s[3:].isdigit()):
        return False
    def char_val(c: str) -> int:
        if c.isdigit():
            return ord(c) - 48
        return 10 + (ord(c) - 65)  # A=10, B=11 ... Z=35
    weights = [7, 3, 1, 7, 3, 1, 7, 3]
    positions = [0, 1, 2, 4, 5, 6, 7, 8]
    total = sum(char_val(s[pos]) * weights[i] for i, pos in enumerate(positions))
    return total % 10 == int(s[3])

def iban_valid(iban: str) -> bool:
    # General IBAN: 15-34 chars, checksum mod 97 == 1
    raw = ''.join(ch for ch in iban if ch.isalnum()).upper()
    if len(raw) < 15 or len(raw) > 34:
        return False
    # Optional stricter check for PL: length 28 and all digits after country+check
    if raw.startswith("PL") and len(raw) != 28:
        return False
    rearranged = raw[4:] + raw[:4]
    # Convert letters
    def char_to_num(c: str) -> str:
        if c.isdigit():
            return c
        return str(10 + ord(c) - ord('A'))
    num_str_iter = (char_to_num(c) for c in rearranged)
    # Streaming mod 97
    remainder = 0
    chunk = ""
    for part in num_str_iter:
        chunk += part
        # Process in blocks to keep ints small
        while len(chunk) >= 7:
            remainder = int(str(remainder) + chunk[:7]) % 97
            chunk = chunk[7:]
    if chunk:
        remainder = int(str(remainder) + chunk) % 97
    return remainder == 1
