from pydantic import BaseModel, Field
from typing import Optional

class Invoice(BaseModel):
    """Defines the structure of an invoice."""
    invoice_number: Optional[str] = Field(None, description="the invoice number")
    customer_name: Optional[str] = Field(None, description="The customer name")
    customer_contact: Optional[str] = Field(None, description="The customer contact")
    customer_address: Optional[str] = Field(None, description="The customer address")
    date: Optional[str] = Field(None, description="The date of the invoice")
    total_amount: Optional[str] = Field(None, description="The total amount on the invoice")
    items: Optional[list[str]] = Field(None, description="The items on the invoice")
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
        Extract the invoice details using the schema from the text, if a detail cannot be found, then dont put anything.
        text: {text}
        """
