import os

import streamlit as st
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="Persona Support Agent", layout="wide")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    os.environ["GEMINI_API_KEY"] = api_key
else:
    st.error("Missing GEMINI_API_KEY in environment variables or Streamlit secrets.")
    st.stop()

from src.classifier import classify_persona
from src.generator import generate_adaptive_response
from src.rag_pipeline import get_vector_db, retrieve_context, seed_knowledge_base


@st.cache_resource
def get_collection():
    return get_vector_db()


collection = get_collection()
seed_count = seed_knowledge_base(collection)
if seed_count:
    st.success(f"Knowledge base seeded from {seed_count} chunks!")
elif collection.count() == 0:
    st.warning("No support documents found in the data/ folder.")

st.title("Persona-Adaptive Support Center")
user_input = str(st.text_input("Customer Input message:", placeholder="Type a message..."))

if st.button("Submit Request") and user_input:
    with st.spinner("Processing..."):
        analysis = classify_persona(user_input)
        chunks = retrieve_context(collection, user_input, top_k=3)
        output = generate_adaptive_response(user_input, analysis["persona"], chunks)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Classification & Metadata Metrics")
            st.metric("Detected Persona", analysis["persona"])
            st.json(analysis)
        with col2:
            st.subheader("Agent Engine Output")
            if output["escalated"]:
                st.error("Escalated to Human Agent!")
                st.write(output["response"])
                st.code(output["handoff"], language="json")
            else:
                st.success("Auto-Resolved by AI")
                st.write(output["response"])