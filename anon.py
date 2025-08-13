import pandas as pd
import re
import random
import string
import hashlib
from typing import Dict, List, Optional, Union
import numpy as np

class PolishDataAnonymizer:
    """
    Anonymizer specifically designed for Polish language data in pandas DataFrames.
    Handles Polish names, addresses, phone numbers, PESEL, NIP, REGON, and more.
    """
    
    def __init__(self, seed: int = 42):
        """Initialize with Polish-specific patterns and fake data."""
        random.seed(seed)
        np.random.seed(seed)
        self.replacement_cache: Dict[str, str] = {}
        
        # Polish-specific patterns
        self.patterns = {
            'pesel': r'\b\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])\d{5}\b',
            'nip': r'\b\d{3}-?\d{3}-?\d{2}-?\d{2}\b',
            'regon': r'\b\d{7,14}\b',
            'polish_phone': r'(\+48\s?)?(?:\d{2,3}[-\s]?\d{3}[-\s]?\d{3}|\d{3}[-\s]?\d{3}[-\s]?\d{3})',
            'polish_postal': r'\b\d{2}-\d{3}\b',
            'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'iban_pl': r'\bPL\d{26}\b',
            'account_number': r'\b\d{26}\b',  # Polish account number
            'long_numbers': r'\b\d{8,}\b',
            'dowod_osobisty': r'\b[A-Z]{3}\s?\d{6}\b',  # Polish ID format
            'paszport': r'\b[A-Z]{2}\d{7}\b',  # Polish passport
        }
        
        # Polish fake names
        self.polish_first_names_male = [
            'Jan', 'Andrzej', 'Krzysztof', 'Stanisław', 'Tomasz', 'Paweł',
            'Józef', 'Marcin', 'Marek', 'Michał', 'Piotr', 'Kamil',
            'Adam', 'Łukasz', 'Zbigniew', 'Ryszard', 'Dariusz', 'Henryk'
        ]
        
        self.polish_first_names_female = [
            'Anna', 'Maria', 'Katarzyna', 'Małgorzata', 'Agnieszka', 'Barbara',
            'Ewa', 'Krystyna', 'Elżbieta', 'Zofia', 'Janina', 'Teresa',
            'Magdalena', 'Monika', 'Joanna', 'Beata', 'Dorota', 'Renata'
        ]
        
        self.polish_last_names = [
            'Nowak', 'Kowalski', 'Wiśniewski', 'Wójcik', 'Kowalczyk', 'Kamiński',
            'Lewandowski', 'Zieliński', 'Szymański', 'Woźniak', 'Dąbrowski',
            'Kozłowski', 'Jankowski', 'Mazur', 'Kwiatkowski', 'Krawczyk',
            'Piotrowski', 'Grabowski', 'Nowakowski', 'Pawłowski', 'Michalski'
        ]
        
        # Polish cities
        self.polish_cities = [
            'Warszawa', 'Kraków', 'Łódź', 'Wrocław', 'Poznań', 'Gdańsk',
            'Szczecin', 'Bydgoszcz', 'Lublin', 'Białystok', 'Katowice',
            'Gdynia', 'Częstochowa', 'Radom', 'Sosnowiec', 'Toruń'
        ]
        
        # Polish street types
        self.polish_street_types = [
            'ul.', 'al.', 'pl.', 'os.', 'skwer', 'bulwar', 'park'
        ]
        
        # Polish street names
        self.polish_street_names = [
            'Marszałkowska', 'Królewska', 'Nowy Świat', 'Piękna', 'Złota',
            'Mokotowska', 'Jerozolimskie', 'Solidarity', 'Powstańców',
            'Słowackiego', 'Mickiewicza', 'Kościuszki', 'Sienkiewicza'
        ]
    
    def _generate_fake_polish_name(self, original: str) -> str:
        """Generate fake Polish name."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        # Simple heuristic: if ends with 'a', assume female
        if original.strip().split()[-1].endswith('a'):
            first_name = random.choice(self.polish_first_names_female)
        else:
            first_name = random.choice(self.polish_first_names_male)
        
        last_name = random.choice(self.polish_last_names)
        fake_name = f"{first_name} {last_name}"
        
        self.replacement_cache[original] = fake_name
        return fake_name
    
    def _generate_fake_pesel(self, original: str) -> str:
        """Generate fake PESEL number."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        # Generate fake PESEL with valid format but fake data
        year = random.randint(50, 99)  # Birth year
        month = random.randint(1, 12)
        day = random.randint(1, 28)
        serial = random.randint(100, 999)
        sex = random.randint(0, 9)
        
        # Simple checksum (not real PESEL algorithm)
        checksum = random.randint(0, 9)
        
        fake_pesel = f"{year:02d}{month:02d}{day:02d}{serial}{sex}{checksum}"
        self.replacement_cache[original] = fake_pesel
        return fake_pesel
    
    def _generate_fake_nip(self, original: str) -> str:
        """Generate fake NIP number."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        # Generate fake NIP with format XXX-XXX-XX-XX
        fake_nip = f"{random.randint(100, 999):03d}-{random.randint(100, 999):03d}-{random.randint(10, 99):02d}-{random.randint(10, 99):02d}"
        self.replacement_cache[original] = fake_nip
        return fake_nip
    
    def _generate_fake_polish_phone(self, original: str) -> str:
        """Generate fake Polish phone number."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        # Common Polish mobile prefixes
        prefixes = ['501', '502', '503', '505', '506', '507', '508', '509',
                   '510', '511', '512', '513', '514', '515', '516', '517',
                   '518', '519', '530', '531', '532', '533', '534', '535',
                   '536', '537', '538', '539', '570', '571', '572', '573',
                   '574', '575', '576', '577', '578', '579', '600', '601',
                   '602', '603', '604', '605', '606', '607', '608', '609']
        
        prefix = random.choice(prefixes)
        number = f"{random.randint(100, 999):03d}-{random.randint(100, 999):03d}"
        
        if '+48' in original:
            fake_phone = f"+48 {prefix}-{number}"
        else:
            fake_phone = f"{prefix}-{number}"
        
        self.replacement_cache[original] = fake_phone
        return fake_phone
    
    def _generate_fake_address(self, original: str) -> str:
        """Generate fake Polish address."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        street_type = random.choice(self.polish_street_types)
        street_name = random.choice(self.polish_street_names)
        house_number = random.randint(1, 200)
        apartment = random.randint(1, 50) if random.random() > 0.7 else None
        
        if apartment:
            address = f"{street_type} {street_name} {house_number}/{apartment}"
        else:
            address = f"{street_type} {street_name} {house_number}"
        
        self.replacement_cache[original] = address
        return address
    
    def _generate_fake_postal_code(self, original: str) -> str:
        """Generate fake Polish postal code."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        fake_postal = f"{random.randint(10, 99):02d}-{random.randint(100, 999):03d}"
        self.replacement_cache[original] = fake_postal
        return fake_postal
    
    def _generate_fake_city(self, original: str) -> str:
        """Generate fake Polish city."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        fake_city = random.choice(self.polish_cities)
        self.replacement_cache[original] = fake_city
        return fake_city
    
    def _generate_fake_email(self, original: str) -> str:
        """Generate fake email."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        domains = ['example.pl', 'test.com.pl', 'demo.pl', 'sample.org.pl']
        username = ''.join(random.choices(string.ascii_lowercase, k=8))
        fake_email = f"{username}@{random.choice(domains)}"
        
        self.replacement_cache[original] = fake_email
        return fake_email
    
    def _generate_fake_number(self, original: str) -> str:
        """Generate fake number maintaining length."""
        if original in self.replacement_cache:
            return self.replacement_cache[original]
        
        length = len(re.sub(r'[^\d]', '', original))
        fake_number = ''.join([str(random.randint(1, 9))] + 
                             [str(random.randint(0, 9)) for _ in range(length - 1)])
        self.replacement_cache[original] = fake_number
        return fake_number
    
    def anonymize_text(self, text: str) -> str:
        """Anonymize Polish text."""
        if pd.isna(text) or text == '':
            return text
        
        result = str(text)
        
        # PESEL numbers
        def replace_pesel(match):
            return self._generate_fake_pesel(match.group(0))
        result = re.sub(self.patterns['pesel'], replace_pesel, result)
        
        # NIP numbers
        def replace_nip(match):
            return self._generate_fake_nip(match.group(0))
        result = re.sub(self.patterns['nip'], replace_nip, result)
        
        # Polish phone numbers
        def replace_phone(match):
            return self._generate_fake_polish_phone(match.group(0))
        result = re.sub(self.patterns['polish_phone'], replace_phone, result)
        
        # Polish postal codes
        def replace_postal(match):
            return self._generate_fake_postal_code(match.group(0))
        result = re.sub(self.patterns['polish_postal'], replace_postal, result)
        
        # Email addresses
        def replace_email(match):
            return self._generate_fake_email(match.group(0))
        result = re.sub(self.patterns['email'], replace_email, result, flags=re.IGNORECASE)
        
        # ID numbers (Dowód osobisty)
        def replace_id(match):
            fake_id = f"{random.choice(['ABC', 'DEF', 'GHI'])}{random.randint(100000, 999999):06d}"
            return fake_id
        result = re.sub(self.patterns['dowod_osobisty'], replace_id, result)
        
        # Long numbers
        def replace_long_number(match):
            return self._generate_fake_number(match.group(0))
        result = re.sub(self.patterns['long_numbers'], replace_long_number, result)
        
        return result
    
    def anonymize_dataframe(self, df: pd.DataFrame, 
                          column_config: Optional[Dict[str, str]] = None,
                          auto_detect: bool = True) -> pd.DataFrame:
        """
        Anonymize a pandas DataFrame with Polish data.
        
        Args:
            df: Input DataFrame
            column_config: Dictionary mapping column names to data types
                          ('name', 'address', 'city', 'phone', 'email', 'pesel', etc.)
            auto_detect: Whether to auto-detect Polish data patterns
        
        Returns:
            Anonymized DataFrame
        """
        result_df = df.copy()
        
        # Default column mappings for common Polish column names
        default_mappings = {
            'imie': 'name',
            'imię': 'name', 
            'nazwisko': 'name',
            'nazwa': 'name',
            'pesel': 'pesel',
            'nip': 'nip',
            'telefon': 'phone',
            'tel': 'phone',
            'email': 'email',
            'e-mail': 'email',
            'adres': 'address',
            'ulica': 'address',
            'miasto': 'city',
            'kod': 'postal',
            'kod_pocztowy': 'postal',
            'dowod': 'id',
            'dowód': 'id',
        }
        
        if column_config is None:
            column_config = {}
        
        # Process each column
        for column in result_df.columns:
            column_lower = column.lower()
            data_type = column_config.get(column)
            
            # Auto-detect data type if not specified
            if data_type is None and auto_detect:
                for pattern, detected_type in default_mappings.items():
                    if pattern in column_lower:
                        data_type = detected_type
                        break
            
            # Apply specific anonymization based on data type
            if data_type == 'name':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_polish_name(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'address':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_address(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'city':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_city(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'postal':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_postal_code(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'pesel':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_pesel(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'nip':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_nip(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'phone':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_polish_phone(str(x)) if pd.notna(x) else x
                )
            elif data_type == 'email':
                result_df[column] = result_df[column].apply(
                    lambda x: self._generate_fake_email(str(x)) if pd.notna(x) else x
                )
            else:
                # General text anonymization for all other columns
                result_df[column] = result_df[column].apply(
                    lambda x: self.anonymize_text(str(x)) if pd.notna(x) else x
                )
        
        return result_df
    
    def anonymize_column(self, series: pd.Series, data_type: str = 'auto') -> pd.Series:
        """Anonymize a single pandas Series/column."""
        if data_type == 'auto':
            # Try to detect data type from first few non-null values
            sample = series.dropna().head(10)
            # Basic detection logic here
            data_type = 'text'
        
        if data_type == 'name':
            return series.apply(lambda x: self._generate_fake_polish_name(str(x)) if pd.notna(x) else x)
        elif data_type == 'pesel':
            return series.apply(lambda x: self._generate_fake_pesel(str(x)) if pd.notna(x) else x)
        else:
            return series.apply(lambda x: self.anonymize_text(str(x)) if pd.notna(x) else x)
    
    def get_replacement_mapping(self) -> Dict[str, str]:
        """Get the mapping of original -> anonymized values."""
        return self.replacement_cache.copy()
    
    def save_mapping(self, filename: str) -> None:
        """Save replacement mapping to file."""
        import json
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.replacement_cache, f, indent=2, ensure_ascii=False)
        print(f"Mapping saved to {filename}")
