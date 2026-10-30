# Legal Case Validator

[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](https://www.python.org/downloads/)
[![cognition](https://img.shields.io/badge/cognition-inside-7b2fbe?labelColor=f3effa&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjIgMCAzNiAzNiIgZmlsbD0ibm9uZSI+PHBvbHlnb24gcG9pbnRzPSIyMCw0IDM0LjMsMTQuNCAyOC44LDMxLjYgMTEuMiwzMS42IDUuNywxNC40IiBzdHJva2U9IiM3YjJmYmUiIHN0cm9rZS13aWR0aD0iMi4yIi8+PGcgc3Ryb2tlPSIjYzQ3ZDIwIiBzdHJva2Utd2lkdGg9IjIiPjxsaW5lIHgxPSIyMCIgeTE9IjIwIiB4Mj0iMjAiIHkyPSI0Ii8+PGxpbmUgeDE9IjIwIiB5MT0iMjAiIHgyPSIzNC4zIiB5Mj0iMTQuNCIvPjxsaW5lIHgxPSIyMCIgeTE9IjIwIiB4Mj0iMjguOCIgeTI9IjMxLjYiLz48bGluZSB4MT0iMjAiIHkxPSIyMCIgeDI9IjExLjIiIHkyPSIzMS42Ii8+PGxpbmUgeDE9IjIwIiB5MT0iMjAiIHgyPSI1LjciIHkyPSIxNC40Ii8+PC9nPjxnIGZpbGw9IiM3YjJmYmUiPjxjaXJjbGUgY3g9IjIwIiBjeT0iNCIgcj0iMy4yIi8+PGNpcmNsZSBjeD0iMzQuMyIgY3k9IjE0LjQiIHI9IjMuMiIvPjxjaXJjbGUgY3g9IjI4LjgiIGN5PSIzMS42IiByPSIzLjIiLz48Y2lyY2xlIGN4PSIxMS4yIiBjeT0iMzEuNiIgcj0iMy4yIi8+PGNpcmNsZSBjeD0iNS43IiBjeT0iMTQuNCIgcj0iMy4yIi8+PC9nPjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjQuNiIgZmlsbD0iI2M0N2QyMCIvPjwvc3ZnPgo=)](https://github.com/polycog/cognition)
[![cognition on PyPI](https://img.shields.io/pypi/v/polycog-cognition?label=cognition%20on%20PyPI&color=c47d20&labelColor=f3effa&logo=data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjIgMCAzNiAzNiIgZmlsbD0ibm9uZSI+PHBvbHlnb24gcG9pbnRzPSIyMCw0IDM0LjMsMTQuNCAyOC44LDMxLjYgMTEuMiwzMS42IDUuNywxNC40IiBzdHJva2U9IiM3YjJmYmUiIHN0cm9rZS13aWR0aD0iMi4yIi8+PGcgc3Ryb2tlPSIjYzQ3ZDIwIiBzdHJva2Utd2lkdGg9IjIiPjxsaW5lIHgxPSIyMCIgeTE9IjIwIiB4Mj0iMjAiIHkyPSI0Ii8+PGxpbmUgeDE9IjIwIiB5MT0iMjAiIHgyPSIzNC4zIiB5Mj0iMTQuNCIvPjxsaW5lIHgxPSIyMCIgeTE9IjIwIiB4Mj0iMjguOCIgeTI9IjMxLjYiLz48bGluZSB4MT0iMjAiIHkxPSIyMCIgeDI9IjExLjIiIHkyPSIzMS42Ii8+PGxpbmUgeDE9IjIwIiB5MT0iMjAiIHgyPSI1LjciIHkyPSIxNC40Ii8+PC9nPjxnIGZpbGw9IiM3YjJmYmUiPjxjaXJjbGUgY3g9IjIwIiBjeT0iNCIgcj0iMy4yIi8+PGNpcmNsZSBjeD0iMzQuMyIgY3k9IjE0LjQiIHI9IjMuMiIvPjxjaXJjbGUgY3g9IjI4LjgiIGN5PSIzMS42IiByPSIzLjIiLz48Y2lyY2xlIGN4PSIxMS4yIiBjeT0iMzEuNiIgcj0iMy4yIi8+PGNpcmNsZSBjeD0iNS43IiBjeT0iMTQuNCIgcj0iMy4yIi8+PC9nPjxjaXJjbGUgY3g9IjIwIiBjeT0iMjAiIHI9IjQuNiIgZmlsbD0iI2M0N2QyMCIvPjwvc3ZnPgo=)](https://pypi.org/project/polycog-cognition/)

## 1. Summary

A **neurosymbolic** document validator built with the [`cognition`](https://github.com/polycog/cognition) library. The validator reads the case facts and court notes of an immigration case and decides whether the applicant qualifies for a specific status under the law.

### Contents

1. [Summary](#1-summary)
2. [Problem Statement](#2-problem-statement)
3. [Technical Approach and Demo](#3-technical-approach-and-demo)
4. [Install, Run, and Test](#4-install-run-and-test)
5. [License and Disclaimers](#5-license-and-disclaimers)

---

## 2. Problem Statement

Legal immigration and advocacy organizations decide eligibility for immigration relief, such as SIJ status, by having paralegals manually audit case files against statutory checklists, a slow process that limits how many cases they can handle. LLMs can read the court orders and notes where the facts live, but they can't be trusted to apply the law exactly or to show their reasoning. Both errors are costly: a false positive can trigger a premature filing and deportation proceedings, and a false negative can deny a vulnerable youth legal protection. A **neurosymbolic** approach combines both: the LLM reads the record, and symbolic reasoning applies the law by deduction, so every conclusion follows from the facts and can be audited.

See [the full problem statement and opportunity](docs/usecase.md).

---

## 3. Technical Approach and Demo

Like an expert paralegal, the validator applies the law to the case facts, and concludes the applicant is eligible only if every legal condition holds. An LLM reads the court's notes and turns each finding into a fact, citing the note it came from. The legal rules, written as WHEN/THEN operators in a **[symbolic decision process](https://docs.polycog.ai/ideas/kadp.html)** built with `cognition`, then apply to those facts by deduction alone, so the conclusion is deterministic and every step can be audited. See [the technical approach](docs/approach.md) for details.

**Demo:** [watch the validator run on an applicant's case](https://drive.google.com/file/d/14jnK5VI7ICHNg4FS9kUgCo29eMzOwxG5/view?usp=sharing)

---

## 4. Install, Run, and Test

### 4.1 Clone the repository

```bash
git clone https://github.com/polycog/demo-legal-tech.git
cd demo-legal-tech
```

### 4.2 Create a Python environment

`cognition` requires **Python 3.13 or later**.

```bash
# with venv
python3.13 -m venv .venv
source .venv/bin/activate

# or with conda
conda create -n sij-validator python=3.13
conda activate sij-validator
```

### 4.3 Install the dependencies

```bash
pip install -r requirements.txt
```

This installs:

- **`polycog-cognition`**, the `cognition` library, published on PyPI under that name;
- **`pydantic-ai-slim[openai]`** (2.9.x), which `cognition` builds on, with the OpenAI extra that the note classifier needs to run on `openai:gpt-4o`;
- **`pytest`**, for running the test suite.

Check the install:

```bash
python -c "import cognition, pydantic_ai, openai; print('ok')"
```

### 4.4 Set your OpenAI API key

Create a key at <https://platform.openai.com/api-keys>, then export it in the shell you run the validator from:

```bash
export OPENAI_API_KEY="sk-..."
```

To keep it across sessions, add that line to your shell profile (`~/.zshrc` on macOS, `~/.bashrc` on most Linux systems) and open a new terminal. Check it is set with:

```bash
echo ${OPENAI_API_KEY:+set}
```

Keep the key out of the repository: don't write it into `validator.py` or `case-facts.json`.

### 4.5 Run the validator

```bash
python validator.py
```

### 4.6 Run the tests

The test suite uses [pytest](https://docs.pytest.org/), installed with the other requirements, and runs fully offline: it replaces the LLM note classifier with a deterministic keyword-based fake, so it needs no API key and makes no paid calls.

```bash
python -m pytest tests
```

---

## 5. License and Disclaimers

This project is released under the [Apache License 2.0](LICENSE). Copyright © 2026 Polycog, Inc. If you use it, please cite it using the metadata in [`CITATION.cff`](CITATION.cff).

> **Disclaimer:** this project is a technical demonstration of neurosymbolic reasoning. It is not legal advice, has not been reviewed for use in real cases, and is no substitute for a qualified immigration attorney. The case in `case-facts.json` is fictional.
