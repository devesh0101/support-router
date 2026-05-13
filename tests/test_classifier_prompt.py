from prompts.classifier import CLASSIFIER_SYSTEM_PROMPT


def test_classifier_prompt_exists():
    assert CLASSIFIER_SYSTEM_PROMPT is not None
    assert len(CLASSIFIER_SYSTEM_PROMPT) > 0


def test_classifier_prompt_has_categories():
    assert "billing" in CLASSIFIER_SYSTEM_PROMPT.lower()
    assert "technical" in CLASSIFIER_SYSTEM_PROMPT.lower()
    assert "refund" in CLASSIFIER_SYSTEM_PROMPT.lower()


def test_classifier_prompt_has_escalation_rules():
    assert "escalat" in CLASSIFIER_SYSTEM_PROMPT.lower()


def test_classifier_prompt_requires_json():
    assert "json" in CLASSIFIER_SYSTEM_PROMPT.lower()