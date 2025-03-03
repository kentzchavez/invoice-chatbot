import streamlit as st
import pandas as pd

class AppFields:
    """Determines different fields of showing invoice details for modularity"""

    def __init__(self):
        self.invoice_keys = ["invoice_number", "date", "invoice_due_date", "supplier"]
        self.customer_keys = ["customer_name", "customer_contact", "customer_address"]
        self.transaction_keys = ["total_amount", "payment_method", "currency", "due_date"]

    def divider(self):
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    def show_invoice_info(self, present_values):
        """Show the invoice information."""
        if any(key in present_values for key in self.invoice_keys):
            st.markdown("### 📄 Invoice Information")
            for key in self.invoice_keys:
                if key in present_values:
                    st.write(f"**{key.replace('_', ' ').title()}**: {present_values[key]}")
            self.divider()
    
    def show_customer_info(self, present_values):
        """Show the customer info"""
        if any(key in present_values for key in self.customer_keys):
            st.markdown("### 👤 Customer Information")
            for key in self.customer_keys:
                if key in present_values:
                    st.write(f"**{key.replace('_', ' ').title()}**: {present_values[key]}")
            self.divider()

    def show_transaction_info(self, present_values):
        """Show the transaction info"""
        if any(key in present_values for key in self.transaction_keys):
            st.markdown("### 💳 Payment & Transaction Details")
            for key in self.transaction_keys:
                if key in present_values:
                    st.write(f"**{key.replace('_', ' ').title()}**: {present_values[key]}")
            self.divider()

    def show_items(self, present_values):
        """Shows the items in the invoice"""   
        if "items" in present_values and isinstance(present_values["items"], list):
            st.subheader("📦 Items")
        if present_values["items"]:
            items_df = pd.DataFrame(present_values["items"])

            # Remove empty columns
            items_df = items_df.dropna(axis=1, how="all")

            st.table(items_df)
        else:
            st.write("No item details found.")

    def show_missing_fields(self, missing_values):
        """Show the missing fields"""
        if missing_values:
            with st.expander("🚨 Show Missing Details"):
                for key in missing_values:
                    st.write(f"**{key.replace('_', ' ').title()}**: NaN")

    def show_fields(self, present_values, missing_values):
        """Show all the fields"""
        self.show_invoice_info(present_values)
        self.show_customer_info(present_values)
        self.show_transaction_info(present_values)
        self.show_items(present_values)
        self.show_missing_fields(missing_values)