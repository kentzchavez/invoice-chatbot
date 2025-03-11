import sqlite3
import json
import hashlib
from typing import List, Dict
from src.vectorStore.invoice_VectorStore import InvoiceVectorStore

class InvoiceDB:
    def __init__(self, db_name="db/invoices.db", vector_store: InvoiceVectorStore = None):
        self.db_name = db_name
        self.create_table()
        self.vector_store = vector_store

    def connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_table(self):
        """Create the invoice table with key details stored in separate columns."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT UNIQUE NOT NULL,
                    invoice_number TEXT,
                    customer_name TEXT,
                    customer_contact_number TEXT,
                    customer_contact_email TEXT,
                    customer_address TEXT,
                    date TEXT,
                    total_amount TEXT,
                    supplier TEXT,
                    currency TEXT,
                    due_date TEXT,
                    items TEXT NOT NULL, -- Store items as JSON
                    hash TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

    def generate_invoice_hash(self, invoice_data: Dict) -> str:
        """Generate a unique hash for an invoice using its key details."""
        invoice_str = json.dumps(invoice_data, sort_keys=True)  # Convert to JSON string
        return hashlib.sha256(invoice_str.encode()).hexdigest()

    def is_duplicate(self, po_number: str, invoice_hash: str) -> bool:
        """Check if an invoice is already stored (duplicate PO number or hash)."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM invoices WHERE po_number = ? OR hash = ?", (po_number, invoice_hash))
            return cursor.fetchone() is not None

    def save_invoice(self, invoice_data: Dict):
        """Save an invoice and automatically store it in the vector store."""
        po_number = invoice_data.get("po_number", "").strip().upper()
        invoice_hash = self.generate_invoice_hash(invoice_data)

        if self.is_duplicate(po_number, invoice_hash):
            return {"success": False, "message": f"Duplicate detected: Invoice with PO Number {po_number} already exists."}

        # Extract key invoice details
        invoice_number = invoice_data.get("invoice_number", "").strip()
        customer_name = invoice_data.get("customer_name", "").strip()
        customer_contact_number = invoice_data.get("customer_contact_number", "").strip()
        customer_contact_email = invoice_data.get("customer_contact_email", "").strip()
        customer_address = invoice_data.get("customer_address", "").strip()
        date = invoice_data.get("date", "").strip()
        total_amount = invoice_data.get("total_amount", "").strip()
        supplier = invoice_data.get("supplier", "").strip()
        currency = invoice_data.get("currency", "").strip()
        due_date = invoice_data.get("due_date", "").strip()
        
        items_json = json.dumps(invoice_data.get("items", []))  # Convert list to JSON string

        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO invoices (
                        po_number, invoice_number, customer_name, customer_contact_number, 
                        customer_contact_email, customer_address, date, total_amount, 
                        supplier, currency, due_date, items, hash
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (po_number, invoice_number, customer_name, customer_contact_number,
                    customer_contact_email, customer_address, date, total_amount, 
                    supplier, currency, due_date, items_json, invoice_hash))
                
                conn.commit()

                # **After saving, add to vector store**
                if self.vector_store:
                    self.vector_store.add_invoice_to_vector_store(invoice_data)
                    print(f"Invoice {po_number} added to vector store.")

                return {"success": True, "message": f"Invoice with PO Number {po_number} successfully saved and embedded."}
            except sqlite3.IntegrityError:
                return {"success": False, "message": f"Duplicate detected: Invoice with PO Number {po_number} already exists."}

    def get_all_invoices(self) -> List[Dict]:
        """Retrieve all invoices with structured data."""
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

