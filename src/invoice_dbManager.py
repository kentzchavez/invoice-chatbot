import sqlite3
from typing import List, Dict

class InvoiceDB:
    def __init__(self, db_name="invoices.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_table(self):
        """Create the invoice table if it doesn't exist."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS invoices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL
                )
            """)
            conn.commit()

    def save_invoice(self, invoice_data: Dict):
        """Save an extracted invoice to the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO invoices (data) VALUES (?)", 
                           (str(invoice_data),))  # Store as string
            conn.commit()

    def get_all_invoices(self) -> List[Dict]:
        """Retrieve all invoices from the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT data FROM invoices")
            rows = cursor.fetchall()
            return [eval(row[0]) for row in rows]  # Convert string back to dict
