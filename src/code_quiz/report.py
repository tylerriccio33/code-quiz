"""Turn graded runs into a codebase-simplicity report."""
from __future__ import annotations

import statistics as st
from collections import defaultdict

DOC_SUFFIXES = (".md", ".rst", ".txt")


def _mean(xs: list[float]) -> float | None:
    xs = [x for x in xs if x is not None]
    return st.mean(xs) if xs else None


def discounted(r: dict, timeout: float) -> float:
    # Full credit if instant, linearly down to 50% at the limit: rewards answers that are *quick* to find.
    return r["score"] * (1 - 0.5 * min(r["seconds"], timeout) / timeout)


def doc_only_miss(r: dict) -> bool:
    """A wrong answer whose cited evidence is only documentation: a likely doc/code drift signal."""
    ev = r.get("evidence") or []
    return r["score"] < 1 and bool(ev) and all(e.lower().endswith(DOC_SUFFIXES) for e in ev)


def per_question(results: list[dict], pass_threshold: float) -> list[dict]:
    by: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        by[r["id"]].append(r)
    rows = []
    for qid, rs in by.items():
        scores = [r["score"] for r in rs]
        rows.append({
            "id": qid, "question": rs[0]["question"], "expected": rs[0]["expected"], "grader": rs[0]["grader"],
            "tags": rs[0]["tags"], "trials": len(rs), "mean": st.mean(scores),
            "pass_at_k": float(any(s >= pass_threshold for s in scores)),
            "pass_all": float(all(s >= pass_threshold for s in scores)),  # consistency (pass^k, tau-bench)
            "stdev": st.pstdev(scores) if len(scores) > 1 else 0.0,
            "seconds": st.median(r["seconds"] for r in rs),
            "turns": _mean([r.get("turns") for r in rs]),
            "evidence_recall": _mean([r.get("evidence_recall") for r in rs]),
            "answers": [("TIMEOUT" if r["timed_out"] else r["answer"]) for r in rs],
            "doc_drift": any(doc_only_miss(r) for r in rs),
        })
    return rows


def summarize(results: list[dict], timeout: float, pass_threshold: float) -> dict:
    qs = per_question(results, pass_threshold)
    disc = [discounted(r, timeout) for r in results]
    by_tag: dict[str, list[float]] = defaultdict(list)
    for r in results:
        for t in r.get("tags") or ["untagged"]:
            by_tag[t].append(r["score"])
    idx = st.mean(disc) if disc else 0.0
    return {
        "questions": len(qs), "runs": len(results),
        "mean_score": _mean([r["score"] for r in results]) or 0.0,
        "pass_at_k": _mean([q["pass_at_k"] for q in qs]) or 0.0,
        "pass_all_k": _mean([q["pass_all"] for q in qs]) or 0.0,
        "timeouts": sum(r["timed_out"] for r in results),
        "median_seconds": st.median(r["seconds"] for r in results) if results else 0.0,
        "mean_turns": _mean([r.get("turns") for r in results]),
        "total_cost_usd": sum(r.get("cost_usd") or 0 for r in results),
        "evidence_recall": _mean([r.get("evidence_recall") for r in results]),
        "simplicity_index": round(100 * idx, 1),
        "grade": _letter(idx),
        "by_tag": {k: st.mean(v) for k, v in sorted(by_tag.items())},
        "doc_drift_suspects": [q["id"] for q in qs if q["doc_drift"]],
        "per_question": qs,
    }


def _letter(x: float) -> str:
    for cut, g in [(0.85, "A"), (0.7, "B"), (0.55, "C"), (0.4, "D")]:
        if x >= cut:
            return g
    return "F"


def _f(x: float | None, fmt: str = ".2f") -> str:
    return "–" if x is None else format(x, fmt)


def _cell(x: object, n: int) -> str:
    return str(x).replace("|", "\\|").replace("\n", " ")[:n]


def markdown(meta: dict, summary: dict, results: list[dict]) -> str:
    s = summary
    k = meta["trials"]
    out = [
        f"# Code Quiz report: `{meta['codebase']}`", "",
        f"Agent: `{meta['agent']}` | {meta['timeout']}s/question | {k} trial(s) | pass threshold {meta['pass_threshold']}", "",
        f"## Simplicity index: **{s['simplicity_index']} / 100** (grade {s['grade']})", "",
        f"**Effort:** {_f(s['mean_turns'], '.1f')} agent turns and {s['median_seconds']:.0f}s median per question. "
        "When correctness saturates, compare codebases on effort.", "",
        "| metric | value |", "|---|---|",
        f"| questions / runs | {s['questions']} / {s['runs']} |",
        f"| mean correctness | {s['mean_score']:.2f} |",
        f"| pass@{k} (any trial passes) | {s['pass_at_k']:.0%} |",
        f"| pass^{k} (every trial passes) | {s['pass_all_k']:.0%} |",
        f"| evidence recall (cited the right files) | {_f(s['evidence_recall'])} |",
        f"| median time | {s['median_seconds']:.1f}s |",
        f"| mean agent turns | {_f(s['mean_turns'], '.1f')} |",
        f"| timeouts | {s['timeouts']} |",
        f"| cost | ${s['total_cost_usd']:.2f} |", "",
        "Index = mean correctness discounted by time used (full credit at 0s, half at the limit).", "",
        "## By tag", "", "| tag | mean score |", "|---|---|",
        *[f"| {t} | {v:.2f} |" for t, v in s["by_tag"].items()], "",
        "## Questions", "",
        "| id | grader | mean | pass^k | time | turns | evidence | answer(s) | expected |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for q in s["per_question"]:
        out.append(f"| {q['id']}{' ⚠' if q['doc_drift'] else ''} | {q['grader']} | {q['mean']:.2f} | {q['pass_all']:.0f} | "
                   f"{q['seconds']:.0f}s | {_f(q['turns'], '.0f')} | {_f(q['evidence_recall'])} | "
                   f"{_cell(' / '.join(q['answers']), 90)} | {_cell(q['expected'], 60)} |")
    if s["doc_drift_suspects"]:
        out += ["", "## ⚠ Possible doc/code drift", "",
                "Wrong answers whose only cited evidence was documentation. Check whether the docs are stale "
                "(or the answer key is):", ""]
        out += [f"- **{q}**" for q in s["doc_drift_suspects"]]
    hard = sorted(s["per_question"], key=lambda q: (q["mean"], -q["seconds"]))[:3]
    out += ["", "## Hardest questions", ""]
    out += [f"- **{q['id']}** ({q['mean']:.2f}, {q['seconds']:.0f}s): {q['question']}" for q in hard]
    return "\n".join(out) + "\n"
