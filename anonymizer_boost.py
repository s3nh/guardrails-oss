import os, re, hashlib
from typing import List, Dict
from dataclasses import dataclass
import spacy
from config import AnonymizationConfig

nlp = spacy.load("en_core_web_trf")

BASE_PATTERNS = {
    "EMAIL": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "PHONE": re.compile(r"""(?x)(\+?\d{1,3}[\s-]?)?(\(?\d{3}\)?[\s-]?)?\d{3}[\s-]?\d{4}"""),
    "CREDIT_CARD": re.compile(r"\b(?:\d[ -]*?){13,19}\b"),
    "SSN": re.compile(r"\b(?!000|666|9\d\d)\d{3}[- ]?(?!00)\d{2}[- ]?(?!0000)\d{4}\b"),
    "IPV4": re.compile(r"\b(?:(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b"),
    "ADDRESS_FRAGMENT": re.compile(
        r"\b\d{1,6}\s+(?:[A-Za-z0-9'\.-]+\s){0,5}(Street|St|Road|Rd|Avenue|Ave|Boulevard|Blvd|Lane|Ln|Court|Ct|Drive|Dr)\b",
        re.IGNORECASE
    )
}

GENERIC_NUMERIC_FORMATTED = re.compile(r"\b\d[\d\-./_,]*\d\b")
GENERIC_INTEGER = re.compile(r"\b\d+\b")
DECIMAL_NUMBER = re.compile(r"\b\d+\.\d+\b")
ALPHANUM_ID = re.compile(r"\b(?=[A-Za-z0-9]*[A-Za-z])(?=[A-Za-z0-9]*\d)[A-Za-z0-9]{6,}\b")
GUID_PATTERN = re.compile(r"\b[0-9a-fA-F]{8}-?(?:[0-9a-fA-F]{4}-?){3}[0-9a-fA-F]{12}\b")
HEX_LONG = re.compile(r"\b[0-9a-fA-F]{16,}\b")

def luhn_valid(number: str) -> bool:
    digits = [int(d) for d in re.sub(r"\D", "", number)]
    if len(digits) < 13: return False
    checksum = 0
    parity = len(digits) % 2
    for i, d in enumerate(digits):
        if i % 2 == parity:
            d = d * 2
            if d > 9: d -= 9
        checksum += d
    return checksum % 10 == 0

def stable_hash(value: str, salt: str) -> str:
    return hashlib.sha256((salt + value).encode()).hexdigest()[:16]

@dataclass
class EntitySpan:
    start: int
    end: int
    label: str
    text: str
    priority: int

PRIORITY = {
    "CREDIT_CARD": 110,
    "SSN": 105,
    "EMAIL": 100,
    "PHONE": 95,
    "IPV4": 90,
    "ADDRESS": 85,
    "GENERIC_NUMBER": 50,
    "ALPHANUM_ID": 55,
    "PERSON": 60,
    "ORG": 55,
    "GPE": 50,
    "LOC": 50
}

def detect_base(text: str) -> List[EntitySpan]:
    spans = []
    for label, pattern in BASE_PATTERNS.items():
        for m in pattern.finditer(text):
            raw = m.group(0)
            if label == "CREDIT_CARD" and not luhn_valid(raw):
                continue
            mapped = "ADDRESS" if label == "ADDRESS_FRAGMENT" else label
            spans.append(EntitySpan(m.start(), m.end(), mapped, raw, PRIORITY.get(mapped, 10)))
    return spans

def detect_ner(text: str) -> List[EntitySpan]:
    doc = nlp(text)
    out = []
    for ent in doc.ents:
        if ent.label_ in ("PERSON","ORG","GPE","LOC"):
            out.append(EntitySpan(ent.start_char, ent.end_char, ent.label_, ent.text, PRIORITY.get(ent.label_, 10)))
    return out

def span_overlap(a: EntitySpan, b: EntitySpan) -> bool:
    return not (a.end <= b.start or a.start >= b.end)

def merge_spans(spans: List[EntitySpan]) -> List[EntitySpan]:
    spans_sorted = sorted(spans, key=lambda s: (s.start, -s.priority))
    result = []
    for s in spans_sorted:
        replaced = False
        to_remove = []
        for r in result:
            if span_overlap(s, r):
                if s.priority > r.priority:
                    to_remove.append(r)
                else:
                    replaced = True
                    break
        if replaced:
            continue
        for r in to_remove:
            result.remove(r)
        result.append(s)
    return sorted(result, key=lambda s: s.start)

def extract_shape(num_str: str) -> str:
    return re.sub(r"\d", "D", num_str)

def normalize_number(num_str: str, strategy: str) -> str:
    if strategy == "digits_only":
        return re.sub(r"\D", "", num_str)
    if strategy == "canonical":
        digits_only = re.sub(r"\D", "", num_str)
        shape = extract_shape(num_str)
        return f"{digits_only}|{shape}"
    return num_str

def detect_generic_numbers(text: str, existing: List[EntitySpan], cfg: AnonymizationConfig) -> List[EntitySpan]:
    if not cfg.aggressive_numeric_redaction:
        return []
    occupied = [(s.start, s.end) for s in existing]

    def overlaps_any(start: int, end: int) -> bool:
        for a, b in occupied:
            if not (end <= a or start >= b):
                return True
        return False

    spans = []
    patterns = [DECIMAL_NUMBER, GENERIC_NUMERIC_FORMATTED, GENERIC_INTEGER]
    for pat in patterns:
        for m in pat.finditer(text):
            s, e = m.start(), m.end()
            if overlaps_any(s, e):
                continue
            token = m.group(0)
            digits_only = re.sub(r"\D", "", token)
            if cfg.preserve_small_integers and digits_only.isdigit():
                val_int = int(digits_only) if digits_only else None
                if val_int is not None and val_int <= cfg.small_integer_max and len(digits_only) < cfg.min_numeric_length:
                    continue
            if len(digits_only) < cfg.min_numeric_length:
                continue
            spans.append(EntitySpan(s, e, "GENERIC_NUMBER", token, PRIORITY["GENERIC_NUMBER"]))
    return spans

def detect_alphanum_ids(text: str, existing: List[EntitySpan], cfg: AnonymizationConfig) -> List[EntitySpan]:
    if not cfg.general_alphanumeric_id_redaction:
        return []
    occupied = [(s.start, s.end) for s in existing]

    def overlaps_any(start: int, end: int) -> bool:
        for a, b in occupied:
            if not (end <= a or start >= b):
                return True
        return False

    spans = []
    for pattern in (GUID_PATTERN, HEX_LONG, ALPHANUM_ID):
        for m in pattern.finditer(text):
            s, e = m.start(), m.end()
            if overlaps_any(s, e):
                continue
            token = m.group(0)
            if len(token) < cfg.alphanumeric_min_length:
                continue
            spans.append(EntitySpan(s, e, "ALPHANUM_ID", token, PRIORITY["ALPHANUM_ID"]))
    return spans

def transform(entity: EntitySpan, salt: str, counters: Dict, cfg: AnonymizationConfig) -> str:
    if entity.label == "PERSON":
        idx = counters.setdefault("PERSON", 0) + 1
        counters["PERSON"] = idx
        return f"[NAME_{idx}]"
    if entity.label == "EMAIL":
        return f"[EMAIL_{stable_hash(entity.text.lower(), salt)}]"
    if entity.label == "PHONE":
        return "[PHONE]"
    if entity.label == "CREDIT_CARD":
        digits = re.sub(r"\D", "", entity.text)
        if cfg.retain_credit_card_last4 and len(digits) >= 4:
            last4 = digits[-4:]
            return f"[CARD_{stable_hash(digits, salt)}_LAST4_{last4}]"
        return f"[CARD_{stable_hash(digits, salt)}]"
    if entity.label == "SSN":
        return "[SSN]"
    if entity.label == "ADDRESS":
        return "[ADDRESS]"
    if entity.label in ("ORG","GPE","LOC"):
        return f"[{entity.label}]"
    if entity.label == "IPV4":
        return "[IP]"
    if entity.label == "GENERIC_NUMBER":
        norm = normalize_number(entity.text, cfg.normalization_strategy)
        h = stable_hash(norm, salt)
        digits_only = re.sub(r"\D", "", entity.text)
        length_digits = len(digits_only)
        if cfg.include_shape_metadata and cfg.normalization_strategy != "canonical":
            shape = extract_shape(entity.text)
            # All variables precomputed; no backslashes in f-string expression parts
            return f"[NUM_{h}_S={shape}_L={length_digits}]"
        return f"[NUM_{h}]"
    if entity.label == "ALPHANUM_ID":
        norm = entity.text.upper()
        h = stable_hash(norm, salt)
        return f"[ID_{h}_L={len(entity.text)}]"
    return "[REDACTED]"

def anonymize(text: str, cfg: AnonymizationConfig) -> dict:
    salt = os.environ.get(cfg.salt_env_var, "change_me")
    base_spans = detect_base(text)
    ner_spans = detect_ner(text)
    merged = merge_spans(base_spans + ner_spans)
    gen_num_spans = detect_generic_numbers(text, merged, cfg)
    merged = merge_spans(merged + gen_num_spans)
    alphanum_spans = detect_alphanum_ids(text, merged, cfg)
    merged = merge_spans(merged + alphanum_spans)
    counters = {}
    output = []
    last = 0
    entities_meta = []
    for span in merged:
        output.append(text[last:span.start])
        replacement = transform(span, salt, counters, cfg)
        output.append(replacement)
        entities_meta.append({
            "label": span.label,
            "original": span.text,
            "replacement": replacement,
            "start": span.start,
            "end": span.end
        })
        last = span.end
    output.append(text[last:])
    return {
        "sanitized_text": "".join(output),
        "entities": entities_meta
    }

if __name__ == "__main__":
    from config import AnonymizationConfig
    cfg = AnonymizationConfig()
    sample = "John paid 1,234.56 on 2025-08-26; ref ID AB12CD34; phone 321-123-1234; hex 9f3a5b7c9d2e4f10."
    result = anonymize(sample, cfg)
    print(result["sanitized_text"])
    for e in result["entities"]:
        print(e)
