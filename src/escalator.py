import json


def should_escalate(query: str, chunks: list[dict], threshold: float = 0.45) -> bool:
    query_lower = query.lower()
    sensitive_topics = [
        "refund",
        "charge",
        "duplicate charges",
        "legal",
        "account change",
        "account modification",
    ]
    best_score = max((chunk["score"] for chunk in chunks), default=0.0)
    return best_score < threshold or any(topic in query_lower for topic in sensitive_topics)


def build_handoff_summary(query: str, persona: str, chunks: list[dict]) -> dict:
    best_score = max((chunk["score"] for chunk in chunks), default=0.0)
    return {
        "persona": persona,
        "detected_issue": query[:120],
        "retrieved_sources": [chunk["source"] for chunk in chunks],
        "confidence_score": best_score,
        "recommended_action": "Review issue manually and follow up with the customer.",
        "action": "Escalate to Human",
    }


def build_handoff_json(query: str, persona: str, chunks: list[dict]) -> str:
    return json.dumps(build_handoff_summary(query, persona, chunks), indent=2)
