import re
from dataclasses import dataclass
from typing import Callable, List, Optional, Tuple, Dict, Set

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
    # additional standalone long hex
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
    # 1) Keyword-triggered (replace only the number itself)
    for m in patterns.PHONE_KEYWORD.finditer(text):
        num_span = m.span("num")
        raw = m.group("num")
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if 9 <= len(digits) <= 11:
            _add_match(res, num_span[0], num_span[1], raw, "PHONE")
    # 2) General (+48 optional, common groupings)
    for m in patterns.PHONE_GENERAL.finditer(text):
        raw = m.group("num")
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) == 9 or (len(digits) == 11 and digits.startswith("48")):
            _add_match(res, m.start("num"), m.end("num"), raw, "PHONE")
    return res

def detect_long_numbers(text: str) -> List[Match]:
    res: List[Match] = []
    # contiguous 9+ digits
    for m in patterns.LONG_NUMBER.finditer(text):
        raw = m.group(0)
        if len(raw) >= 9:
            _add_match(res, m.start(), m.end(), raw, "LONG_NUMBER")
    # 9+ digits allowing whitespace between groups
    for m in patterns.LONG_NUMBER_WS.finditer(text):
        raw = m.group(0)
        digits = ''.join(ch for ch in raw if ch.isdigit())
        if len(digits) >= 9:
            _add_match(res, m.start(), m.end(), raw, "LONG_NUMBER")
    return res

def detect_names(
    text: str,
    first_names: Optional[Set[str]] = None,
    surnames: Optional[Set[str]] = None,
) -> List[Match]:
    res: List[Match] = []
    fn = set(n.capitalize() for n in (first_names or []))
    sn = set(s.capitalize() for s in (surnames or []))

    for m in patterns.FULL_NAME.finditer(text):
        first, last = m.group(1), m.group(2)
        if fn and first.capitalize() not in fn:
            continue
        # accept hyphenated surnames; normalize with title for ALL CAPS matches
        last_norm = last.title()
        base_norm = last.split('-')[0].capitalize()
        if sn and (base_norm not in sn and last_norm not in sn and last.capitalize() not in sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    for m in patterns.INITIAL_SURNAME.finditer(text):
        initial, last = m.group(1), m.group(2)
        last_norm = last.title()
        base_norm = last.split('-')[0].capitalize()
        if sn and (base_norm not in sn and last_norm not in sn and last.capitalize() not in sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    for m in patterns.HONORIFIC_NAME.finditer(text):
        honor, name = m.group(1), m.group(2)
        if fn and name.capitalize() not in fn and name.title() not in fn:
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

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
    # Greedy non-overlapping selection by (priority desc, length desc)
    matches.sort(key=lambda m: (m.priority, (m.end - m.start)), reverse=True)
    selected: List[Match] = []
    for m in matches:
        if all(m.end <= s.start or m.start >= s.end for s in selected):
            selected.append(m)
    selected.sort(key=lambda m: m.start)
    return selected
