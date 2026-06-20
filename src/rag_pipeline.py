from pathlib import Path

import chromadb
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .config import CHROMA_DB_DIR, DATA_DIR, EMBEDDING_MODEL, client


def get_vector_db():
    chroma_client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
    return chroma_client.get_or_create_collection(name="support_kb")


def load_support_documents() -> list[dict]:
    supported_suffixes = {".md", ".txt", ".pdf"}
    documents = []

    if not DATA_DIR.exists():
        return documents

    for file_path in sorted(DATA_DIR.iterdir()):
        if not file_path.is_file() or file_path.suffix.lower() not in supported_suffixes:
            continue

        if file_path.suffix.lower() in {".md", ".txt"}:
            content = file_path.read_text(encoding="utf-8")
        else:
            reader = PdfReader(str(file_path))
            content = "\n".join(page.extract_text() or "" for page in reader.pages)

        documents.append({"source": file_path.name, "text": content})

    return documents


def embed_text(text: str) -> list:
    emb_resp = client.models.embed_content(model=EMBEDDING_MODEL, contents=text)
    return emb_resp.embeddings[0].values


def seed_knowledge_base(collection) -> int:
    if collection.count() != 0:
        return 0

    docs = load_support_documents()
    if not docs:
        return 0

    splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)
    inserted_chunks = 0

    for doc in docs:
        chunks = splitter.split_text(doc["text"])
        for idx, chunk in enumerate(chunks):
            embedding = embed_text(chunk)
            collection.add(
                ids=[f"{doc['source']}_{idx}"],
                embeddings=[embedding],
                metadatas=[{"source": doc["source"], "chunk_index": idx}],
                documents=[chunk],
            )
            inserted_chunks += 1

    return inserted_chunks


def retrieve_context(collection, query: str, top_k: int = 3) -> list[dict]:
    query_embedding = embed_text(query)
    search_res = collection.query(query_embeddings=[query_embedding], n_results=top_k)

    chunks = []
    if search_res and search_res.get("documents") and search_res["documents"][0]:
        for index in range(len(search_res["documents"][0])):
            chunks.append(
                {
                    "text": search_res["documents"][0][index],
                    "source": search_res["metadatas"][0][index]["source"],
                    "score": 1.0 - (search_res["distances"][0][index] if search_res.get("distances") else 0.0),
                }
            )
    return chunks
