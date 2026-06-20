import json
import re

from .config import GENERATION_MODEL, client


def parse_json_response(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1]
        if cleaned.endswith("```"):
            cleaned = cleaned.rsplit("```", 1)[0]

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        cleaned = match.group(0)

    return json.loads(cleaned.strip())


def normalize_persona(persona: str, message: str) -> str:
    message_lower = message.lower()
    if any(word in message_lower for word in ["refund", "charge", "billing", "forgot", "password", "error", "issue", "help", "broken", "not working"]):
        return "Frustrated User"
    if any(word in message_lower for word in ["timeline", "impact", "budget", "revenue", "executive", "business"]):
        return "Business Executive"
    if any(word in message_lower for word in ["api", "endpoint", "token", "401", "error code", "parameter", "stack trace", "debug"]):
        return "Technical Expert"

    persona_lower = persona.strip().lower()
    if persona_lower in {"technical expert", "frustrated user", "business executive"}:
        return "Business Executive" if persona_lower == "business executive" else persona.title()
    return "Technical Expert"


def classify_persona(message: str) -> dict:
    system_prompt = (
        "Analyze sentiment/tone. Classify into exactly one of: Technical Expert, "
        "Frustrated User, or Business Executive. Return only JSON."
    )
    response = client.models.generate_content(
        model=GENERATION_MODEL,
        contents=(
            f"{system_prompt}\n\n"
            f"Message: {message}\n\n"
            "Return only valid JSON with persona, confidence, and reasoning."
        ),
    )
    analysis = parse_json_response(response.text)
    analysis["persona"] = normalize_persona(str(analysis.get("persona", "")), message)
    return analysis
