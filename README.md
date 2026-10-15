# SIJ Document Validator

A **neurosymbolic** document validator built with the **`cognition`** library. It reads the facts and court notes of an immigration case from `case-facts.json`, and decides whether the applicant qualifies for **Special Immigrant Juvenile (SIJ) status** under [INA § 101(a)(27)(J)](https://libguides.law.rutgers.edu/c.php?g=858689&p=6152306).

The validator splits the work between two kinds of reasoning:

- **Neural: reading the text.** An LLM reads the court's notes, written in plain English, and turns each finding into a fact: was a custody order issued? Is reunification with a parent not viable? Is returning home not in the applicant's best interest? Each answer cites the note it came from.
- **Symbolic: applying the law.** The legal rules are written as code. Each rule is an `Operator` whose conditions are spelled out in `can_perform`, and the validator applies them to the facts by deduction to reach its conclusion. No LLM is involved in this step, so the conclusion follows from the facts exactly as the law says, and every step can be checked.

This neurosymbolic validator [reasons the way an expert, attorney, or judge would](https://www.judcom.nsw.gov.au/publications/benchbks/judicial_officers/argumentation_in_legal_reasoning.html#id-1.4.4.4.7):
1. **Major premise (the law):** Rule A lists the conditions for SIJ eligibility.
2. **Minor premises (the facts):** the case facts, some stated directly and some inferred from the court's notes by the LLM.
3. **Conclusion:** the applicant is eligible if and only if every condition of Rule A holds.

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

The validator works like a careful paralegal with a checklist. It has four rules, and each rule says **when** it applies and **what** it does. The validator keeps checking which rules apply, carries one out, and repeats until none apply.

**Step 1: Fill in the missing facts (neural).** Three facts aren't stated directly and have to be found in the court's notes. Each has its own rule, which asks the LLM to read the notes one at a time and answer a yes-or-no question:

| Rule | Question it answers from the notes |
|---|---|
| Find custody order | Did a state court appoint a guardian, place the applicant in custody, or declare them dependent? |
| Find reunification not viable | Did the court find that the applicant can't be reunited with a parent because of abuse, neglect, abandonment, or something similar? |
| Find best interest not to return | Did the court find that going back to their home country is not in the applicant's best interest? |

A rule stops reading as soon as it finds a note that answers "yes", and records that note as its evidence. If no note says so, the answer is "no". Each question is asked only once.

**Step 2: Apply the law (symbolic).** Once every fact is known, the last rule, **Apply Rule A**, checks all five conditions of the law. No LLM is used here; it is a plain check of the facts against the conditions.

- If every condition holds, the applicant is **ELIGIBLE**, and the validator lists the fact behind each condition.
- If any condition fails, the applicant stays **INELIGIBLE**, which is the starting answer, and the validator lists the conditions that were not met.

Because the decision starts as INELIGIBLE and only a fully satisfied Rule A can change it, the validator never says "eligible" on missing or uncertain information.

> **For developers:** each rule is an `Operator` in `validator.py`, with its "when" in `can_perform` and its "what" in `perform`. The fact-finding rules (`InferCustodyOrder`, `InferReunificationNotViable`, `InferBestInterestNotToReturn`) each use a yes/no `EnumClassifier`; they can run in any order, so a `uniform_evaluator` picks among them at random. The conditions of Rule A are defined once, in `ApplySIJRule.conditions`.

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
