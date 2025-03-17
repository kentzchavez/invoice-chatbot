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
    def get_RAG_response_prompt(query: str, data: str, chat_history: str):
        """Prompt template for getting a response."""
        return f"""
        Given the provided query and data, respond in a relevant and straightforward manner. Follow these guidelines:

        Focus on relevance: Address the query directly using the data provided. If the requested information (e.g., an invoice) is unavailable, simply state that it is unavailable without mentioning missing data or limitations.
        Formatting: Format your response clearly and professionally.
        Tabularize: Present the 'items' field in a well-structured table, if the query asked to show the items.
        Omit missing data: Do not include any fields or information that are not available in the data, inform the user separately after showing the available data about the missing ones.
        Use Chat History: If context is not clear, check the chat history provided.

        Query: {query}
        Data: {data}

        Chat History: {chat_history}
        """

    @staticmethod
    def classify_query_prompt(query: str, chat_history: str):
        """Prompt template for classifying user query"""
        return f"""
        Task:
        Given the user query and chat history, classify the user query into one of the predefined categories based on the intent and context. Use the chat history to determine the appropriate classification.

        Classifications:
        Invoice Inquiry (II): Use this classification if the user is asking for details about a specific invoice and the required data is already available in the chat history.
        Example: "Can you tell me the total amount for invoice #123?" (assuming the data is in the chat history).

        RAG Invoice Inquiry (RAG-II): Use this classification if the user is asking for details about a specific invoice but the required data is not in the chat history and needs to be retrieved from an external database or system.
        Example: "What is the due date for invoice #456?" (assuming the data is not in the chat history).

        Email Drafting (ED): Use this classification if the user is requesting assistance in drafting an email related to invoices.
        Example: "Can you help me write an email to follow up on invoice #789?"

        Guidelines:
        - Carefully analyze the user query and chat history to determine the intent and context.
        - Focus on whether the required data is already in the chat history or needs to be retrieved externally.
        - Only return the classification code (e.g., II, RAG-II, ED) as the output. Do not include any additional text, explanations, or notes.

        Input:

        Query: {query}

        Chat History: {chat_history}
        """
    
    @staticmethod
    def get_invoice_response_prompt(query: str, chat_history: str):
        """Prompt template for getting invoice details."""
        return f"""
        Answer the user's query properly based on the given details in the chat history.

        Focus on relevance: Address the query directly using the data provided. If the requested information (e.g., an invoice) is unavailable, simply state that it is unavailable without mentioning missing data or limitations.
        Formatting: Format your response clearly and professionally.
        Tabularize: Present the 'items' field in a well-structured table, if the query asked to show the items.
        Omit missing data: Do not include any fields or information that are not available in the data, inform the user separately after showing the available data about the missing ones.
        Use Chat History: If context is not clear, check the chat history provided.

        Query: {query}

        chat history: {chat_history}
        """
    
    def draft_email_prompt(query: str, chat_history: str):
        """Prompt template for drafting an email."""
        return f"""
        Draft a professional, polite, and concise email addressing the user query. Use the chat history for context.

        Purpose:
        Resolve invoice discrepancies (e.g., missing values).
        Follow up with customers on invoices or payments.
        Provide clarification or additional details.

        Guidelines:
        Tone: Friendly, professional, and polite.
        Structure:
        - Subject line: Clear and concise.
        - Body: Acknowledge query, provide info/next steps, offer assistance.
        - Closing: Polite sign-off (e.g., "Best regards").
        - Length: Short and to the point.

        Query: {query}

        Chat History: {chat_history}"""
    

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

