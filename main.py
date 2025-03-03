from src.invoiceValidator import InvoiceExtractor
import json
from dotenv import load_dotenv

# Example usage
if __name__ == "__main__":
    load_dotenv()
    file_path = "samples/invoice2.pdf"  # Replace with your file
    extractor = InvoiceExtractor()
    result = extractor.extract_invoice_details(file_path)

    print("Extracted Invoice Details:")
    print(result)