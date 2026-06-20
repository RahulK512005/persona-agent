import os
import json
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
import chromadb
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 1. Initialization & Config
load_dotenv()
st.set_page_config(page_title="Persona Support Agent", layout="wide")

if "GEMINI_API_KEY" not in os.environ:
    st.error("Missing GEMINI_API_KEY in environment variables.")
    st.stop()

client = genai.Client(
    api_key=os.environ["GEMINI_API_KEY"],
    http_options=types.HttpOptions(apiVersion="v1"),
)

GENERATION_MODEL = "models/gemini-2.5-flash"
EMBEDDING_MODEL = "models/gemini-embedding-001"


def parse_json_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]
    return json.loads(cleaned.strip())


def normalize_persona(persona: str, message: str) -> str:
    message_lower = message.lower()
    if any(word in message_lower for word in ["refund", "charge", "forgot", "password", "error", "issue", "help", "broken", "not working"]):
        return "Frustrated User"
    if any(word in message_lower for word in ["timeline", "impact", "budget", "revenue", "executive", "business"]):
        return "Business Executive"
    if any(word in message_lower for word in ["api", "endpoint", "token", "401", "error code", "parameter", "stack trace", "debug"]):
        return "Technical Expert"
    persona_lower = persona.strip().lower()
    if persona_lower in {"technical expert", "frustrated user", "business executive"}:
        return "Business Executive" if persona_lower == "business executive" else persona.title()
    return "Technical Expert"

@st.cache_resource
def get_vector_db():
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    return chroma_client.get_or_create_collection(name="support_kb")

collection = get_vector_db()

# 2. Automated Seed Data (Saves time creating manual text files)
def seed_knowledge_base():
    if collection.count() == 0:
        docs = {
            "api_troubleshooting.md": "To fix 401 Unauthorized errors on API calls, verify the bearer token header. Ensure format is 'Authorization: Bearer <token>'. Production tokens expire every 90 days.",
            "billing_policy.txt": "Refund requests are processed within 5-7 business days. All duplicate charges are flagged automatically and sent to human review. Contact billing@company.com.",
            "password_reset_guide.md": "Users can change credentials via the account security dashboard. Click 'Forgot Password', verify the email OTP, and enter a new alpha-numeric password."
        }
        splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
        for name, text in docs.items():
            chunks = splitter.split_text(text)
            for idx, chunk in enumerate(chunks):
                emb_resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=chunk)
                embedding = emb_resp.embeddings[0].values
                collection.add(
                    ids=[f"{name}_{idx}"],
                    embeddings=[embedding],
                    metadatas=[{"source": name}],
                    documents=[chunk]
                )
        st.success("Knowledge Base auto-seeded successfully!")

seed_knowledge_base()

# 3. Step 2 & 4 Core AI Functions
def classify_persona(msg: str) -> dict:
    sys_prompt = "Analyze sentiment/tone. Classify into exactly one of: Technical Expert, Frustrated User, or Business Executive. Return only JSON."
    resp = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=f"{sys_prompt}\n\nMessage: {msg}\n\nReturn only valid JSON with persona, confidence, and reasoning."
    )
    analysis = parse_json_response(resp.text)
    analysis["persona"] = normalize_persona(str(analysis.get("persona", "")), msg)
    return analysis

def generate_adaptive_response(query: str, persona: str, chunks: list) -> dict:
    best_score = max([c["score"] for c in chunks]) if chunks else 0.0
    # Escalation Logic Threshold check (Triggered if score < 0.30 or billing issue)
    if best_score < 0.30 or "refund" in query.lower() or "charge" in query.lower():
        handoff = {"persona": persona, "query_preview": query[:50], "confidence": best_score, "action": "Escalate to Human"}
        return {"escalated": True, "response": "I am connecting you with a human specialist.", "handoff": json.dumps(handoff, indent=2)}

    if persona == "Technical Expert":
        instr = "You are a Senior Engineer. Provide exact technical diagnostic paths, error codes, and parameters."
    elif persona == "Frustrated User":
        instr = "You are an empathetic agent. Validate frustration first, then provide simple, bulleted action items."
    else:
        instr = "You are a brief Executive Director. Provide high-level timelines and operational impacts only."

    context_text = "\n\n".join([f"Source [{c['source']}]: {c['text']}" for c in chunks])
    full_prompt = f"{instr}\n\nBase response strictly on context:\n{context_text}"
    
    resp = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=f"{full_prompt}\n\nUser query: {query}",
        config=types.GenerateContentConfig(temperature=0.2)
    )
    return {"escalated": False, "response": resp.text, "handoff": None}

# 4. Streamlit Interactive Interface
st.title("Persona-Adaptive Support Center")
user_input = str(st.text_input("Customer Input message:", placeholder="Type a message..."))

if st.button("Submit Request") and user_input:
    with st.spinner("Processing..."):
        # Run classification
        analysis = classify_persona(user_input)
        
        # Run semantic search
        q_emb = client.models.embed_content(model=EMBEDDING_MODEL, contents=user_input).embeddings[0].values
        search_res = collection.query(query_embeddings=[q_emb], n_results=2)
        
        chunks = []
        if search_res and search_res['documents'][0]:
            for i in range(len(search_res['documents'][0])):
                chunks.append({
                    "text": search_res['documents'][0][i],
                    "source": search_res['metadatas'][0][i]['source'],
                    "score": 1.0 - (search_res['distances'][0][i] if search_res['distances'] else 0.0)
                })
        
        # Generate final response
        output = generate_adaptive_response(user_input, analysis["persona"], chunks)
        
        # Display Results
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