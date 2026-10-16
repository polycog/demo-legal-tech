"""tests for the SIJ document validator; the LLM classifier is replaced by FakeClassifier (see conftest.py)"""

import random

import pytest

import validator
from conftest import MATEO_NOTES, UNDECIDABLE, make_case
from validator import (
    ApplySIJRule,
    CaseFacts,
    CaseState,
    Decision,
    InferBestInterestNotToReturn,
    InferCustodyOrder,
    InferReunificationNotViable,
    load_case,
)

INFER_OPERATORS = [
    (InferCustodyOrder, "custody_order", validator.CustodyOrder),
    (InferReunificationNotViable, "reunification_not_viable", validator.ReunificationNotViable),
    (InferBestInterestNotToReturn, "best_interest_not_to_return", validator.BestInterestNotToReturn),
]


def eligible_facts(**overrides) -> CaseFacts:
    """facts satisfying every condition of Rule A, with any overridden"""
    facts = dict(
        applicant="Mateo",
        age=17,
        married=False,
        state_court="California Superior Court",
        state_court_is_juvenile_court=True,
        custody_order=True,
        reunification_not_viable=True,
        best_interest_not_to_return=True,
    )
    facts.update(overrides)
    return CaseFacts(**facts)


# --- load_case ---------------------------------------------------------------------------------


class TestLoadCase:
    def test_reads_repo_case_file(self):
        state = load_case(validator.CASE_FACTS)
        assert state.facts.applicant == "Mateo"
        assert state.facts.age == 17
        assert state.facts.married is False
        assert state.facts.state_court == "California Superior Court"
        assert state.facts.state_court_is_juvenile_court is True
        assert len(state.notes) == 3

    def test_inferred_facts_start_unknown(self, write_case):
        state = load_case(write_case(make_case()))
        assert state.facts.custody_order is None
        assert state.facts.reunification_not_viable is None
        assert state.facts.best_interest_not_to_return is None

    def test_initial_state(self, write_case):
        state = load_case(write_case(make_case()))
        assert state.decision is Decision.INELIGIBLE
        assert state.inferences == []
        assert state.reasons == []
        assert state.notes == MATEO_NOTES

    def test_optional_fields_default(self, write_case):
        case = make_case()
        del case["facts"]["state_court"]
        del case["facts"]["state_court_is_juvenile_court"]
        del case["notes"]
        state = load_case(write_case(case))
        assert state.facts.state_court == ""
        assert state.facts.state_court_is_juvenile_court is False
        assert state.notes == []

    def test_inferred_facts_can_be_given_directly(self, write_case):
        case = make_case(custody_order=True, reunification_not_viable=False, best_interest_not_to_return=True)
        state = load_case(write_case(case))
        assert state.facts.custody_order is True
        assert state.facts.reunification_not_viable is False
        assert state.facts.best_interest_not_to_return is True

    @pytest.mark.parametrize("required", ["applicant", "age", "married"])
    def test_missing_required_fact_raises(self, write_case, required):
        case = make_case()
        del case["facts"][required]
        with pytest.raises(KeyError):
            load_case(write_case(case))


# --- Rule A ------------------------------------------------------------------------------------


class TestRuleAConditions:
    def test_all_conditions_hold(self):
        facts = eligible_facts()
        assert all(ApplySIJRule.conditions(facts).values())
        assert ApplySIJRule.unmet(facts) == []

    def test_five_conditions(self):
        assert len(ApplySIJRule.conditions(eligible_facts())) == 5

    def test_condition_labels_include_case_details(self):
        labels = list(ApplySIJRule.conditions(eligible_facts(age=19, state_court="Texas Juvenile Court")))
        assert "under 21 years old (age 19)" in labels
        assert any("Texas Juvenile Court" in label for label in labels)

    @pytest.mark.parametrize("age, holds", [(0, True), (17, True), (20, True), (21, False), (25, False)])
    def test_age_boundary(self, age, holds):
        facts = eligible_facts(age=age)
        assert ApplySIJRule.conditions(facts)[f"under 21 years old (age {age})"] is holds

    @pytest.mark.parametrize(
        "override, unmet_fragment",
        [
            ({"age": 21}, "under 21"),
            ({"married": True}, "unmarried"),
            ({"state_court_is_juvenile_court": False}, "declared dependent"),
            ({"custody_order": False}, "declared dependent"),
            ({"custody_order": None}, "declared dependent"),
            ({"reunification_not_viable": False}, "reunification"),
            ({"reunification_not_viable": None}, "reunification"),
            ({"best_interest_not_to_return": False}, "best interest"),
            ({"best_interest_not_to_return": None}, "best interest"),
        ],
    )
    def test_single_failing_condition(self, override, unmet_fragment):
        unmet = ApplySIJRule.unmet(eligible_facts(**override))
        assert len(unmet) == 1
        assert unmet_fragment in unmet[0]

    def test_unknown_facts_are_not_satisfied(self):
        facts = eligible_facts(custody_order=None, reunification_not_viable=None, best_interest_not_to_return=None)
        assert len(ApplySIJRule.unmet(facts)) == 3

    def test_unmet_lists_every_failure(self):
        facts = eligible_facts(age=30, married=True, custody_order=False)
        assert len(ApplySIJRule.unmet(facts)) == 3


class TestApplySIJRule:
    def test_can_perform_when_all_conditions_hold(self):
        op = ApplySIJRule("apply")
        assert op.can_perform(CaseState(facts=eligible_facts()), None)

    def test_cannot_perform_when_a_condition_fails(self):
        op = ApplySIJRule("apply")
        assert not op.can_perform(CaseState(facts=eligible_facts(married=True)), None)

    def test_cannot_perform_once_eligible(self):
        op = ApplySIJRule("apply")
        state = CaseState(facts=eligible_facts(), decision=Decision.ELIGIBLE)
        assert not op.can_perform(state, None)

    def test_perform_decides_eligible_with_reasons(self):
        op = ApplySIJRule("apply")
        state = CaseState(facts=eligible_facts())
        op.perform(state, None)
        assert state.decision is Decision.ELIGIBLE
        assert state.reasons == list(ApplySIJRule.conditions(state.facts))


# --- inference operators -------------------------------------------------------------------------


@pytest.mark.parametrize("op_cls, fact, enum_type", INFER_OPERATORS)
class TestInferOperators:
    def test_builds_classifier_for_its_enum(self, fake_classifier, op_cls, fact, enum_type):
        op = op_cls("infer")
        assert op._classifier.enum_type is enum_type
        assert "Special Immigrant Juvenile" in op._classifier.task_desc

    def test_can_perform_when_fact_unknown(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}))
        assert op_cls("infer").can_perform(state, None)

    @pytest.mark.parametrize("known", [True, False])
    def test_cannot_perform_when_fact_known(self, fake_classifier, op_cls, fact, enum_type, known):
        state = CaseState(facts=eligible_facts(**{fact: known}))
        assert not op_cls("infer").can_perform(state, None)

    def test_cannot_perform_once_eligible(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}), decision=Decision.ELIGIBLE)
        assert not op_cls("infer").can_perform(state, None)

    def test_sets_fact_true_from_supporting_note(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=list(MATEO_NOTES))
        op_cls("infer").perform(state, None)
        assert getattr(state.facts, fact) is True
        assert len(state.inferences) == 1
        assert "inferred from note" in state.inferences[0]

    def test_stops_at_first_supporting_note(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=list(MATEO_NOTES))
        op_cls("infer").perform(state, None)
        classified = [note for _, note, _ in fake_classifier]
        supporting = MATEO_NOTES[[op[1] for op in INFER_OPERATORS].index(fact)]
        assert classified[-1] == supporting
        assert classified == MATEO_NOTES[: MATEO_NOTES.index(supporting) + 1]
        assert supporting in state.inferences[0]

    def test_uses_three_trials_per_note(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=list(MATEO_NOTES))
        op_cls("infer").perform(state, None)
        assert all(trials == 3 for _, _, trials in fake_classifier)

    def test_sets_fact_false_when_no_note_supports_it(self, fake_classifier, op_cls, fact, enum_type):
        notes = ["The applicant attends high school.", "The hearing was continued to next month."]
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=notes)
        op_cls("infer").perform(state, None)
        assert getattr(state.facts, fact) is False
        assert [note for _, note, _ in fake_classifier] == notes
        assert state.inferences[0].startswith("no note establishes")

    def test_sets_fact_false_with_no_notes(self, fake_classifier, op_cls, fact, enum_type):
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=[])
        op_cls("infer").perform(state, None)
        assert getattr(state.facts, fact) is False
        assert fake_classifier == []

    def test_undecided_note_does_not_establish_fact(self, fake_classifier, op_cls, fact, enum_type, capsys):
        notes = [f"{UNDECIDABLE} something about guardian custody reunification best interest"]
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=notes)
        op_cls("infer").perform(state, None)
        assert getattr(state.facts, fact) is False
        assert f"?  {notes[0]}" in capsys.readouterr().out

    def test_does_not_touch_other_facts(self, fake_classifier, op_cls, fact, enum_type):
        facts = eligible_facts(custody_order=None, reunification_not_viable=None, best_interest_not_to_return=None)
        state = CaseState(facts=facts, notes=list(MATEO_NOTES))
        op_cls("infer").perform(state, None)
        others = {name for _, name, _ in INFER_OPERATORS} - {fact}
        assert all(getattr(state.facts, other) is None for other in others)
        assert state.decision is Decision.INELIGIBLE

    def test_prints_marks(self, fake_classifier, op_cls, fact, enum_type, capsys):
        state = CaseState(facts=eligible_facts(**{fact: None}), notes=list(MATEO_NOTES))
        op_cls("infer").perform(state, None)
        out = capsys.readouterr().out
        assert "✓" in out
        assert "→ Yes" in out


def test_note_marks():
    assert validator.NOTE_MARKS[True, False] == "✓"
    assert validator.NOTE_MARKS[False, False] == "✗"
    assert validator.NOTE_MARKS[False, True] == "?"


# --- end to end: main() --------------------------------------------------------------------------


@pytest.fixture
def run_main(fake_classifier, monkeypatch, write_case, capsys):
    """runs validator.main() on a case document, returning its printed output"""

    def _run(case: dict, seed: int = 0) -> str:
        monkeypatch.setattr(validator, "CASE_FACTS", write_case(case))
        random.seed(seed)
        validator.main()
        return capsys.readouterr().out

    return _run


class TestMain:
    @pytest.mark.parametrize("seed", range(5))
    def test_mateo_is_eligible_in_any_rule_order(self, run_main, seed):
        out = run_main(make_case(), seed)
        assert "Conclusion: Mateo is ELIGIBLE for Special Immigrant Juvenile status." in out
        assert "✗  under 21" not in out

    def test_each_question_asked_once(self, run_main):
        out = run_main(make_case())
        assert out.count("Is there a state court custody or dependency order?") == 1
        assert out.count("Did the court find that reunification with a parent is not viable?") == 1
        assert out.count("Did the court find that returning home is not in the applicant's best interest?") == 1

    def test_runs_on_repo_case_file(self, fake_classifier, capsys):
        validator.main()
        assert "Mateo is ELIGIBLE" in capsys.readouterr().out

    @pytest.mark.parametrize(
        "overrides, failing",
        [
            ({"age": 21}, "✗  under 21 years old (age 21)"),
            ({"married": True}, "✗  unmarried"),
            ({"state_court_is_juvenile_court": False}, "✗  declared dependent"),
            ({"notes": MATEO_NOTES[1:]}, "✗  declared dependent"),
            ({"notes": [MATEO_NOTES[0], MATEO_NOTES[2]]}, "✗  reunification"),
            ({"notes": MATEO_NOTES[:2]}, "✗  return to home country"),
            ({"notes": []}, "✗  declared dependent"),
        ],
    )
    def test_ineligible_when_a_condition_fails(self, run_main, overrides, failing):
        out = run_main(make_case(**overrides))
        assert "Conclusion: Mateo is INELIGIBLE" in out
        assert failing in out

    def test_given_facts_skip_inference(self, run_main, fake_classifier):
        case = make_case(custody_order=True, reunification_not_viable=True, best_interest_not_to_return=True, notes=[])
        out = run_main(case)
        assert fake_classifier == []
        assert "Is there a state court" not in out
        assert "Mateo is ELIGIBLE" in out

    def test_given_false_fact_overrides_notes(self, run_main):
        out = run_main(make_case(custody_order=False))
        assert "Is there a state court" not in out
        assert "Mateo is INELIGIBLE" in out

    def test_undecided_notes_never_make_eligible(self, run_main):
        notes = [f"{UNDECIDABLE} {note}" for note in MATEO_NOTES]
        out = run_main(make_case(notes=notes))
        assert "Mateo is INELIGIBLE" in out
