import pandas as pd
import pdfkit
import streamlit as st

class InvoiceSaver:
    @staticmethod
    def save_as_csv(data, filename="invoices.csv"):
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return filename

    @staticmethod
    def save_as_pdf(data, filename="invoices.pdf"):
        df = pd.DataFrame(data)
        html = df.to_html(index=False)
        
        options = {
            "enable-local-file-access": None
        }
        pdfkit.from_string(html, filename, options=options)
        return filename
