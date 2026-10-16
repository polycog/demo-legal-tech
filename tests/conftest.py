"""shared fixtures: an offline stand-in for the LLM note classifier, and helpers to build cases"""

import json
import os
import sys
from pathlib import Path

import pytest

# validator builds its default model at import time, which needs a key; tests never call the real API
os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-a-real-key")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import validator  # noqa: E402

KEYWORDS = {
    validator.CustodyOrder: ("guardian", "custody", "dependent"),
    validator.ReunificationNotViable: ("reunification", "reunified"),
    validator.BestInterestNotToReturn: ("best interest",),
}
"""a note establishes a fact for the fake classifier when it contains one of the fact's keywords"""

UNDECIDABLE = "[undecidable]"
"""a note containing this marker makes the fake classifier return None, as an undecided LLM would"""


class FakeClassifier:
    """stands in for EnumClassifier: labels notes by keyword and records every call"""

    calls: list[tuple[type, str, int]] = []

    def __init__(self, enum_type: type, task_desc: str | None = None) -> None:
        self.enum_type = enum_type
        self.task_desc = task_desc

    def __call__(self, utterance: str, llm, num_trials: int = 3, timeout_secs: int = 10):
        FakeClassifier.calls.append((self.enum_type, utterance, num_trials))
        if UNDECIDABLE in utterance:
            return None, None
        lowered = utterance.lower()
        if any(word in lowered for word in KEYWORDS[self.enum_type]):
            return self.enum_type.TRUE, None
        return self.enum_type.FALSE, None


@pytest.fixture
def fake_classifier(monkeypatch):
    """replaces the LLM classifier in validator with FakeClassifier, and returns its call log"""
    FakeClassifier.calls = []
    monkeypatch.setattr(validator, "EnumClassifier", FakeClassifier)
    return FakeClassifier.calls


MATEO_NOTES = [
    "The California Superior Court legally appointed Mateo's aunt as his guardian.",
    "The court formally found that reunification with Mateo's father is impossible due to severe abandonment.",
    "The court found that returning to his home country would expose Mateo to unsafe living conditions "
    "and is not in his best interest.",
]


def make_case(**fact_overrides) -> dict:
    """a case-facts document for an eligible applicant, with any facts overridden"""
    facts = {
        "applicant": "Mateo",
        "age": 17,
        "married": False,
        "state_court": "California Superior Court",
        "state_court_is_juvenile_court": True,
    }
    notes = fact_overrides.pop("notes", MATEO_NOTES)
    facts.update(fact_overrides)
    return {"case": "test case", "petition": "test petition", "facts": facts, "notes": notes}


@pytest.fixture
def write_case(tmp_path):
    """writes a case-facts document to a temp file and returns its path"""

    def _write(case: dict) -> Path:
        path = tmp_path / "case-facts.json"
        path.write_text(json.dumps(case))
        return path

    return _write
