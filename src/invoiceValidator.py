import os
import json
import pdfplumber
import xml.etree.ElementTree as ET
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain.chains import create_extraction_chain
from pydantic import BaseModel, Field
from typing import Optional

from src.templates import Invoice, Prompts


# Load environment variables
load_dotenv()

class InvoiceExtractor:
    """Handles validation and information extraction of the invoices"""
    def __init__(self):
        self.llm = ChatOpenAI(model="gpt-4o")

    def extract_text_from_pdf(self, file_path):
        """Extract text from a PDF file."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n" if page.extract_text() else ""
        return text.strip()

    def extract_text_from_xml(self, file_path):
        """Extract text from an XML file."""
        tree = ET.parse(file_path)
        root = tree.getroot()
        return " ".join([elem.text for elem in root.iter() if elem.text]).strip()

    def extract_text_from_json(self, file_path):
        """Extract text from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return json.dumps(data)

    def extract_text(self, file_path):
        """Extract text based on file type."""
        ext = file_path.split(".")[-1].lower()
        if ext == "pdf":
            return self.extract_text_from_pdf(file_path)
        elif ext == "xml":
            return self.extract_text_from_xml(file_path)
        elif ext == "json":
            return self.extract_text_from_json(file_path)
        else:
            raise ValueError("Unsupported file format")

    def extract_invoice_details(self, file_path):
        """Extract structured invoice details using LangChain's LLM framework."""
        text = self.extract_text(file_path)
        prompt = Prompts.extract_invoice_details(text=text)
        schema = Invoice
        chain = self.llm.with_structured_output(schema=schema)
        extracted_data = chain.invoke(prompt)
        return extracted_data

