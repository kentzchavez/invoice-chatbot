import streamlit as st
import pandas as pd
from src.invoice_Validator import InvoiceExtractor
from src.st_Fields import AppFields
from src.invoice_dbManager import InvoiceDB 
import io
class InvoiceApp:
    def __init__(self):
        self.extractor = InvoiceExtractor()
        self.st_fields = AppFields()
        self.setup_page()
        if "invoices" not in st.session_state:
            st.session_state["invoices"] = [] 
        self.db = InvoiceDB()

    def setup_page(self):
        """Setup Streamlit page configurations and load styles."""
        st.set_page_config(layout="wide", page_title="Invoice Extractor")
        self.load_css()
        st.title("📄 Invoice Details Extractor")

    def load_css(self):
        """Load external CSS file for styling."""
        try:
            with open("static/style.css", "r") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.error("CSS file not found! Ensure 'style.css' exists.")

    def left_section(self):
        """Handles invoice upload and extraction."""
        with st.container(key="main-left-col"):
            st.subheader("📤 Upload an Invoice")
            uploaded_file = st.file_uploader("File Uploader", type=["pdf", "xml", "json", "csv"])

            if uploaded_file:
                file_type = uploaded_file.name.split(".")[-1].lower()

                with st.spinner("Extracting invoice details..."):
                    result = self.extractor.extract_invoice_details(uploaded_file, file_type)

                invoice_data = result.model_dump()
                present_values = {key: value for key, value in invoice_data.items() if value is not None}
                missing_values = {key: "Missing" for key, value in invoice_data.items() if value is None}

                with st.container(key="invoice-info"):
                    st.subheader("📌 Extracted Invoice Details")
                    self.st_fields.divider()
                    self.st_fields.show_fields(present_values, missing_values)

                    try:
                        self.db.save_invoice(present_values)
                        st.success("Invoice saved successfully!")
                    except ValueError as e:
                        st.error(str(e))  # Display duplicate invoice error

    def right_section(self):
        """Displays the table with extracted invoice details from SQLite database."""
        with st.container(key="main-right-col"):  # No extra <div> needed
            col1, spacer, col2 = st.columns([3, 1, 0.5])
            
            with col1:
                st.subheader("Your Invoices")

            invoices = self.db.get_all_invoices()  # Fetch invoices from SQLite

            if invoices:
                formatted_invoices = []
                for invoice in invoices:
                    formatted_invoice = {}
                    for key, value in invoice.items():
                        if isinstance(value, list):  
                            formatted_invoice[key] = ", ".join(map(str, value))  # Convert list to string
                        elif isinstance(value, dict):  
                            formatted_invoice[key] = ", ".join(f"{k}: {v}" for k, v in value.items())  # Convert dict to string
                        else:
                            formatted_invoice[key] = value
                    formatted_invoices.append(formatted_invoice)

                df = pd.DataFrame(formatted_invoices)

                # Display table with full width
                st.dataframe(df, use_container_width=True)

                # Save button: Generate CSV in memory and download it immediately
                with col2:
                    csv_buffer = io.StringIO()
                    df.to_csv(csv_buffer, index=False)
                    csv_data = csv_buffer.getvalue()

                    st.download_button(
                        label="Save as CSV",
                        data=csv_data,
                        file_name="invoices.csv",
                        mime="text/csv"
                    )
            else:
                st.info("No invoices uploaded yet. Upload an invoice to see the extracted data.")

    def run(self):
        """Run the Streamlit app with a 2-column layout."""
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        col1, spacer, col2 = st.columns([1, 0.05, 2])  # Left (1/4), Right (3/4)

        with col1:
            self.left_section()

        with col2:
            self.right_section()

# Run the application
if __name__ == "__main__":
    app = InvoiceApp()
    app.run()