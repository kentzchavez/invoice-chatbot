import pandas as pd
import pdfkit
import streamlit as st

class InvoiceSaver:
    @staticmethod
    def save_as_csv(data, filename="saved_invoices.csv"):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return filename
