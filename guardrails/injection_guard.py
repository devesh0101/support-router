import re

# Patterns that signal prompt injection attempts
INJECTION_PATTERNS = [
    r"ignore (all )?(previous|prior|above) instructions",
    r"disregard (all )?(previous|prior|above) instructions",
    r"forget (all )?(previous|prior|above) instructions",
    r"you are now",
    r"new persona",
    r"act as (a |an )?(?!support|helpful|customer)",
    r"pretend (you are|to be)",
    r"jailbreak",
    r"do anything now",
    r"dan mode",
    r"developer mode",
    r"override (all )?(previous )?instructions",
    r"system prompt",
    r"reveal (your )?(instructions|prompt|system)",
    r"print (your )?(instructions|prompt|system)",
    r"what (are|were) your instructions",
]

COMPILED_PATTERNS = [
    re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS
]


def check_injection(text: str) -> tuple[bool, str]:
    """
    Checks if text contains prompt injection attempts.
    Returns (is_injection, reason).
    """
    for pattern in COMPILED_PATTERNS:
        if pattern.search(text):
            return True, f"Detected suspicious pattern: '{pattern.pattern}'"

    # Check for unusually high ratio of special characters
    special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
    if len(text) > 20 and special_chars / len(text) > 0.4:
        return True, "Unusually high special character ratio"

    return False, ""