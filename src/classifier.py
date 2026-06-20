def classify_persona(message: str) -> dict:
    message_lower = message.lower()

    technical_signals = [
        "api",
        "header",
        "headers",
        "bearer",
        "token",
        "endpoint",
        "parameter",
        "parameters",
        "stack trace",
        "database integration",
        "internal errors",
        "error code",
        "401",
        "debug",
    ]
    business_signals = [
        "timeline",
        "operational",
        "uptime",
        "impact",
        "business",
        "revenue",
        "resolution",
        "estimated",
        "summary",
    ]
    frustrated_signals = [
        "forgot",
        "password",
        "loading",
        "nothing is loading",
        "issue",
        "help",
        "broken",
        "not working",
        "frustrated",
        "hour",
        "cookies",
        "refund",
        "charge",
        "billing",
        "duplicate charges",
    ]

    if any(signal in message_lower for signal in technical_signals):
        persona = "Technical Expert"
        confidence = 0.92
        reasoning = "The message contains technical terminology and implementation-specific details."
    elif any(signal in message_lower for signal in business_signals):
        persona = "Business Executive"
        confidence = 0.9
        reasoning = "The message focuses on timelines, operational impact, and business-level concerns."
    elif any(signal in message_lower for signal in frustrated_signals):
        persona = "Frustrated User"
        confidence = 0.88
        reasoning = "The message shows a support request, friction, or billing concern that needs empathetic handling."
    else:
        persona = "Technical Expert"
        confidence = 0.7
        reasoning = "No strong executive or frustration signals were found, so a technical support framing is safest."

    return {
        "persona": persona,
        "confidence": confidence,
        "reasoning": reasoning,
    }
