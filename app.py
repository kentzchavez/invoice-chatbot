import streamlit as st
import pandas as pd
from src.invoiceValidator import InvoiceExtractor

# Initialize the invoice extractor
extractor = InvoiceExtractor()

# Streamlit page setup
st.set_page_config(layout="wide", page_title="Invoice Extractor")

# Custom CSS for styling
st.markdown(
    """
    <style>
        .styled-box {
            background-color: #f7f7f7;  
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }
        .upload-box {
            background-color: #eaf2ff;  
            padding: 20px;
            border-radius: 10px;
            box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.1);
        }
        .divider {
            border-top: 2px solid #ccc;
            margin-top: 10px;
            margin-bottom: 10px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Layout
st.title("📄 Invoice Extractor")

# File Upload Section
st.markdown('<div class="upload-box">', unsafe_allow_html=True)
st.header("📤 Upload Your Invoice")
uploaded_file = st.file_uploader("Upload an invoice (PDF, XML, JSON)", type=["pdf", "xml", "json"])
st.markdown('</div>', unsafe_allow_html=True)

if uploaded_file:
    # Save the uploaded file temporarily
    file_path = f"temp_{uploaded_file.name}"
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # Extract invoice details
    with st.spinner("Extracting invoice details..."):
        result = extractor.extract_invoice_details(file_path)

    # Convert Pydantic model to dictionary
    invoice_data = result.model_dump()

    # Separate missing values
    missing_values = {key: "Missing" for key, value in invoice_data.items() if value is None}
    present_values = {key: value for key, value in invoice_data.items() if value is not None}

    # Display extracted details (excluding items)
    st.subheader("📌 Extracted Invoice Details")
    for key, value in present_values.items():
        if key != "items":  # Exclude items (we'll display them separately)
            st.write(f"**{key.replace('_', ' ').title()}**: {value}")

    # Divider
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Display items in a table if available
    if "items" in present_values and isinstance(present_values["items"], list):
        st.subheader("📦 Items")
        if present_values["items"]:
            items_df = pd.DataFrame(present_values["items"])

            # Remove "Missing" column if all its values are NaN
            items_df = items_df.dropna(axis=1, how="all")

            st.table(items_df)
        else:
            st.write("No item details found.")


    # Missing values in a collapsible dropdown
    if missing_values:
        with st.expander("🚨 Show Missing Fields"):
            for key in missing_values:
                st.write(f"**{key.replace('_', ' ').title()}**: NaN")
