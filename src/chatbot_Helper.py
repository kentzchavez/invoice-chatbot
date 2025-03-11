import os
import streamlit as st
from langchain_openai import ChatOpenAI
from src.vectorStore.invoice_VectorStore import InvoiceVectorStore
from langchain_core.runnables import RunnableLambda
from dotenv import load_dotenv
from src.templates import Prompts

load_dotenv()

class InvoiceChatbot:
    def __init__(self, vector_store: InvoiceVectorStore = None):
        self.vector_store = vector_store  # Connect to vector store
        self.llm = ChatOpenAI(model="gpt-4o")  # Initialize LLM

    def get_response(self, user_query):
        """Generate a chatbot response based on invoice data."""
        data = self.vector_store.query_similar_invoices(user_query)
        prompt = Prompts.get_response_prompt(query=user_query, data=data)
        print('[PROMPT]:',prompt) ## DEBUG
        response = self.llm.invoke(prompt).content
        return response

    def chatbot_ui(self):
        """Streamlit UI for the invoice chatbot."""
        with st.container(border=True, key='chatbot-container'):
            st.subheader("Invoice Assistant")
            st.write("Ask anything about your invoices!")

            # Chat Input
            user_input = st.text_input("Ask something about the invoices...", key="chatbot_input")

            if user_input:
                response = self.get_response(user_input)
                st.write(f"**Response:** {response}")
