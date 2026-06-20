from .config import GENERATION_MODEL, client
from .escalator import build_handoff_json, should_escalate


def generate_adaptive_response(query: str, persona: str, chunks: list[dict]) -> dict:
    if should_escalate(query, chunks):
        return {
            "escalated": True,
            "response": "I am connecting you with a human specialist.",
            "handoff": build_handoff_json(query, persona, chunks),
        }

    if persona == "Technical Expert":
        instr = "You are a Senior Engineer. Provide exact technical diagnostic paths, error codes, and parameters."
    elif persona == "Frustrated User":
        instr = "You are an empathetic agent. Validate frustration first, then provide simple, bulleted action items."
    else:
        instr = "You are a brief Executive Director. Provide high-level timelines and operational impacts only."

    context_text = "\n\n".join([f"Source [{chunk['source']}]: {chunk['text']}" for chunk in chunks])
    full_prompt = f"{instr}\n\nBase response strictly on context:\n{context_text}"

    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=f"{full_prompt}\n\nUser query: {query}",
        config={"temperature": 0.2},
    )
    return {"escalated": False, "response": response.text, "handoff": None}
