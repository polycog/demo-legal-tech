"""document validator that applies the SIJ eligibility rule (INA § 101(a)(27)(J)) to the facts in case-facts.json"""

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from cognition import (
    OPERATOR_SELF_PARAM,
    DecisionProcess,
    DocEnum,
    EnumClassifier,
    IOContainer,
    Operator,
    uniform_evaluator,
)
from pydantic_ai.models import Model, infer_model

CASE_FACTS = Path(__file__).parent / "case-facts.json"
DEFAULT_LLM: Model = infer_model("openai:gpt-4o")


class CustodyOrder(DocEnum):
    """whether a case note establishes a state court custody or dependency order"""

    TRUE = (
        "true",
        "the note records a state court appointing a guardian for the applicant, placing the applicant "
        "in the custody of an individual or agency, or declaring the applicant dependent on the court",
    )
    FALSE = (
        "false",
        "the note does not record such an order, for example a finding only about reunification with a parent "
        "or about the applicant's best interest, or a court declining to make a custody order",
    )


class ReunificationNotViable(DocEnum):
    """whether a case note establishes that reunification with a parent is not viable"""

    TRUE = (
        "true",
        "the note records a state court finding that reunification of the applicant with one or both parents "
        "is not viable or not possible, due to abuse, neglect, abandonment, or a similar basis",
    )
    FALSE = (
        "false",
        "the note does not record such a finding, for example a finding only about custody or about the "
        "applicant's best interest, or a court finding that reunification is possible",
    )


class BestInterestNotToReturn(DocEnum):
    """whether a case note establishes that returning to the home country is not in the applicant's best interest"""

    TRUE = (
        "true",
        "the note records a state court finding that returning the applicant to their home country "
        "(or their parents' country of nationality or last habitual residence) is not in the applicant's best interest",
    )
    FALSE = (
        "false",
        "the note does not record such a finding, for example a finding only about custody or about reunification "
        "with a parent, or a court finding that return is in the applicant's best interest",
    )


NOTE_MARKS = {(True, False): "✓", (False, False): "✗", (False, True): "?"}
"""how a classified note is shown: ✓ establishes the fact, ✗ does not, ? the classifier could not decide"""


class Decision(StrEnum):
    """outcome of applying a rule to the case facts"""

    ELIGIBLE = "eligible"
    INELIGIBLE = "ineligible"


@dataclass
class CaseFacts:
    """minor premises: the facts of the case, as read from case-facts.json

    custody_order, reunification_not_viable, and best_interest_not_to_return start None (unknown)
    and are set true or false when a rule classifies the notes
    """

    applicant: str
    age: int
    married: bool
    state_court: str
    state_court_is_juvenile_court: bool
    custody_order: bool | None
    reunification_not_viable: bool | None
    best_interest_not_to_return: bool | None


@dataclass
class CaseState:
    """state of the validation: the facts, the decision, and the reasoning behind it

    the decision starts INELIGIBLE and is set ELIGIBLE only when Rule A fires
    """

    facts: CaseFacts
    notes: list[str] = field(default_factory=list)
    inferences: list[str] = field(default_factory=list)
    decision: Decision = Decision.INELIGIBLE
    reasons: list[str] = field(default_factory=list)


def load_case(path: Path) -> CaseState:
    """reads the `facts` object and `notes` list of a case-facts JSON file"""
    case = json.loads(path.read_text())
    facts = case["facts"]
    case_facts = CaseFacts(
        applicant=facts["applicant"],
        age=facts["age"],
        married=facts["married"],
        state_court=facts.get("state_court", ""),
        state_court_is_juvenile_court=facts.get("state_court_is_juvenile_court", False),
        custody_order=facts.get("custody_order"),
        reunification_not_viable=facts.get("reunification_not_viable"),
        best_interest_not_to_return=facts.get("best_interest_not_to_return"),
    )
    return CaseState(facts=case_facts, notes=case.get("notes", []))


class InferCustodyOrder(Operator[CaseState]):
    """
    a state court appointing a guardian, placing a child in custody, or declaring them dependent
    is a custody or dependency order

    INIT: instantiate a binary EnumClassifier for CustodyOrder
    when: the applicant has not been found eligible, AND whether a custody order exists is unknown
    then: classify the notes; a custody order exists if any note establishes one, and not otherwise
    """

    def __init__(self, name: str, llm: Model = DEFAULT_LLM, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._llm = llm
        self._classifier = EnumClassifier(
            CustodyOrder,
            task_desc="an immigration attorney is reviewing notes on a Special Immigrant Juvenile status case; "
            "does the note establish a state court order placing the applicant under custody, guardianship, or dependency",
        )

    def can_perform(self, state: CaseState, _io: IOContainer) -> bool:
        """propose when the applicant is not yet found eligible and custody is unknown"""
        return state.decision is Decision.INELIGIBLE and state.facts.custody_order is None

    def perform(self, state: CaseState, _io: IOContainer) -> None:
        """classifies each note (majority of three trials) until one establishes a custody order;
        sets custody_order true if one does, false otherwise"""
        print(f"\nIs there a state court custody or dependency order?")
        for note in state.notes:
            label, _confidence = self._classifier(note, self._llm, num_trials=3)
            print(f"  {NOTE_MARKS[label is CustodyOrder.TRUE, label is None]}  {note}")
            if label is CustodyOrder.TRUE:
                state.facts.custody_order = True
                state.inferences.append(f"custody order inferred from note: {note!r}")
                print("  → Yes, a custody order exists.")
                return
        state.facts.custody_order = False
        state.inferences.append("no note establishes a custody order")
        print("  → No, no note establishes a custody order.")


class InferReunificationNotViable(Operator[CaseState]):
    """
    a state court finding that reunification with a parent is impossible establishes it is not viable

    INIT: instantiate a binary EnumClassifier for ReunificationNotViable
    when: the applicant has not been found eligible, AND whether reunification is viable is unknown
    then: classify the notes; reunification is not viable if any note establishes it, and viable otherwise
    """

    def __init__(self, name: str, llm: Model = DEFAULT_LLM, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._llm = llm
        self._classifier = EnumClassifier(
            ReunificationNotViable,
            task_desc="an immigration attorney is reviewing notes on a Special Immigrant Juvenile status case; "
            "does the note establish a state court finding that the applicant cannot be reunified with a parent",
        )

    def can_perform(self, state: CaseState, _io: IOContainer) -> bool:
        """propose when the applicant is not yet found eligible and reunification viability is unknown"""
        return state.decision is Decision.INELIGIBLE and state.facts.reunification_not_viable is None

    def perform(self, state: CaseState, _io: IOContainer) -> None:
        """classifies each note (majority of three trials) until one establishes that reunification is not viable;
        sets reunification_not_viable true if one does, false otherwise"""
        print(f"\nDid the court find that reunification with a parent is not viable?")
        for note in state.notes:
            label, _confidence = self._classifier(note, self._llm, num_trials=3)
            print(f"  {NOTE_MARKS[label is ReunificationNotViable.TRUE, label is None]}  {note}")
            if label is ReunificationNotViable.TRUE:
                state.facts.reunification_not_viable = True
                state.inferences.append(f"reunification not viable inferred from note: {note!r}")
                print("  → Yes, reunification with a parent is not viable.")
                return
        state.facts.reunification_not_viable = False
        state.inferences.append("no note establishes that reunification is not viable")
        print("  → No, no note establishes that reunification is not viable.")


class InferBestInterestNotToReturn(Operator[CaseState]):
    """
    a state court finding that returning to the home country is not in the applicant's best interest
    establishes that fact

    INIT: instantiate a binary EnumClassifier for BestInterestNotToReturn
    when: the applicant has not been found eligible, AND whether return is in the applicant's best interest is unknown
    then: classify the notes; return is not in the best interest if any note establishes it, and is otherwise
    """

    def __init__(self, name: str, llm: Model = DEFAULT_LLM, **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._llm = llm
        self._classifier = EnumClassifier(
            BestInterestNotToReturn,
            task_desc="an immigration attorney is reviewing notes on a Special Immigrant Juvenile status case; "
            "does the note establish a state court finding that returning the applicant to their home country "
            "is not in their best interest",
        )

    def can_perform(self, state: CaseState, _io: IOContainer) -> bool:
        """propose when the applicant is not yet found eligible and the best-interest finding is unknown"""
        return state.decision is Decision.INELIGIBLE and state.facts.best_interest_not_to_return is None

    def perform(self, state: CaseState, _io: IOContainer) -> None:
        """classifies each note (majority of three trials) until one establishes that return is not in the
        applicant's best interest; sets best_interest_not_to_return true if one does, false otherwise"""
        print(f"\nDid the court find that returning home is not in the applicant's best interest?")
        for note in state.notes:
            label, _confidence = self._classifier(note, self._llm, num_trials=3)
            print(f"  {NOTE_MARKS[label is BestInterestNotToReturn.TRUE, label is None]}  {note}")
            if label is BestInterestNotToReturn.TRUE:
                state.facts.best_interest_not_to_return = True
                state.inferences.append(f"return not in best interest inferred from note: {note!r}")
                print("  → Yes, returning home is not in the applicant's best interest.")
                return
        state.facts.best_interest_not_to_return = False
        state.inferences.append("no note establishes that return is not in the applicant's best interest")
        print("  → No, no note establishes that returning home is not in the applicant's best interest.")


class ApplySIJRule(Operator[CaseState]):
    """
    Rule A, INA § 101(a)(27)(J): an applicant is eligible for Special Immigrant Juvenile status
    if and only if all of its conditions hold

    when: the applicant has not been found eligible, AND every condition of Rule A holds
    then: the applicant is ELIGIBLE
    """

    @staticmethod
    def conditions(f: CaseFacts) -> dict[str, bool]:
        """each condition of Rule A, and whether the facts satisfy it (an unknown fact is not satisfied)"""
        return {
            f"under 21 years old (age {f.age})": f.age < 21,
            "unmarried": not f.married,
            f"declared dependent or placed in custody by a state juvenile court ({f.state_court})": (
                f.state_court_is_juvenile_court and f.custody_order is True
            ),
            "reunification with a parent not viable due to abuse, neglect, abandonment, or similar": (
                f.reunification_not_viable is True
            ),
            "return to home country not in best interest": f.best_interest_not_to_return is True,
        }

    @classmethod
    def unmet(cls, f: CaseFacts) -> list[str]:
        """the conditions of Rule A the facts do not satisfy"""
        return [condition for condition, holds in cls.conditions(f).items() if not holds]

    def can_perform(self, state: CaseState, _io: IOContainer) -> bool:
        """propose when the applicant is not yet found eligible and every condition of Rule A holds"""
        return state.decision is Decision.INELIGIBLE and not self.unmet(state.facts)

    def perform(self, state: CaseState, _io: IOContainer) -> None:
        """decides the applicant is eligible, citing each condition it satisfied"""
        state.reasons = list(self.conditions(state.facts))
        state.decision = Decision.ELIGIBLE


def main() -> None:
    state = load_case(CASE_FACTS)

    operators: list[Operator[CaseState]] = [
        InferCustodyOrder("infer_custody_order"),
        InferReunificationNotViable("infer_reunification_not_viable"),
        InferBestInterestNotToReturn("infer_best_interest_not_to_return"),
        ApplySIJRule("apply_sij_rule"),
    ]

    dp: DecisionProcess[CaseState] = DecisionProcess(lambda: state)
    for op in operators:
        dp.add_operator(op)
    # inference rules set independent facts, so when several apply at once any order will do
    dp.add_action_evaluator(
        uniform_evaluator(
            0,
            lambda a: isinstance(
                a.params[OPERATOR_SELF_PARAM],
                (InferCustodyOrder, InferReunificationNotViable, InferBestInterestNotToReturn),
            ),
            name="inferences-in-any-order",
        )
    )
    # done once no operator applies: either Rule A has fired (ELIGIBLE),
    # or every fact is known and Rule A cannot fire (the decision stays INELIGIBLE)
    dp.add_termination_check(lambda s, io: not any(op.can_perform(s, io) for op in operators))
    dp.run_until_done()

    print(f"\nRule A, INA § 101(a)(27)(J), applied to {state.facts.applicant}:")
    for condition, holds in ApplySIJRule.conditions(state.facts).items():
        print(f"  {'✓' if holds else '✗'}  {condition}")
    print(f"\nConclusion: {state.facts.applicant} is {state.decision.upper()} for Special Immigrant Juvenile status.")


if __name__ == "__main__":
    main()
