import streamlit as st
import pandas as pd
from src.invoice_Validator import InvoiceExtractor
from src.st_Fields import AppFields
from src.dbManager.invoice_dbManager import InvoiceDB 
from src.dbManager.po_dbManager import PurchaseOrderDB
from src.templates import DataPreparer
import io
from src.vectorStore.invoice_VectorStore import InvoiceVectorStore
from src.chatbot_Helper import InvoiceChatbot
class InvoiceApp:
    def __init__(self):
        self.extractor = InvoiceExtractor()
        self.st_fields = AppFields()
        self.vector_handler = InvoiceVectorStore()
        self.setup_page()
        self.invoice_db = InvoiceDB(vector_store=self.vector_handler)
        self.po_db = PurchaseOrderDB()
        self.dataprep = DataPreparer()
        self.chatbot = InvoiceChatbot(vector_store=self.vector_handler)
        self.vector_handler.initialize_vector_store()

    def setup_page(self):
        """Setup Streamlit page configurations and load styles."""
        st.set_page_config(layout="wide", page_title="Invoice Extractor")
        self.load_css()
        st.title("Invoice Details Extractor")

    def load_css(self):
        """Load external CSS file for styling."""
        try:
            with open("static/style.css", "r") as f:
                css = f.read()
            st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
        except FileNotFoundError:
            st.error("CSS file not found! Ensure 'style.css' exists.")

    def load_invoice_table(self, invoices):
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

        return df

    def left_section(self):
        """Handles invoice or purchase order upload and extraction."""
        with st.container(key="main-left-col"):
            st.subheader("Upload an Invoice/Purchase Order")

            # Initialize session state variables
            session_defaults = {
                "upload_type": None,
                "uploaded_file": None,
                "extracted_data": None, # Flag to prevent re-extraction
            }

            for key, value in session_defaults.items():
                if key not in st.session_state:
                    st.session_state[key] = value

            # File uploader
            uploaded_file = st.file_uploader(
                "File Uploader",
                type=["pdf", "xml", "json", "csv"],
                key="file_uploader",  # Important: Assign a key for session management
            )

            if uploaded_file:
                # Get the file type
                file_type = uploaded_file.name.split(".")[-1].lower()

                with st.spinner(f"Extracting details..."):
                    result = self.extractor.extract_invoice_details(uploaded_file, file_type)

                st.session_state["extracted_data"] = result["invoice_data"].model_dump()
                st.session_state["validation"] = result["validation"]
                st.session_state["upload_type"] = result["upload_type"]

            # Display extracted data if available
            if st.session_state["extracted_data"]:
                extracted_data = st.session_state["extracted_data"]

                present_values = {key: value for key, value in extracted_data.items() if value is not None}
                missing_values = {key: "Missing" for key, value in extracted_data.items() if value is None}

                with st.container(key="invoice-info"):
                    # Save extracted data to the database only if it's valid
                    if st.session_state["validation"]["valid"]:
                        try:
                            structured_data = self.dataprep.prepare_structured_data(extracted_data, st.session_state["upload_type"])

                            if st.session_state["upload_type"] == "invoice":
                                save_msg = self.invoice_db.save_invoice(structured_data)
                                if save_msg['success']:
                                    st.success(save_msg['message'])
                                else:
                                    st.error(save_msg['message'])
                            else:
                                save_msg = self.po_db.save_purchase_order(structured_data)
                                st.success(save_msg)

                        except ValueError as e:
                            st.error(str(e))  # Display duplicate entry error
                    else:
                        st.error(st.session_state["validation"]["message"])

                    st.subheader(f"Extracted Details")
                    self.st_fields.divider()
                    self.st_fields.show_fields(present_values, missing_values)

    def right_section(self):
        """Displays the table with extracted invoice details from SQLite database."""
        df = pd.DataFrame()
        with st.container(key="main-right-col"):  # No extra <div> needed
            col1, spacer, col2 = st.columns([3, 1, 0.5])
            with col1:
                st.subheader("Your Invoices")

            invoices = self.invoice_db.get_all_invoices()  # Fetch invoices from SQLite
            if invoices:
                df = self.load_invoice_table(invoices)

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
    
        # Chatbot
        self.chatbot.chatbot_ui()

    def run(self):
        """Run the Streamlit app with a 2-column layout."""
        st.markdown('<div class="upload-box">', unsafe_allow_html=True)
        col1, spacer, col2 = st.columns([0.80, 0.05, 2.20])

        with col1:
            self.left_section()

        with col2:
            self.right_section()
