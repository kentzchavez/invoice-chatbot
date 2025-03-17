import sqlite3
import json
import os
import faiss
import numpy as np
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.schema import Document
from dotenv import load_dotenv
from sklearn.feature_extraction.text import TfidfVectorizer  # For re-ranking
from sklearn.metrics.pairwise import cosine_similarity  # For re-ranking

load_dotenv()

class InvoiceVectorStore:
    def __init__(self, db_path="db/invoices.db", vector_db_path="db/vstore"):
        self.db_path = db_path
        self.vector_db_path = vector_db_path
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004")
        self.index = None
        self.metadata = []
        self.load_or_initialize_faiss_index()

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def get_all_invoices(self):
        """Retrieve all invoices from the database."""
        with self.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT po_number, invoice_number, customer_name, customer_contact_number, 
                    customer_contact_email, customer_address, date, total_amount, 
                    supplier, currency, due_date, items 
                FROM invoices
            """)
            rows = cursor.fetchall()

        invoices = []
        for row in rows:
            try:
                invoice_data = {
                    "po_number": row[0],
                    "invoice_number": row[1],
                    "customer_name": row[2],
                    "customer_contact_number": row[3],
                    "customer_contact_email": row[4],
                    "customer_address": row[5],
                    "date": row[6],
                    "total_amount": row[7],
                    "supplier": row[8],
                    "currency": row[9],
                    "due_date": row[10],
                    "items": json.loads(row[11])  # Convert JSON string back to list
                }
                invoices.append(invoice_data)
            except json.JSONDecodeError as e:
                print(f"Error decoding JSON: {e}")
                continue

        return invoices

    def format_invoice_text(self, invoice):
        """Formats invoice data into a structured text format for embedding."""
        items_text = "\n".join([
            f"- {item['name']} (Qty: {item['quantity']}, Price: {item['price']}, Subtotal: {item['subtotal']})"
            for item in invoice.get('items', [])
        ]) if invoice.get('items') else "No items listed"

        return f"""
        PO Number: {invoice.get('po_number', 'N/A')}
        Invoice Number: {invoice.get('invoice_number', 'N/A')}
        Customer Name: {invoice.get('customer_name', 'N/A')}
        Contact Number: {invoice.get('customer_contact_number', 'N/A')}
        Email: {invoice.get('customer_contact_email', 'N/A')}
        Address: {invoice.get('customer_address', 'N/A')}
        Invoice Date: {invoice.get('date', 'N/A')}
        Due Date: {invoice.get('due_date', 'N/A')}
        Total Amount: {invoice.get('total_amount', 'N/A')} {invoice.get('currency', 'N/A')}
        Supplier: {invoice.get('supplier', 'N/A')}
        
        Items:
        {items_text}
        """.strip()

    def get_existing_invoice_ids(self):
        """Fetch already stored invoice numbers from FAISS to prevent duplicates."""
        return {metadata["invoice_number"] for metadata in self.metadata if "invoice_number" in metadata}

    def load_or_initialize_faiss_index(self):
        """Load or initialize the FAISS index."""
        index_file = os.path.join(self.vector_db_path, "faiss_index.index")
        metadata_file = os.path.join(self.vector_db_path, "metadata.json")

        if os.path.exists(index_file) and os.path.exists(metadata_file):
            self.index = faiss.read_index(index_file)
            with open(metadata_file, "r") as f:
                self.metadata = json.load(f)
            print("Loaded existing FAISS index and metadata.")
        else:
            self.index = None
            self.metadata = []
            print("Initializing new FAISS index.")

    def save_faiss_index(self):
        """Save the FAISS index and metadata to disk."""
        os.makedirs(self.vector_db_path, exist_ok=True)
        index_file = os.path.join(self.vector_db_path, "faiss_index.index")
        metadata_file = os.path.join(self.vector_db_path, "metadata.json")

        if self.index:
            faiss.write_index(self.index, index_file)
        with open(metadata_file, "w") as f:
            json.dump(self.metadata, f)
        print("Saved FAISS index and metadata.")

    def normalize_embeddings(self, embeddings):
        """Normalize embeddings to unit length for cosine similarity."""
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        return embeddings / norms

    def create_vector_store(self):
        """Convert structured invoice data into text embeddings and store in FAISS without duplicates."""
        invoices = self.get_all_invoices()
        existing_invoice_ids = self.get_existing_invoice_ids()
        documents = []

        for invoice in invoices:
            if invoice["invoice_number"] in existing_invoice_ids:
                print(f"Skipping duplicate invoice: {invoice['invoice_number']}")
                continue

            text_content = self.format_invoice_text(invoice)
            documents.append(Document(
                page_content=text_content,
                metadata=invoice  # Store the full invoice data in metadata
            ))

        if documents:
            texts = [doc.page_content for doc in documents]
            embeddings = self.embeddings.embed_documents(texts)
            embeddings = np.array(embeddings).astype('float32')
            embeddings = self.normalize_embeddings(embeddings)  # Normalize embeddings

            if self.index is None:
                self.index = faiss.IndexFlatIP(embeddings.shape[1])  # Use Inner Product (cosine similarity)
                self.index.add(embeddings)
            else:
                self.index.add(embeddings)

            self.metadata.extend([doc.metadata for doc in documents])
            self.save_faiss_index()
            print(f"Added {len(documents)} new invoices to FAISS.")
        else:
            print("No new invoices to add.")

    def add_invoice_to_vector_store(self, invoice_data):
        """Embed and store a new invoice while preventing duplicates."""
        existing_invoice_ids = self.get_existing_invoice_ids()

        if invoice_data["invoice_number"] in existing_invoice_ids:
            print(f"Invoice {invoice_data['invoice_number']} already exists in FAISS. Skipping.")
            return

        text_content = self.format_invoice_text(invoice_data)
        embedding = self.embeddings.embed_documents([text_content])
        embedding = np.array(embedding).astype('float32')
        embedding = self.normalize_embeddings(embedding)  # Normalize embedding

        if self.index is None:
            self.index = faiss.IndexFlatIP(embedding.shape[1])  # Use Inner Product (cosine similarity)
        self.index.add(embedding)

        self.metadata.append({"po_number": invoice_data["po_number"], "invoice_number": invoice_data["invoice_number"]})
        self.save_faiss_index()
        print(f"Invoice {invoice_data['invoice_number']} embedded and stored in FAISS.")

    def query_similar_invoices(self, query_text, k=5):
        """Query the FAISS index for similar invoices and re-rank using TF-IDF and cosine similarity."""
        # Step 1: Retrieve top-k results using FAISS
        query_embedding = self.embeddings.embed_documents([query_text])
        query_embedding = np.array(query_embedding).astype('float32')
        query_embedding = self.normalize_embeddings(query_embedding)  # Normalize query embedding

        distances, indices = self.index.search(query_embedding, k)
        initial_results = []

        for idx in indices[0]:
            if idx < len(self.metadata):
                invoice_data = self.metadata[idx]
                initial_results.append((self.format_invoice_text(invoice_data), invoice_data))

        # Step 2: Re-rank using TF-IDF and cosine similarity
        if initial_results:
            # Extract text content from initial results
            texts = [result[0] for result in initial_results]
            # Compute TF-IDF vectors
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([query_text] + texts)
            # Compute cosine similarity between query and results
            cosine_similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()
            # Combine results with their similarity scores
            scored_results = list(zip(initial_results, cosine_similarities))
            # Sort by similarity score (higher is better)
            scored_results.sort(key=lambda x: x[1], reverse=True)
            # Extract the re-ranked results
            re_ranked_results = [result[0][0] for result in scored_results]
            return re_ranked_results
        else:
            return []

    def initialize_vector_store(self):
        """Check if the vector store exists, if not, initialize it."""
        if os.path.exists(os.path.join(self.vector_db_path, "faiss_index.index")):
            print("FAISS index already initialized. Skipping re-embedding.")
        else:
            print("Initializing FAISS index for the first time...")
            self.create_vector_store()