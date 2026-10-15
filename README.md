# SIJ Document Validator

A document validator built with the **`cognition`** library. It reads the facts and court notes of an immigration case from `case-facts.json`, and decides whether the applicant qualifies for **Special Immigrant Juvenile (SIJ) status** under [INA § 101(a)(27)(J)](https://libguides.law.rutgers.edu/c.php?g=858689&p=6152306).

The validator reasons the way an attorney or judge would, by deduction:

1. **Major premise (the law):** Rule A lists the conditions for SIJ eligibility.
2. **Minor premises (the facts):** the case facts, some stated directly and some inferred from the court's notes.
3. **Conclusion:** the applicant is eligible if and only if every condition of Rule A holds.

An LLM is used only to read the notes. The deduction itself is symbolic: each legal rule is an `Operator` whose conditions are spelled out in `can_perform`.

**Demo:** [watch the validator run on Mateo's case](https://drive.google.com/file/d/14jnK5VI7ICHNg4FS9kUgCo29eMzOwxG5/view?usp=sharing)

---

## The Law: Rule A

Under INA § 101(a)(27)(J), an applicant is eligible for SIJ status **if and only if**:

1. they are under 21 years old, AND
2. they are unmarried, AND
3. a state juvenile court has declared them dependent or placed them in the custody of an individual or agency, AND
4. the state court determined that reunification with one or both parents is not viable due to abuse, neglect, abandonment, or a similar basis, AND
5. the state court determined it is not in their best interest to return to their home country.

---

## The Facts: `case-facts.json`

```json
{
  "case": "Mateo — Special Immigrant Juvenile Status",
  "petition": "Petition for Special Immigrant Juvenile (SIJ) classification under INA § 101(a)(27)(J).",
  "facts": {
    "applicant": "Mateo",
    "age": 17,
    "married": false,
    "state_court": "California Superior Court",
    "state_court_is_juvenile_court": true
  },
  "notes": [
    "The California Superior Court legally appointed Mateo's aunt as his guardian.",
    "The court formally found that reunification with Mateo's father is impossible due to severe abandonment.",
    "The court found that returning to his home country would expose Mateo to unsafe living conditions and is not in his best interest."
  ]
}
```

- **`facts`** holds the facts stated directly: `applicant`, `age`, `married`, `state_court`, `state_court_is_juvenile_court`.
- **`notes`** holds the court's findings in plain English. The validator infers three facts from them. Each starts unknown (`null`), and is set true if some note records the finding below, false otherwise:

| Fact | Set true when a note records… |
|---|---|
| `custody_order` | the state court appointing a guardian, placing the applicant in custody, or declaring them dependent |
| `reunification_not_viable` | a state court finding that reunification with a parent is not viable due to abuse, neglect, abandonment, or similar |
| `best_interest_not_to_return` | a state court finding that returning to the home country is not in the applicant's best interest |

An inferred fact can also be given directly in `facts` as `true` or `false`. It is then known from the start, and its rule doesn't fire.

---

## The Decision Process

The validator is a single `DecisionProcess[CaseState]` with four operators. Each cycle, the operators whose `can_perform` holds are proposed, one is chosen, and its `perform` updates the state.

The decision starts as **INELIGIBLE**. Only `ApplySIJRule` can change it, to **ELIGIBLE**. The process stops when no operator applies any more. That happens either when the applicant has been found **ELIGIBLE**, or when every fact is known and a condition of Rule A fails, so the rule can never fire and the decision stays **INELIGIBLE**. The unmet conditions (`ApplySIJRule.unmet`) are then listed to explain it.

| Operator | When | Then |
|---|---|---|
| `InferCustodyOrder` | not yet eligible, AND `custody_order` is unknown | classify the notes with a binary `EnumClassifier` over `CustodyOrder` (`TRUE`/`FALSE`); set `custody_order` true if a note establishes a custody order (citing it), false otherwise |
| `InferReunificationNotViable` | not yet eligible, AND `reunification_not_viable` is unknown | classify the notes with a binary `EnumClassifier` over `ReunificationNotViable`; set `reunification_not_viable` true if a note establishes it (citing it), false otherwise |
| `InferBestInterestNotToReturn` | not yet eligible, AND `best_interest_not_to_return` is unknown | classify the notes with a binary `EnumClassifier` over `BestInterestNotToReturn`; set `best_interest_not_to_return` true if a note establishes it (citing it), false otherwise |
| `ApplySIJRule` | not yet eligible, AND all five conditions of Rule A hold | set the decision to **ELIGIBLE**, citing the facts for each condition |

`ApplySIJRule` cannot fire before the inference rules have run: an unknown fact does not satisfy its condition, and only an inference rule can make it true.

### Design notes

- **Conditions live in `can_perform`.** Each operator states its "when" in full, so the rules read like the law and can be checked against it.
- **One binary classifier per inference rule.** Each inference rule builds its own `EnumClassifier` over a two-valued `DocEnum` in `__init__`. `can_perform` only checks that its fact is unknown; `perform` classifies the notes, stopping at the first that establishes the fact, and sets the fact true or false. Because the fact is then known, the rule runs, and calls the LLM, once.
- **`ApplySIJRule` never overlaps with another operator.** When more than one operator applies, `cognition` asks the registered action evaluators to rank them, and raises `No action rankings` if none are registered. The three inference rules set independent facts and can apply in the same cycle, so a `uniform_evaluator` ranks them equally and one is chosen at random. `ApplySIJRule` is kept apart from them by its conditions, so an overlap there raises an error instead of being silently resolved.
- **Ineligible is the default.** Like the inferred facts, the decision starts in its negative state and only a rule can make it positive: `ApplySIJRule` is the "if" of Rule A, and the INELIGIBLE default covers the "only if". The conditions of Rule A are defined once, in `ApplySIJRule.conditions`: `can_perform` checks that all hold, `perform` cites them, and `ApplySIJRule.unmet` (used for the explanation) lists those that fail, so changing a condition in one place changes it everywhere.

---

## Installation

### 1. Create a Python environment

`cognition` requires **Python 3.13 or later**.

```bash
# with venv
python3.13 -m venv .venv
source .venv/bin/activate

# or with conda
conda create -n sij-validator python=3.13
conda activate sij-validator
```

### 2. Install `cognition`

`cognition` is published on PyPI as the `polycog-cognition` package:

```bash
pip install polycog-cognition
```

This also installs `pydantic-ai-slim` (2.9.x), which `cognition` builds on.

### 3. Install `pydantic-ai` with OpenAI support

The note classifier runs on `openai:gpt-4o`, which needs the OpenAI extra of `pydantic-ai`:

```bash
pip install "pydantic-ai-slim[openai]~=2.9.1"
```

Check the install:

```bash
python -c "import cognition, pydantic_ai, openai; print('ok')"
```

### 4. Set your OpenAI API key

Create a key at <https://platform.openai.com/api-keys>, then export it in the shell you run the validator from:

```bash
export OPENAI_API_KEY="sk-..."
```

To keep it across sessions, add that line to your shell profile (`~/.zshrc` on macOS, `~/.bashrc` on most Linux systems) and open a new terminal. Check it is set with:

```bash
echo ${OPENAI_API_KEY:+set}
```

Keep the key out of the repository: don't write it into `validator.py` or `case-facts.json`.

---

## Running

```bash
python validator.py
```

Output for the case above:

```
Is there a state court custody or dependency order?
  ✓  The California Superior Court legally appointed Mateo's aunt as his guardian.
  → Yes, a custody order exists.

Did the court find that reunification with a parent is not viable?
  ✗  The California Superior Court legally appointed Mateo's aunt as his guardian.
  ✓  The court formally found that reunification with Mateo's father is impossible due to severe abandonment.
  → Yes, reunification with a parent is not viable.

Did the court find that returning home is not in the applicant's best interest?
  ✗  The California Superior Court legally appointed Mateo's aunt as his guardian.
  ✗  The court formally found that reunification with Mateo's father is impossible due to severe abandonment.
  ✓  The court found that returning to his home country would expose Mateo to unsafe living conditions and is not in his best interest.
  → Yes, returning home is not in the applicant's best interest.

Rule A, INA § 101(a)(27)(J), applied to Mateo:
  ✓  under 21 years old (age 17)
  ✓  unmarried
  ✓  declared dependent or placed in custody by a state juvenile court (California Superior Court)
  ✓  reunification with a parent not viable due to abuse, neglect, abandonment, or similar
  ✓  return to home country not in best interest

Conclusion: Mateo is ELIGIBLE for Special Immigrant Juvenile status.
```

Each question is one inference rule at work: ✓ marks the note that establishes the fact, ✗ a note that does not, and ? a note the classifier could not decide on. A rule stops at the first ✓.

The inference rules may fire in a different order on each run; the conclusion does not change. Each inference rule makes 3 LLM calls per note it classifies, stopping at the first note that establishes its fact (up to 27 for this case).

To validate another case, edit `case-facts.json`, or point `CASE_FACTS` in `validator.py` at a different file.

---

## Files

| File | Contents |
|---|---|
| `validator.py` | the state, operators, and decision process |
| `case-facts.json` | the facts and court notes for the case being validated |
