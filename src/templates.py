from pydantic import BaseModel, Field
from typing import Optional
class ItemDetails(BaseModel):
    """Defines the structure for individual invoice items."""
    name: Optional[str] = Field(None, description="The name of the item")
    price: Optional[str] = Field(None, description="The price of the item")
    quantity: Optional[int] = Field(None, description="The quantity of the item")
    subtotal: Optional[str] = Field(None, description="The subtotal of the item")
class Invoice(BaseModel):
    """Defines the structure of an invoice."""
    po_number: Optional[str] = Field(None, description="the purchase order number")
    invoice_number: Optional[str] = Field(None, description="the invoice number")
    customer_name: Optional[str] = Field(None, description="The customer name")
    customer_contact_number: Optional[str] = Field(None, description="The customer contact number")
    customer_contact_email: Optional[str] = Field(None, description="The customer contact email")
    customer_address: Optional[str] = Field(None, description="The customer address")
    date: Optional[str] = Field(None, description="The date of the invoice")
    total_amount: Optional[str] = Field(None, description="The total amount on the invoice")
    items: Optional[list[ItemDetails]] = Field(None, description="List of items in the invoice with name, price, and quantity if available")
    supplier: Optional[str] = Field(None, description="The supplier of the invoice")
    currency: Optional[str] = Field(None, description="The currency of the invoice")
    due_date: Optional[str] = Field(None, description="The due date of the invoice")
class Prompts:
    """Defines the prompt templates for the LLM"""

    @staticmethod
    def extract_invoice_details(text: str):
        """Prompt template for extracting invoice details."""
        return f"""
        Extract the following invoice details from the provided text. 
        If a detail is missing, never put anything.

        - Invoice number
        - Customer details (name, contact, address)
        - Date 
        - Total amount
        - Items (if specified, extract name, price, quantity, and subtotal; ensure the price is formatted right, if currency is present, include it, if decimal is missing, add it; ensure to extract every items) 
        - Supplier
        - Payment method
        - Currency (determine based on prices in the invoice, e.g., if "$100" appears, currency is USD)
        - Due date

        Invoice text:
        {text}
        """
    
    @staticmethod
    def get_response_prompt(query: str, data: str):
        """Prompt template for getting a response."""
        return f"""
        Given the following query, provide the appropriate response according to the data provided. Answer relevantly and be straightforward.
        Ensure to format your answer properly. Do not include missing data in your response.

        Query: {query}

        Data: {data}
        """

class DataPreparer:
    """Handles the preparation of structured data for invoices and purchase orders."""

    @staticmethod
    def safe_strip(value):
        """Ensure the value is a string before calling .strip() to prevent NoneType errors."""
        return str(value).strip() if value else ""

    @classmethod
    def prepare_structured_data(self, extracted_data, upload_type):
        """Prepare structured data with safe handling for NoneType values and include all columns."""

        # Common fields for both invoices and purchase orders
        structured_data = {
            "po_number": self.safe_strip(extracted_data.get("po_number")),
            "supplier": self.safe_strip(extracted_data.get("supplier")),
            "customer_name": self.safe_strip(extracted_data.get("customer_name")),
            "customer_contact_number": self.safe_strip(extracted_data.get("customer_contact_number")),
            "customer_contact_email": self.safe_strip(extracted_data.get("customer_contact_email")),
            "customer_address": self.safe_strip(extracted_data.get("customer_address")),
            "order_date": self.safe_strip(extracted_data.get("order_date")),  # Used for Purchase Orders
            "date": self.safe_strip(extracted_data.get("date")),  # Used for Invoices
            "due_date": self.safe_strip(extracted_data.get("due_date")),  # Used for Invoices
            "total_amount": self.safe_strip(extracted_data.get("total_amount")),
            "currency": self.safe_strip(extracted_data.get("currency")),
            "items": extracted_data.get("items", []),  # Keep as a list
        }

        # Add specific fields for invoices
        if upload_type == "invoice":
            structured_data["invoice_number"] = self.safe_strip(extracted_data.get("invoice_number"))

        return structured_data

