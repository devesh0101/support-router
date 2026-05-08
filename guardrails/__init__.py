from guardrails.pii_redactor import redact_pii
from guardrails.injection_guard import check_injection


def process_input(text: str) -> tuple[str, dict]:
    """
    Runs all guardrails on incoming ticket text.
    Returns (processed_text, guard_report).
    """
    report = {
        "original_length": len(text),
        "injection_detected": False,
        "injection_reason": "",
        "pii_detected": [],
        "pii_redacted": False,
        "blocked": False,
        "block_reason": ""
    }

    # Step 1 — Check for prompt injection
    is_injection, reason = check_injection(text)
    if is_injection:
        report["injection_detected"] = True
        report["injection_reason"] = reason
        report["blocked"] = True
        report["block_reason"] = f"Prompt injection detected: {reason}"
        return text, report

    # Step 2 — Redact PII
    redacted_text, detected_types = redact_pii(text)
    if detected_types:
        report["pii_detected"] = detected_types
        report["pii_redacted"] = True

    return redacted_text, report