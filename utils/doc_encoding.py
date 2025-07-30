import base64
import io
import pdfplumber

def read_base64_pdf(base64_pdf):
    """
    Read a base64 encoded PDF using pdfplumber
    
    Args:
        base64_pdf (str): Base64 encoded PDF string
        
    Returns:
        str: Extracted text from the PDF
    """
    # Decode the base64 string to binary
    pdf_bytes = base64.b64decode(base64_pdf)
    
    # Create a BytesIO object
    pdf_file = io.BytesIO(pdf_bytes)
    
    # Extract text using pdfplumber
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() or ""
            extracted_text += "\n\n"  # Add spacing between pages
    
    return extracted_text

# Example usage
if __name__ == "__main__":
    # This would be your base64 encoded PDF string
    base64_pdf_data = "YOUR_BASE64_ENCODED_PDF_STRING_HERE"
    
    try:
        text = read_base64_pdf(base64_pdf_data)
        print("PDF Text Content:")
        print(text)
    except Exception as e:
        print(f"Error processing PDF: {e}")
