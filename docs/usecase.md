# Problem Statement and Opportunity

## Problem statement

### What eligibility requires

Evaluating complex legal applications requires synthesizing unstructured case facts against intricate statutory requirements. In immigration processing, for instance, determining eligibility for [Special Immigrant Juvenile (SIJ)](https://www.uscis.gov/working-in-US/eb4/SIJ) status under INA § 101(a)(27)(J) demands strict verification of multiple interdependent criteria:
- Age requirement: Applicant is under 21 years old.
- Marital status: Applicant is unmarried.
- Judicial declaration: A state juvenile court has declared dependency or placed the applicant under agency/individual custody.
- Family non-reunification determination: State court findings establish that reunification is not viable due to abuse, neglect, abandonment, or a similar legal basis.
- Best interest determination: State court establishes that returning to the home country is not in the applicant's best interest.

### How cases are reviewed today

Currently, legal and advocacy organizations rely on paralegals and legal experts to manually audit case files against checklists. For instance, a paralegal might review age and marital status as straightforward facts from the organization’s database while deriving points 3–5 from court documents and expert annotations. Statutory law rarely applies in a vacuum and often intersects with or conflicts with alternative legal pathways (for example, [U Nonimmigrant Status (U-Visa)](https://www.uscis.gov/humanitarian/victims-of-criminal-activity-u-nonimmigrant-status) under INA § 101(a)(15)(U) vs. INA § 101(a)(27)(J)). This labor-intensive review creates significant operational bottlenecks and limits throughput, especially when legal definitions intersect or require cross-document validation.

## Opportunity and challenge

Deploying an autonomous, agentic document validator directly addresses these limitations by automatically parsing case facts, evaluating eligibility rules, and identifying missing evidence or contradictions before filing. However, the success of autonomous agents depends on conclusions that provably follow the law from the facts in the record, with every fact traceable to its source: a false positive could trigger premature filings leading to deportation proceedings or permanent inadmissibility, whereas a false negative might unjustly deny a vulnerable youth critical legal protection.

## Why this needs neurosymbolic AI

### What rules alone can't do

The statute is a clean conjunction of five conditions, and two of them (age and marital status) are structured fields. The other three live in court orders and expert annotations, written in legal prose that varies by court and judge: "the court finds that reunification with the father is not viable due to abandonment" may appear as a finding, a recital, or an attorney's note. A rules engine can evaluate the statute but can't read the record, so today a paralegal does that reading by hand, and that is the bottleneck.

### What an LLM alone can't do

An LLM can read the record, but asked "is this applicant eligible for SIJ status?", it:

- **can answer from plausibility rather than the law,** for example concluding eligibility from a sympathetic narrative while a required finding, such as best interest, is missing;
- **can blur neighbouring pathways,** mixing SIJ criteria with those of a U-visa;
- **can't reliably do date arithmetic** at the age-21 boundary;
- **can't show a chain of reasoning an attorney can audit:** its explanation is generated after the answer, not the reason for it.

A confident wrong answer causes real harm in both directions: a premature filing, or a denied protection.

### Splitting the work

| Neural: reading the record | Symbolic: applying the law |
|---|---|
| Turn each court finding into a fact | Check age and marital status from structured data |
| Cite the note each fact came from | Apply every condition of the statute by deduction |
| | Report which conditions hold, fail, or lack evidence |

This mirrors how legal reasoning already works: the facts are the minor premise, the statute the major premise, and the conclusion follows by deduction alone.

## Impact

Automating routine case validation speeds up processing, reduces error rates, and offloads repetitive compliance auditing from legal staff, allowing expert paralegals to focus on high-value casework and direct client support.

## Technical approach

See [the technical approach](approach.md) for how an agent with cognition inside meets this challenge.
