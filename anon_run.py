import pandas as pd
import numpy as np
from polish_anonymizer import PolishDataAnonymizer

def process_your_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process your actual DataFrame with Polish anonymization.
    Customize this function for your specific needs.
    """
    
    # Initialize anonymizer
    anonymizer = PolishDataAnonymizer(seed=42)  # Use consistent seed for reproducible results
    
    # Option 1: Let auto-detection handle everything
    anonymized_df = anonymizer.anonymize_dataframe(df, auto_detect=True)
    
    # Option 2: Specify exact column mappings for better control
    # Uncomment and customize this section:
    """
    column_config = {
        'your_name_column': 'name',
        'your_pesel_column': 'pesel', 
        'your_phone_column': 'phone',
        'your_email_column': 'email',
        'your_address_column': 'address',
        'your_city_column': 'city',
        'your_postal_column': 'postal',
        'your_nip_column': 'nip',
        # Add more mappings as needed
    }
    
    anonymized_df = anonymizer.anonymize_dataframe(df, column_config=column_config)
    """
    
    return anonymized_df

def anonymize_specific_columns(df: pd.DataFrame, columns_to_anonymize: list) -> pd.DataFrame:
    """Anonymize only specific columns."""
    
    anonymizer = PolishDataAnonymizer(seed=42)
    result_df = df.copy()
    
    for column in columns_to_anonymize:
        if column in df.columns:
            result_df[column] = anonymizer.anonymize_column(df[column], data_type='auto')
        else:
            print(f"Warning: Column '{column}' not found in DataFrame")
    
    return result_df

def batch_anonymize_files(file_paths: list, output_dir: str = 'anonymized/'):
    """Anonymize multiple CSV files."""
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    anonymizer = PolishDataAnonymizer(seed=42)
    
    for file_path in file_paths:
        try:
            # Read CSV
            df = pd.read_csv(file_path, encoding='utf-8')
            
            # Anonymize
            anonymized_df = anonymizer.anonymize_dataframe(df, auto_detect=True)
            
            # Save
            output_file = os.path.join(output_dir, f"anonymized_{os.path.basename(file_path)}")
            anonymized_df.to_csv(output_file, index=False, encoding='utf-8')
            
            print(f"Anonymized: {file_path} -> {output_file}")
            
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")
    
    # Save mapping
    mapping_file = os.path.join(output_dir, 'anonymization_mapping.json')
    anonymizer.save_mapping(mapping_file)

# Example usage for your DataFrame:
if __name__ == "__main__":
    # Example 1: Load your DataFrame
    # df = pd.read_csv('your_polish_data.csv', encoding='utf-8')
    
    # Example 2: Create a sample DataFrame to test
    sample_data = {
        'customer_name': ['Marek Kowalczyk', 'Agata Zielińska', 'Tomasz Nowicki'],
        'customer_pesel': ['85021256789', '90040198765', '78111287654'],
        'phone_number': ['501-234-567', '+48 602-345-678', '512 987 654'],
        'email_address': ['marek@example.pl', 'agata.z@gmail.com', 'tomasz.n@wp.pl'],
        'home_address': ['ul. Długa 15/3', 'al. Niepodległości 89', 'ul. Krótka 7'],
        'city_name': ['Warszawa', 'Poznań', 'Wrocław'],
        'zip_code': ['01-234', '60-001', '50-123'],
        'company_nip': ['123-45-67-890', '987-65-43-210', '456-78-90-123'],
        'salary': [4500, 6800, 5200],
        'department': ['IT', 'HR', 'Finance']
    }
    
    df = pd.DataFrame(sample_data)
    
    print("Original DataFrame:")
    print(df)
    print("\n" + "="*100 + "\n")
    
    # Anonymize the DataFrame
    anonymized_df = process_your_dataframe(df)
    
    print("Anonymized DataFrame:")
    print(anonymized_df)
    
    # Save to file
    anonymized_df.to_csv('anonymized_polish_data.csv', index=False, encoding='utf-8')
    print("\nAnonymized data saved to 'anonymized_polish_data.csv'")
