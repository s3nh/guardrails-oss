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
    "ADDRESS": 70,
    "POSTAL_CODE": 65,
    "TRANSACTION_ID": 60,
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
    # additional standalone long hex (avoid clashing with UUID which is separate)
    for m in patterns.LONG_HEX.finditer(text):
        token = m.group(0)
        # Exclude if this span overlaps with an existing match (UUID may have been added)
        res.append(Match(m.start(), m.end(), token, "TRANSACTION_ID", CategoryPriority["TRANSACTION_ID"]))
    return res

def detect_addresses(text: str) -> List[Match]:
    res: List[Match] = []
    for m in patterns.ADDRESS_LINE.finditer(text):
        _add_match(res, m.start(), m.end(), m.group(0), "ADDRESS")
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
        # Basic heuristics: require dictionary match for first name if provided
        if fn and first.capitalize() not in fn:
            continue
        # Optional surname dict if provided
        if sn and (last.split('-')[0].capitalize() not in sn and last.capitalize() not in sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    for m in patterns.INITIAL_SURNAME.finditer(text):
        initial, last = m.group(1), m.group(2)
        if sn and (last.split('-')[0].capitalize() not in sn and last.capitalize() not in sn):
            continue
        res.append(Match(m.start(), m.end(), m.group(0), "NAME", CategoryPriority["NAME"]))

    for m in patterns.HONORIFIC_NAME.finditer(text):
        honor, name = m.group(1), m.group(2)
        if fn and name.capitalize() not in fn:
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
        detect_addresses,
        detect_postal_code,
        detect_transaction_ids,
    ):
        matches.extend(detector(text))
    if enable_names:
        matches.extend(detect_names(text, first_names, surnames))
    # Deduplicate overlaps: keep highest priority, then longest, then earliest
    matches.sort(key=lambda m: (m.start, -(m.end - m.start), -m.priority))
    non_overlapping: List[Match] = []
    occupied = []  # list of (start,end,priority)
    for m in matches:
        overlap = False
        for kept in non_overlapping:
            if not (m.end <= kept.start or m.start >= kept.end):
                # overlap, keep the one with higher priority or longer span
                if (m.priority > kept.priority) or (m.priority == kept.priority and (m.end - m.start) > (kept.end - kept.start)):
                    # replace kept if m completely covers or is better
                    # but simpler: mark overlap and later we'll re-resolve by building non-overlapping sorted by priority
                    overlap = True
                    break
                else:
                    overlap = True
                    break
        if not overlap:
            non_overlapping.append(m)
    # Re-run a more robust selection: sort by (priority desc, length desc), greedily choose non-overlapping
    matches.sort(key=lambda m: (m.priority, (m.end - m.start)), reverse=True)
    selected: List[Match] = []
    for m in matches:
        if all(m.end <= s.start or m.start >= s.end for s in selected):
            selected.append(m)
    selected.sort(key=lambda m: m.start)
    return selected
