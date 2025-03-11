import json
import pdfplumber
import xml.etree.ElementTree as ET
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel
from typing import Optional
from src.templates import Invoice, Prompts
import sqlite3

# Load environment variables
load_dotenv()

class InvoiceExtractor:
    """Handles validation and information extraction of invoices"""
    
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")

    def extract_text_from_pdf(self, file):
        """Extract text from a PDF file (file is a BytesIO object)."""
        text = ""
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                extracted_text = page.extract_text()
                if extracted_text:
                    text += extracted_text + "\n"
        return text.strip()

    def extract_text_from_xml(self, file):
        """Extract text from an XML file (file is a BytesIO object)."""
        tree = ET.parse(file)
        root = tree.getroot()
        return " ".join([elem.text for elem in root.iter() if elem.text]).strip()

    def extract_text_from_json(self, file):
        """Extract text from a JSON file (file is a BytesIO object)."""
        data = json.load(file)
        return json.dumps(data)

    def extract_text_from_csv(self, file):
        """Extract text from a CSV file (file is a BytesIO object)."""
        file.seek(0)  
        df = pd.read_csv(file)
        return df.to_string(index=False)  

    def extract_text(self, uploaded_file, file_type):
        """Extract text based on file type without saving."""
        if file_type == "pdf":
            return self.extract_text_from_pdf(uploaded_file)
        elif file_type == "xml":
            return self.extract_text_from_xml(uploaded_file)
        elif file_type == "json":
            return self.extract_text_from_json(uploaded_file)
        elif file_type == "csv":
            return self.extract_text_from_csv(uploaded_file)
        else:
            raise ValueError("Unsupported file format")

    def get_upload_type(self, data):
        """Determines whether document is an invoice or PO"""
        if data.invoice_number:
            return "invoice"
        else:
            return "purchase_order"

    def validate_invoice(self, data, upload_type):
        """Validate if extracted invoice data contains a PO number and if it exists in the database."""
        # Check if PO number is present
        if not data.po_number:
            return {"valid": False, "message": "Missing purchase order number (PO number). Document not saved."}
        
        if upload_type != "invoice":
            return {"valid": True, "message": "Valid"}
        else:
            # Check if PO number exists in the database
            conn = sqlite3.connect("db/purchase_orders.db")
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM purchase_orders WHERE po_number = ?", (data.po_number,))
            po_exists = cursor.fetchone()[0] > 0  # True if PO number is found, False otherwise

            conn.close()

            if not po_exists:
                return {"valid": False, "message": f"PO number {data.po_number} has no match in the database. Document not saved."}
            return {"valid": True, "message": "Valid"}

    def extract_invoice_details(self, uploaded_file, file_type):
        """Extract structured invoice details using LangChain's LLM framework."""
        text = self.extract_text(uploaded_file, file_type)
        prompt = Prompts.extract_invoice_details(text=text)
        schema = Invoice
        chain = self.llm.with_structured_output(schema=schema)
        extracted_data = chain.invoke(prompt)
        upload_type = self.get_upload_type(extracted_data)
        validation_result = self.validate_invoice(extracted_data, upload_type)
        
        return {"invoice_data": extracted_data, "validation": validation_result, "upload_type": upload_type}