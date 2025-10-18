import streamlit as st
import os
from dotenv import load_dotenv
from rag_pipeline.rag_chain import FinancialNewsRAG

# Load environment variables
load_dotenv()

# Initialize RAG system
rag = FinancialNewsRAG(openai_api_key=os.getenv("OPENAI_API_KEY"))

# Set up Streamlit page
st.set_page_config(
    page_title="Financial News QA",
    page_icon="📈",
    layout="wide"
)

# Title and description
st.title("Financial News Question Answering")
st.markdown("""
Ask questions about financial news and get AI-powered answers based on the latest news articles.
The system uses RAG (Retrieval Augmented Generation) to provide accurate and up-to-date information.
""")

# Question input
question = st.text_input("Enter your question about financial news:")

if question:
    with st.spinner("Searching for relevant information..."):
        # Get answer from RAG system
        result = rag.answer_question(question)
        
        # Display answer
        st.subheader("Answer")
        st.write(result["answer"])
        
        # Display sources
        st.subheader("Sources")
        for i, source in enumerate(result["sources"], 1):
            with st.expander(f"Source {i}: {source['metadata']['title']}"):
                st.write(source["text"])
                st.caption(f"Source: {source['metadata']['source']}")
                st.caption(f"Published: {source['metadata']['published_date']}")
                st.caption(f"URL: {source['metadata']['url']}")

# Add footer
st.markdown("---")
st.markdown("Built with Streamlit, LangChain, and OpenAI") 