import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Set

from . import patterns
from .checksums import (
    iban_valid,
    luhn_valid,
    pesel_valid,
    nip_valid,
    regon_valid,
    polish_id_card_valid,
)

@dataclass
class Match:
    start: int
    end: int
    value: str
    category: str
    priority: int

CategoryPriority: Dict[str, int] = {
    "IBAN": 100,
    "CARD": 95,
    "UUID": 90,
    "PESEL": 85,
    "NIP": 80,
    "REGON": 78,
    "ID_CARD": 75,
    "PHONE": 72,
    "ADDRESS": 70,
    "POSTAL_CODE": 65,
    "TRANSACTION_ID": 60,
    "LONG_NUMBER": 55,
    "NAME": 10,
}

def _add_match(matches: List[Match], start: int, end: int, value: str, category: str):
    matches.append(Match(start, end, value, category, CategoryPriority.get(category, 0)))

def detect_iban(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.IBAN_CANDIDATE.finditer(text):
        raw = m.group(0)
        stripped = ''.join(ch for ch in raw if ch.isalnum()).upper()
        if iban_valid(stripped):
            _add_match(res, m.start(), m.end(), raw, "IBAN")
    return res

def detect_card(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.CARD_CANDIDATE.finditer(text):
        raw = m.group(0)
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if 13 <= len(digits) <= 19 and luhn_valid(digits):
            _add_match(res, m.start(), m.end(), raw, "CARD")
    return res

def detect_pesel(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.PESEL_CANDIDATE.finditer(text):
        raw = m.group(0)
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 11 and pesel_valid(digits):
            _add_match(res, m.start(), m.end(), raw, "PESEL")
    return res

def detect_nip(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.NIP_CANDIDATE.finditer(text):
        raw = m.group(0)
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 10 and nip_valid(digits):
            _add_match(res, m.start(), m.end(), raw, "NIP")
    return res

def detect_regon(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.REGON14_CANDIDATE.finditer(text):
        raw = m.group(0)
        if regon_valid(raw):
            _add_match(res, m.start(), m.end(), raw, "REGON")
    for m in patterns.REGON9_CANDIDATE.finditer(text):
        raw = m.group(0)
        if regon_valid(raw):
            _add_match(res, m.start(), m.end(), raw, "REGON")
    return res

def detect_id_card(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.IDCARD_CANDIDATE.finditer(text):
        raw = m.group(0)
        normalized = ''.join(ch for ch in raw if ch.isalnum()).upper()
        if polish_id_card_valid(normalized):
            _add_match(res, m.start(), m.end(), raw, "ID_CARD")
    return res

def detect_postal_code(text: str) -> List[Match]:
    return [Match(m.start(), m.end(), m.group(0), "POSTAL_CODE", CategoryPriority["POSTAL_CODE"])
            for m in patterns.POSTAL_CODE.finditer(text)]

def detect_uuid(text: str) -> List[Match]:
    return [Match(m.start(), m.end(), m.group(0), "UUID", CategoryPriority["UUID"])
            for m in patterns.UUID_CANDIDATE.finditer(text)]

def detect_transaction_ids(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.TRANSACTION_BY_KEYWORD.finditer(text):
        token = m.group(1)
        if token:
            _add_match(res, m.start(1), m.end(1), token, "TRANSACTION_ID")
    for m in patterns.LONG_HEX.finditer(text):
        token = m.group(0)
        res.append(Match(m.start(), m.end(), token, "TRANSACTION_ID", CategoryPriority["TRANSACTION_ID"]))
    return res

def detect_addresses(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.ADDRESS_LINE.finditer(text):
        _add_match(res, m.start(), m.end(), m.group(0), "ADDRESS")
    return res

def detect_phone(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.PHONE_KEYWORD.finditer(text):
        num_span = m.span("num")
        raw = m.group("num")
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if 9 <= len(digits) <= 11:
            _add_match(res, num_span[0], num_span[1], raw, "PHONE")
    for m in patterns.PHONE_GENERAL.finditer(text):
        raw = m.group("num")
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 9 or (len(digits) == 11 and digits.startswith("48")):
            _add_match(res, m.start("num"), m.end("num"), raw, "PHONE")
    return res

def detect_long_numbers(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.LONG_NUMBER.finditer(text):
        raw = m.group(0)
        if len(raw) >= 9:
            _add_match(res, m.start(), m.end(), raw, "LONG_NUMBER")
    for m in patterns.LONG_NUMBER_WS.finditer(text):
        raw = m.group(0)
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) >= 9:
            _add_match(res, m.start(), m.end(), raw, "LONG_NUMBER")
    return res

# ======================
# Name detection helpers
# ======================

def _surname_variant_candidates(token: str) -> Set[str]:
    """
    Generate title/capitalized candidates for a surname token, including common
    feminine<->masculine Polish suffix alternations:
      - ska <-> ski, cka <-> cki, dzka <-> dzki
    """
    t = token.strip()
    lower = t.lower()
    cands: Set[str] = set()
    # base forms
    cands.add(t.capitalize())
    cands.add(t.title())
    # feminine ↔ masculine alternations
    suffix_map = {
        "ska": "ski",
        "cka": "cki",
        "dzka": "dzki",
    }
    for fem, masc in suffix_map.items():
        if lower.endswith(fem):
            root = t[: -len(fem)]
            cands.add((root + fem).capitalize())
            cands.add((root + masc).capitalize())
        if lower.endswith(masc):
            root = t[: -len(masc)]
            cands.add((root + masc).capitalize())
            cands.add((root + fem).capitalize())
    return cands

def _surname_matches_dictionary(surname: str, surnames_dict: Optional[Set[str]]) -> bool:
    """
    True if any part of a (possibly hyphenated) surname matches the dictionary,
    considering feminine/masculine alternations. If no dictionary is provided,
    return False (to avoid false positives for standalone surnames).
    """
    if not surnames_dict:
        return False
    parts = surname.split("-")
    for part in parts:
        for cand in _surname_variant_candidates(part):
            if cand in surnames_dict:
                return True
    # also try the whole joined token just in case dictionary includes hyphenated forms
    for cand in _surname_variant_candidates(surname):
        if cand in surnames_dict:
            return True
    return False

def detect_names(
    text: str,
    first_names: Optional[Set[str]] = None,
    surnames: Optional[Set[str]] = None,
) -> List[Match]:
    res: List[Match] = []
    # Normalize dictionaries to Title/Capitalized for case-insensitive match
    fn = set(n.capitalize() for n in (first_names or []))
    sn = set(s.capitalize() for s in (surnames or []))

    # Full name: Firstname + Surname (hyphenated supported)
    for m in patterns.FULL_NAME.finditer(text):
        first, last = m.group(1), m.group(2)
        # Gate by first-name dictionary if provided
        if fn and first.capitalize() not in fn and first.title() not in fn:
            continue
        # Gate by surname dictionary if provided (any hyphen part, with variant mapping)
        if sn and not _surname_matches_dictionary(last, sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    # Initial + Surname
    for m in patterns.INITIAL_SURNAME.finditer(text):
        last = m.group(2)
        if sn and not _surname_matches_dictionary(last, sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    # Honorific + Name (firstname only)
    for m in patterns.HONORIFIC_NAME.finditer(text):
        name = m.group(2)
        if fn and name.capitalize() not in fn and name.title() not in fn:
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    return res

def detect_hyphenated_surname_only(
    text: str,
    surnames: Optional[Set[str]] = None,
) -> List[Match]:
    """
    Detect standalone hyphenated surnames like 'Doe-Świerczewska' even without
    a preceding firstname. This is DICTIONARY-GATED to avoid false positives:
    at least one hyphen part (or the whole token) must match the surnames dict,
    considering feminine/masculine alternations.
    """
    res: List[Match] = []
    sn = set(s.capitalize() for s in (surnames or []))
    if not sn:
        return res  # require dictionary to keep precision
    for m in patterns.HYPHENATED_SURNAME_ONLY.finditer(text):
        token = m.group(1)
        # Heuristic: ensure it's name-like (each part starts with a letter and looks capitalized or ALL CAPS)
        parts = token.split("-")
        looks_named = all(p and p[0].isalpha() and (p[0].isupper() or token.isupper()) for p in parts)
        if not looks_named:
            continue
        if _surname_matches_dictionary(token, sn):
            res.append(Match(m.start(1), m.end(1), token, "NAME", CategoryPriority["NAME"]))
    return res

def collect_all_matches(
    text: str,
    first_names: Optional[Set[str]] = None,
    surnames: Optional[Set[str]] = None,
    enable_names: bool = True,
) -> List[Match]:
    matches: List[Match] = []
    for detector in (
        detect_iban,
        detect_card,
        detect_uuid,
        detect_pesel,
        detect_nip,
        detect_regon,
        detect_id_card,
        detect_phone,
        detect_addresses,
        detect_postal_code,
        detect_transaction_ids,
        detect_long_numbers,
    ):
        matches.extend(detector(text))
    if enable_names:
        matches.extend(detect_names(text, first_names, surnames))
        # Standalone hyphenated surnames (dictionary-gated)
        matches.extend(detect_hyphenated_surname_only(text, surnames))
    # Greedy non-overlapping selection by (priority desc, length desc)
    matches.sort(key=lambda m: (m.priority, (m.end - m.start)), reverse=True)
    selected: List[Match] = []
    for m in matches:
        if all(m.end <= s.start or m.start >= s.end for s in selected):
            selected.append(m)
    selected.sort(key=lambda m: m.start)
    return selected
