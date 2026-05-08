from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig


analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

# PII types to detect and redact
PII_ENTITIES = [
    "EMAIL_ADDRESS",
    "PHONE_NUMBER",
    "CREDIT_CARD",
    "US_SSN",
    "IP_ADDRESS",
    "PERSON",
    "LOCATION",
]


def redact_pii(text: str) -> tuple[str, list]:
    """
    Detects and redacts PII from text.
    Returns (redacted_text, list of detected PII types).
    """
    results = analyzer.analyze(
        text=text,
        entities=PII_ENTITIES,
        language="en"
    )

    if not results:
        return text, []

    detected_types = list({r.entity_type for r in results})

    anonymized = anonymizer.anonymize(
        text=text,
        analyzer_results=results,
        operators={
            "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
            "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[PHONE]"}),
            "CREDIT_CARD": OperatorConfig("replace", {"new_value": "[CREDIT_CARD]"}),
            "US_SSN": OperatorConfig("replace", {"new_value": "[SSN]"}),
            "IP_ADDRESS": OperatorConfig("replace", {"new_value": "[IP_ADDRESS]"}),
            "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
            "LOCATION": OperatorConfig("replace", {"new_value": "[LOCATION]"}),
        }
    )

    return anonymized.text, detected_types