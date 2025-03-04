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
    invoice_number: Optional[str] = Field(None, description="the invoice number")
    customer_name: Optional[str] = Field(None, description="The customer name")
    customer_contact_number: Optional[str] = Field(None, description="The customer contact number")
    customer_contact_email: Optional[str] = Field(None, description="The customer contact email")
    customer_address: Optional[str] = Field(None, description="The customer address")
    date: Optional[str] = Field(None, description="The date of the invoice")
    total_amount: Optional[str] = Field(None, description="The total amount on the invoice")
    items: Optional[list[ItemDetails]] = Field(None, description="List of items in the invoice with name, price, and quantity if available")
    supplier: Optional[str] = Field(None, description="The supplier of the invoice")
    
    payment_method: Optional[str] = Field(None, description="The payment method used")
    currency: Optional[str] = Field(None, description="The currency of the invoice")
    due_date: Optional[str] = Field(None, description="The due date of the invoice")

class Prompts:
    """Defines the prompt templates for the LLM"""

    @staticmethod
    def extract_invoice_details(text: str):
        """Prompt template for extracting invoice details."""
        return f"""
        Extract the following invoice details from the provided text. If a detail is missing, return an empty field, do not make up any information.

        - Invoice number
        - Customer details (name, contact, address)
        - Date 
        - Total amount
        - Items (if specified, extract name, price, quantity, and subtotal; ensure the price is formatted right, if currency is present, include it, if decimal is missing, add it; ensure to extract everything) 
        - Supplier
        - Payment method
        - Currency (determine based on prices in the invoice, e.g., if "$100" appears, currency is USD)
        - Due date

        Invoice text:
        {text}
        """
