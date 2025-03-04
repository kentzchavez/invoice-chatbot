import sqlite3
import json
import hashlib
from typing import List, Dict

class InvoiceDB:
    def __init__(self, db_name="invoices.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_table(self):
        """Create the invoice table with a unique hash column to prevent duplicates."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    hash TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

    def generate_invoice_hash(self, invoice_data: Dict) -> str:
        """Generate a unique hash for an invoice using its key details."""
        invoice_str = json.dumps(invoice_data, sort_keys=True)  # Convert to JSON string
        return hashlib.sha256(invoice_str.encode()).hexdigest()

    def is_duplicate(self, invoice_data: Dict) -> bool:
        """Check if an invoice is already stored (duplicate)."""
        invoice_hash = self.generate_invoice_hash(invoice_data)
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM invoices WHERE hash = ?", (invoice_hash,))
            return cursor.fetchone() is not None

    def save_invoice(self, invoice_data: Dict):
        """Save an invoice to the database, ensuring it is valid JSON."""
        invoice_hash = self.generate_invoice_hash(invoice_data)

        if self.is_duplicate(invoice_data):
            raise ValueError("Duplicate invoice detected. This invoice is already stored.")

        json_data = json.dumps(invoice_data)  # Convert dictionary to JSON format

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO invoices (data, hash) VALUES (?, ?)", 
                           (json_data, invoice_hash))  # Store as JSON string
            conn.commit()

    def get_all_invoices(self) -> List[Dict]:
        """Retrieve all invoices from the database, ensuring valid JSON parsing."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM invoices")
            rows = cursor.fetchall()

        invoices = []
        for row in rows:
            try:
                invoices.append(json.loads(row[0]))  # Convert JSON string to dictionary
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")  # Debugging
                continue  # Skip invalid entries

        return invoices
