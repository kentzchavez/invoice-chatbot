import sqlite3
import json
import hashlib
from typing import List, Dict

class PurchaseOrderDB:
    def __init__(self, db_name="db/purchase_orders.db"):
        self.db_name = db_name
        self.create_table()

    def connect(self):
        return sqlite3.connect(self.db_name, check_same_thread=False)

    def create_table(self):
        """Create the purchase order table with key details stored in separate columns."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    po_number TEXT UNIQUE NOT NULL,
                    supplier TEXT,
                    customer_name TEXT,
                    customer_contact_number TEXT,
                    customer_contact_email TEXT,
                    customer_address TEXT,
                    order_date TEXT,
                    total_amount TEXT,
                    currency TEXT,
                    items TEXT NOT NULL, -- Store items as JSON
                    hash TEXT UNIQUE NOT NULL
                )
            """)
            conn.commit()

    def generate_po_hash(self, po_data: Dict) -> str:
        """Generate a unique hash for a purchase order using its key details."""
        po_str = json.dumps(po_data, sort_keys=True)  # Convert to JSON string
        return hashlib.sha256(po_str.encode()).hexdigest()

    def is_duplicate(self, po_data: Dict) -> bool:
        """Check if a purchase order is already stored (duplicate PO number or hash)."""
        po_number = po_data.get("po_number", "").strip().upper()
        po_hash = self.generate_po_hash(po_data)

        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM purchase_orders WHERE po_number = ? OR hash = ?", (po_number, po_hash))
            return cursor.fetchone() is not None


    def save_purchase_order(self, po_data: Dict):
        """Save a purchase order, ensuring no duplicate PO numbers."""
        po_hash = self.generate_po_hash(po_data)
        po_number = po_data.get("po_number", "").strip().upper()

        if self.is_duplicate(po_data):
            raise ValueError(f"Duplicate PO detected: PO Number {po_number} already exists.")

        # Extract key PO details
        supplier = po_data.get("supplier", "").strip()
        customer_name = po_data.get("customer_name", "").strip()
        customer_contact_number = po_data.get("customer_contact_number", "").strip()
        customer_contact_email = po_data.get("customer_contact_email", "").strip()
        customer_address = po_data.get("customer_address", "").strip()
        order_date = po_data.get("order_date", "").strip()
        total_amount = po_data.get("total_amount", "").strip()
        currency = po_data.get("currency", "").strip()
        items_json = json.dumps(po_data.get("items", []))

        with self.connect() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                    INSERT INTO purchase_orders (
                        po_number, supplier, customer_name, customer_contact_number, 
                        customer_contact_email, customer_address, order_date, 
                        total_amount, currency, items, hash
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (po_number, supplier, customer_name, customer_contact_number,
                    customer_contact_email, customer_address, order_date, 
                    total_amount, currency, items_json, po_hash))

                conn.commit()
                return 'PO Number {} successfully saved.'.format(po_number)
            except sqlite3.IntegrityError:
                raise ValueError(f"PO Number {po_number} already exists in the database.")


