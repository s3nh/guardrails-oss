from dataclasses import dataclass

@dataclass
class AnonymizationConfig:
    aggressive_numeric_redaction: bool = True
    min_numeric_length: int = 2            # Numbers shorter than this may be skipped if preserve_small_integers
    preserve_small_integers: bool = False  # Keep 0-9 (or maybe 0-12) if True
    small_integer_max: int = 12
    hash_formatted_numbers: bool = True
    normalization_strategy: str = "digits_only"  # digits_only | canonical | none
    general_alphanumeric_id_redaction: bool = True
    alphanumeric_min_length: int = 6
    include_shape_metadata: bool = True
    salt_env_var: str = "PII_SALT"
    # Existing behavior toggles:
    retain_credit_card_last4: bool = True
