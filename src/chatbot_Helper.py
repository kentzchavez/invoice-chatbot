import os
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnableLambda, RunnableBranch
from dotenv import load_dotenv
from src.vectorStore.invoice_VectorStore import InvoiceVectorStore
from src.templates import Prompts

load_dotenv()

class InvoiceChatbot:
    def __init__(self, vector_store: InvoiceVectorStore = None):
        self.vector_store = vector_store  # Connect to vector store
        self.llm = ChatOpenAI(model="gpt-4o")  # Initialize LLM

        # Initialize memory in session state if not already set
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = ConversationBufferMemory(
                k=5, memory_key="history", return_messages=True
            )

        self.memory = st.session_state.chat_memory  # Use session-state memory

    def get_RAG_response(self, user_query):
        """Generate a chatbot response based on invoice data and chat history."""
        data = self.vector_store.query_similar_invoices(user_query["query"])

        print(data) # DEBUG

        chat_history = self.memory.load_memory_variables({})["history"]
        prompt = Prompts.get_RAG_response_prompt(query=user_query["query"], data=data, chat_history=chat_history)
        response = self.llm.invoke(prompt).content
        self.memory.save_context({"input": user_query["query"]}, {"output": response})
        return response

    def classify_query(self, user_query):
        """Classify the user query to determine the type of response."""
        chat_history = self.memory.load_memory_variables({})["history"]
        prompt = Prompts.classify_query_prompt(query=user_query, chat_history=chat_history)
        response = self.llm.invoke(prompt).content
        return {"query": user_query, "classification": response}

    def get_basic_response(self, user_query):
        """Generate a basic response using the LLM."""
        chat_history = self.memory.load_memory_variables({})["history"]
        prompt = Prompts.get_invoice_response_prompt(query=user_query["query"], data="", chat_history=chat_history)
        response = self.llm.invoke(prompt).content
        self.memory.save_context({"input": user_query["query"]}, {"output": response})
        return response
    
    def draft_email(self, user_query):
        """Draft an email based on the user query."""
        chat_history = self.memory.load_memory_variables({})["history"]
        prompt = Prompts.draft_email_prompt(query=user_query["query"], chat_history=chat_history)
        response = self.llm.invoke(prompt).content
        self.memory.save_context({"input": user_query["query"]}, {"output": response})
        return response
    
    def chain_run(self, user_query):
        classify_query_runnable = RunnableLambda(lambda x: self.classify_query(x))
        get_RAG_response_runnable = RunnableLambda(lambda x: self.get_RAG_response(x))
        get_basic_response_runnable = RunnableLambda(lambda x: self.get_basic_response(x))
        draft_email_runnable = RunnableLambda(lambda x: self.draft_email(x))

        query_branch = RunnableBranch(
        (lambda x: "RAG-II"  in x["classification"] , 
        get_RAG_response_runnable),
        (lambda x:  "ED"  in x["classification"] ,
        draft_email_runnable),
            get_basic_response_runnable
        )

        chain = classify_query_runnable | query_branch
        response = chain.invoke(user_query)
        return response

    def chatbot_ui(self):
        """Streamlit UI for the invoice chatbot."""
        st.subheader("Invoice Assistant")

        # Initialize session state for messages
        if 'messages' not in st.session_state:
            st.session_state['messages'] = []

        # Scrollable chat container (appears even when empty)
        with st.container(key="chatbot-container", height=700):
            # Ensure the box is always visible
            if not st.session_state['messages']:
                st.markdown("No messages yet. Ask something about invoices!")

            # Display chat history
            for message in st.session_state['messages']:
                with st.chat_message(message['role']):
                    st.markdown(message['content'])

        # Chat input
        if user_input := st.chat_input("Ask something about the invoices..."):
            # Add user message
            st.session_state['messages'].append({"role": "user", "content": user_input})

            # Display user message immediately
            with st.chat_message("user"):
                st.markdown(user_input)

            # Generate assistant response
            response = self.chain_run(user_input)

            # Add assistant response to history
            st.session_state['messages'].append({"role": "assistant", "content": response})

            # Force rerun to update chat display immediately
            st.rerun()
