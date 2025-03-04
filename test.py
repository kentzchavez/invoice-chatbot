import sqlite3

def check_columns():
    with sqlite3.connect("invoices.db") as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(invoices);")
        columns = cursor.fetchall()
        print(columns)  # Print column names to debug

check_columns()
