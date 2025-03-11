import sqlite3
import json
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from dotenv import load_dotenv

load_dotenv()

class InvoiceVectorStore:
    def __init__(self, db_path="db/invoices.db", vector_db_path="db/vstore"):
        self.db_path = db_path
        self.vector_db_path = vector_db_path
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.vector_store = Chroma(persist_directory=self.vector_db_path, embedding_function=self.embeddings)

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def get_all_invoices(self):
        """Retrieve all invoices from the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT po_number, invoice_number, customer_name, customer_contact_number, 
                    customer_contact_email, customer_address, date, total_amount, 
                    supplier, currency, due_date, items 
                FROM invoices
            """)
            rows = cursor.fetchall()

        invoices = []
        for row in rows:
            try:
                invoice_data = {
                    "po_number": row[0],
                    "invoice_number": row[1],
                    "customer_name": row[2],
                    "customer_contact_number": row[3],
                    "customer_contact_email": row[4],
                    "customer_address": row[5],
                    "date": row[6],
                    "total_amount": row[7],
                    "supplier": row[8],
                    "currency": row[9],
                    "due_date": row[10],
                    "items": json.loads(row[11])  # Convert JSON string back to list
                }
                invoices.append(invoice_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

        return invoices

    def format_invoice_text(self, invoice):
        """Formats invoice data into a structured text format for embedding."""
        items_text = "\n".join([
            f"- {item['name']} (Qty: {item['quantity']}, Price: {item['price']}, Subtotal: {item['subtotal']})"
            for item in invoice.get('items', [])
        ]) if invoice.get('items') else "No items listed"

        return f"""
        PO Number: {invoice.get('po_number', 'N/A')}
        Invoice Number: {invoice.get('invoice_number', 'N/A')}
        Customer Name: {invoice.get('customer_name', 'N/A')}
        Contact Number: {invoice.get('customer_contact_number', 'N/A')}
        Email: {invoice.get('customer_contact_email', 'N/A')}
        Address: {invoice.get('customer_address', 'N/A')}
        Invoice Date: {invoice.get('date', 'N/A')}
        Due Date: {invoice.get('due_date', 'N/A')}
        Total Amount: {invoice.get('total_amount', 'N/A')} {invoice.get('currency', 'N/A')}
        Supplier: {invoice.get('supplier', 'N/A')}
        
        Items:
        {items_text}
        """.strip()

    def get_existing_invoice_ids(self):
        """Fetch already stored invoice numbers from ChromaDB to prevent duplicates."""
        try:
            stored_data = self.vector_store.get()
            return {metadata["invoice_number"] for metadata in stored_data["metadatas"] if "invoice_number" in metadata}
        except Exception as e:
            print(f"Error fetching existing invoices from ChromaDB: {e}")
            return set()

    def create_vector_store(self):
        """Convert structured invoice data into text embeddings and store in ChromaDB without duplicates."""
        invoices = self.get_all_invoices()
        existing_invoice_ids = self.get_existing_invoice_ids()
        documents = []

        for invoice in invoices:
            if invoice["invoice_number"] in existing_invoice_ids:
                print(f"Skipping duplicate invoice: {invoice['invoice_number']}")
                continue

            text_content = self.format_invoice_text(invoice)
            documents.append(Document(
                page_content=text_content,
                metadata={"po_number": invoice["po_number"], "invoice_number": invoice["invoice_number"]}
            ))

        if documents:
            self.vector_store.add_documents(documents)
            print(f"Added {len(documents)} new invoices to ChromaDB.")
        else:
            print("No new invoices to add.")

    def add_invoice_to_vector_store(self, invoice_data):
        """Embed and store a new invoice while preventing duplicates."""
        existing_invoice_ids = self.get_existing_invoice_ids()

        if invoice_data["invoice_number"] in existing_invoice_ids:
            print(f"Invoice {invoice_data['invoice_number']} already exists in ChromaDB. Skipping.")
            return

        text_content = self.format_invoice_text(invoice_data)

        document = Document(
            page_content=text_content,
            metadata={"po_number": invoice_data["po_number"], "invoice_number": invoice_data["invoice_number"]}
        )

        self.vector_store.add_documents([document])
        print(f"Invoice {invoice_data['invoice_number']} embedded and stored in vector DB.")

    def query_similar_invoices(self, query_text, k=3):
        """Query the vector store for similar invoices."""
        results = self.vector_store.similarity_search(query_text, k=k)
        return [res.page_content for res in results]

    def initialize_vector_store(self):
        """Check if the vector store exists, if not, initialize it."""
        if os.path.exists(os.path.join(self.vector_db_path, "chroma-collections.parquet")):
            print("Vector store already initialized. Skipping re-embedding.")
        else:
            print("Initializing vector store for the first time...")
            self.create_vector_store()

if __name__ == "__main__":
    vector_handler = InvoiceVectorStore()
    vector_handler.create_vector_store()

    query = "Find invoices related to John Doe"
    results = vector_handler.query_similar_invoices(query)
    print("\nSimilar Invoices:")
    for res in results:
        print(res)
