import hashlib
import re
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Set, Tuple

from .detectors import collect_all_matches, Match

MASK_DIGIT = "X"
MASK_LETTER = "x"

@dataclass
class AnonymizeConfig:
    strategy: str = "placeholder"   # "placeholder" | "preserve_shape" | "hash"
    hash_salt: str = "change-me"
    placeholders: Dict[str, str] = None
    enable_names: bool = True
    first_names: Optional[Set[str]] = None
    surnames: Optional[Set[str]] = None

    def __post_init__(self):
        default = {
            "IBAN": "[IBAN]",
            "CARD": "[CARD_NUMBER]",
            "UUID": "[UUID]",
            "PESEL": "[PESEL]",
            "NIP": "[NIP]",
            "REGON": "[REGON]",
            "ID_CARD": "[ID_CARD]",
            "PHONE": "[PHONE]",
            "ADDRESS": "[ADDRESS]",
            "POSTAL_CODE": "[POSTAL_CODE]",
            "TRANSACTION_ID": "[TRANSACTION_ID]",
            "LONG_NUMBER": "[LONG_NUMBER]",
            "NAME": "[NAME]",
        }
        if self.placeholders is None:
            self.placeholders = default
        else:
            # fill missing with defaults
            for k, v in default.items():
                self.placeholders.setdefault(k, v)

@dataclass
class Finding:
    start: int
    end: int
    category: str
    original: str
    replacement: str

@dataclass
class AnonymizationResult:
    text: str
    findings: List[Finding]

def mask_preserve_shape(s: str) -> str:
    out = []
    for ch in s:
        if ch.isdigit():
            out.append(MASK_DIGIT)
        elif ch.isalpha():
            out.append(MASK_LETTER)
        else:
            out.append(ch)
    return ''.join(out)

def pseudo_hash(s: str, salt: str, length: int = 10) -> str:
    h = hashlib.sha256((salt + "::" + s).encode("utf-8")).hexdigest()
    return h[:length]

def replacement_for(category: str, value: str, cfg: AnonymizeConfig) -> str:
    if cfg.strategy == "placeholder":
        return cfg.placeholders.get(category, "[REDACTED]")
    elif cfg.strategy == "preserve_shape":
        return mask_preserve_shape(value)
    elif cfg.strategy == "hash":
        return f"[{category}:{pseudo_hash(value, cfg.hash_salt)}]"
    else:
        return cfg.placeholders.get(category, "[REDACTED]")

def anonymize_text(text: str, config: Optional[AnonymizeConfig] = None) -> AnonymizationResult:
    cfg = config or AnonymizeConfig()
    matches = collect_all_matches(
        text,
        first_names=cfg.first_names,
        surnames=cfg.surnames,
        enable_names=cfg.enable_names,
    )
    findings: List[Finding] = []
    out_parts: List[str] = []
    last = 0
    for m in matches:
        if m.start < last:
            continue
        repl = replacement_for(m.category, m.value, cfg)
        out_parts.append(text[last:m.start])
        out_parts.append(repl)
        findings.append(Finding(m.start, m.end, m.category, m.value, repl))
        last = m.end
    out_parts.append(text[last:])
    return AnonymizationResult(text=''.join(out_parts), findings=findings)

def load_name_dictionaries(first_names_path: Optional[str], surnames_path: Optional[str]) -> Tuple[Optional[Set[str]], Optional[Set[str]]]:
    def load(path: Optional[str]) -> Optional[Set[str]]:
        if not path:
            return None
        names: Set[str] = set()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                name = line.strip()
                if not name or name.startswith("#"):
                    continue
                names.add(name)
        return names
    return load(first_names_path), load(surnames_path)
