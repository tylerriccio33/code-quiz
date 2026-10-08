"""Deterministic graders. No LLM judge: every score is a pure function of (response, spec).

Metrics follow established QA-eval practice:
- exact / token_f1: SQuAD normalization (Rajpurkar et al., 2016) -- lowercase, strip
  punctuation and articles, collapse whitespace; F1 over bag of tokens.
- set: precision/recall/F1 over a set of items (files, symbols), as in retrieval eval
  and code-localization benchmarks (e.g. SWE-bench file-level localization).
- numeric: absolute/relative tolerance match (as in DROP, Dua et al., 2019).
- regex / keywords: rubric-style checklist items (all-or-fraction), deterministic.
- choice: multiple choice, the most robust deterministic format (MMLU-style).
"""
from __future__ import annotations

import re
import string
from collections import Counter
from dataclasses import dataclass

ARTICLES = re.compile(r"\b(a|an|the)\b", re.I)


def normalize(s: str, articles: bool = True) -> str:
    s = s.lower()
    s = "".join(ch for ch in s if ch not in set(string.punctuation) - {"_", ".", "/"})
    if articles:
        s = ARTICLES.sub(" ", s)
    return " ".join(s.split())


def token_f1(pred: str, gold: str) -> float:
    p, g = normalize(pred).split(), normalize(gold).split()
    common = Counter(p) & Counter(g)
    same = sum(common.values())
    if not p or not g:
        return float(p == g)
    if same == 0:
        return 0.0
    prec, rec = same / len(p), same / len(g)
    return 2 * prec * rec / (prec + rec)


def _items(s: str) -> set[str]:
    parts = re.split(r"[,\n;]+|\s+and\s+", s)
    items = (normalize(x, articles=False).strip("` ") for x in parts)
    return {x for x in items if x}


def _item_eq(a: str, b: str) -> bool:
    # a path answer may be given relative or with a prefix: match on suffix
    return a == b or a.endswith("/" + b) or b.endswith("/" + a)


def set_f1(pred: str, gold: list[str]) -> float:
    p, g = _items(pred), {normalize(x, articles=False) for x in gold}
    if not p or not g:
        return 0.0
    tp_p = sum(any(_item_eq(x, y) for y in g) for x in p)
    tp_g = sum(any(_item_eq(x, y) for y in p) for x in g)
    prec, rec = tp_p / len(p), tp_g / len(g)
    return 0.0 if prec + rec == 0 else 2 * prec * rec / (prec + rec)


def numeric(pred: str, gold: float, rel_tol: float, abs_tol: float) -> float:
    m = re.search(r"-?\d[\d,]*\.?\d*(?:e-?\d+)?", pred)
    if not m:
        return 0.0
    v = float(m.group().replace(",", ""))
    return float(abs(v - gold) <= max(abs_tol, rel_tol * abs(gold)))


def choice_letter(response: str) -> str | None:
    """The chosen option: a bare letter, a leading `B)`/`(B)`, else the last standalone A-H."""
    r = response.strip()
    m = re.match(r"^\(?([A-Ha-h])\)?(?:[.):\s]|$)", r)
    if m:
        return m.group(1).upper()
    found = re.findall(r"\b([A-H])\b", r)
    return found[-1] if found else None


@dataclass
class Grade:
    score: float  # 0..1
    method: str
    detail: str = ""


def grade(response: str, q: dict) -> Grade:
    """q has `answer` and optional `grader` (default: token_f1) plus grader options."""
    kind = q.get("grader", "token_f1")
    gold = q["answer"]
    if kind == "exact":
        golds = gold if isinstance(gold, list) else [gold]
        ok = any(normalize(response) == normalize(str(g)) for g in golds)
        return Grade(float(ok), kind)
    if kind == "contains":  # gold string(s) appear in the normalized answer
        golds = gold if isinstance(gold, list) else [gold]
        ok = any(normalize(str(g)) in normalize(response) for g in golds)
        return Grade(float(ok), kind)
    if kind == "token_f1":
        golds = gold if isinstance(gold, list) else [gold]
        return Grade(max(token_f1(response, str(g)) for g in golds), kind)
    if kind == "set":
        return Grade(set_f1(response, list(gold)), kind)
    if kind == "numeric":
        return Grade(numeric(response, float(gold), q.get("rel_tol", 0.0), q.get("abs_tol", 0.0)), kind)
    if kind == "choice":
        return Grade(float(choice_letter(response) == str(gold).upper()), kind)
    if kind == "regex":
        return Grade(float(re.search(gold, response, re.I | re.S) is not None), kind)
    if kind == "keywords":  # rubric checklist: fraction of required keywords present
        r = normalize(response)
        hits = [k for k in gold if normalize(k) in r]
        miss = [k for k in gold if k not in hits]
        return Grade(len(hits) / len(gold), kind, f"missing: {miss}" if miss else "")
    raise ValueError(f"unknown grader {kind!r}")


def evidence_recall(cited: list[str], gold: list[str]) -> float | None:
    """Fraction of gold evidence files the agent cited (path-suffix tolerant). None if no gold."""
    if not gold:
        return None
    c = [normalize(x, articles=False) for x in cited]
    g = [normalize(x, articles=False) for x in gold]
    return sum(any(_item_eq(x, y) for x in c) for y in g) / len(g)
