import streamlit as st
import pandas as pd
from src.invoiceValidator import InvoiceExtractor
from src.st_Fields import AppFields

class InvoiceApp:
    def __init__(self):
        self.extractor = InvoiceExtractor()
        self.st_fields = AppFields()
        self.setup_page()

    def setup_page(self):
        """Setup Streamlit page configurations and load styles."""
        st.set_page_config(layout="wide", page_title="Invoice Details Extractor")
        self.load_css()
        st.title("📄 Invoice Extractor")

    def load_css(self):
        """Load external CSS file for styling."""
        try:
            with open("static/style.css", "r") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.error("CSS file not found! Ensure 'static/style.css' exists.")

    def upload_section(self):
        """Create the file upload section."""
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        st.header("📤 Upload Your Invoice")
        uploaded_file = st.file_uploader("Upload an invoice (PDF, XML, JSON, CSV)", type=["pdf", "xml", "json", "csv"])
        st.markdown('</div>', unsafe_allow_html=True)
        return uploaded_file

    def process_invoice(self, uploaded_file):
        """Process the uploaded invoice file without saving it to disk."""
        if uploaded_file:
            file_type = uploaded_file.type.split("/")[-1]  # Get file extension (e.g., pdf, xml, json)

            with st.spinner("Extracting invoice details..."):
                try:
                    result = self.extractor.extract_invoice_details(uploaded_file, file_type)
                    
                    # Convert Pydantic model to dictionary
                    invoice_data = result.model_dump()

                    # Separate missing and present values
                    missing_values = {key: "Missing" for key, value in invoice_data.items() if value is None}
                    present_values = {key: value for key, value in invoice_data.items() if value is not None}

                    self.st_fields.divider()
                    st.subheader("📌 Extracted Invoice Details")
                    self.st_fields.divider()
                    self.st_fields.show_fields(present_values, missing_values)

                except ValueError as e:
                    st.error(f"Error processing file: {e}")

    def run(self):
        """Run the Streamlit app."""
        uploaded_file = self.upload_section()
        self.process_invoice(uploaded_file)

# Run the application
if __name__ == "__main__":
    app = InvoiceApp()
    app.run()
