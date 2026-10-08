"""code-quiz: how well can an agent answer questions about a codebase, read-only, under a time limit?"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import yaml

from . import agent, grading, report


def load_quiz(path: Path) -> dict:
    data = yaml.safe_load(path.read_text())
    for i, q in enumerate(data["questions"]):
        q.setdefault("id", f"q{i + 1}")
        if "question" not in q or "answer" not in q:
            sys.exit(f"question {q['id']} needs `question` and `answer`")
    return data


def run(args: argparse.Namespace) -> None:
    quiz = load_quiz(Path(args.quiz))
    if args.codebase:
        codebase = Path(args.codebase).expanduser().resolve()
    else:  # relative to the quiz file
        codebase = (Path(args.quiz).parent / quiz.get("codebase", ".")).expanduser().resolve()
    timeout = args.timeout or quiz.get("timeout", 120)
    cmd = args.agent_cmd or agent.CLAUDE_CMD
    snap = agent.readonly_snapshot(codebase, agent.DEFAULT_IGNORE + quiz.get("ignore", []))
    print(f"read-only snapshot: {snap}", file=sys.stderr)

    jobs = [(q, t) for q in quiz["questions"] for t in range(args.trials)]

    def one(job: tuple[dict, int]) -> dict:
        q, t = job
        r = agent.ask(q, snap, q.get("timeout", timeout), cmd)
        g = grading.grade(r.answer, q) if not r.timed_out else grading.Grade(0.0, q.get("grader", "token_f1"), "timeout")
        print(f"  {q['id']}#{t}: {g.score:.2f} in {r.seconds:.0f}s{' TIMEOUT' if r.timed_out else ''}", file=sys.stderr)
        return {"id": q["id"], "trial": t, "question": q["question"], "expected": q["answer"],
                "grader": g.method, "score": g.score, "detail": g.detail, "answer": r.answer,
                "seconds": round(r.seconds, 2), "timed_out": r.timed_out, "error": r.error,
                "tags": q.get("tags", []), "raw": r.raw,
                "evidence": r.evidence, "gold_evidence": q.get("evidence", []),
                "evidence_recall": grading.evidence_recall(r.evidence or [], q.get("evidence", [])),
                "turns": r.turns, "cost_usd": r.cost_usd, "tokens": r.tokens}

    try:
        with ThreadPoolExecutor(args.jobs) as ex:
            results = list(ex.map(one, jobs))
    finally:
        agent.make_writable(snap.parent)
        shutil.rmtree(snap.parent, ignore_errors=True)

    meta = {"codebase": str(codebase), "agent": cmd.split()[0], "quiz": str(args.quiz), "timeout": timeout,
            "trials": args.trials, "pass_threshold": args.pass_threshold, "token_budget": args.token_budget}
    summary = report.summarize(results, timeout, args.pass_threshold, args.token_budget)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps({"meta": meta, "summary": summary, "results": results}, indent=2))
    (out / "report.md").write_text(report.markdown(meta, summary, results))
    print(report.markdown(meta, summary, results))
    print(f"wrote {out}/report.md and results.json", file=sys.stderr)


def grade_only(args: argparse.Namespace) -> None:
    """Grade a single response against a question -- handy for testing grader specs."""
    quiz = load_quiz(Path(args.quiz))
    q = next(q for q in quiz["questions"] if q["id"] == args.id)
    g = grading.grade(agent.extract_answer(args.response), q)
    print(json.dumps(g.__dict__))


def main() -> None:
    p = argparse.ArgumentParser(prog="code-quiz", description=__doc__)
    sub = p.add_subparsers(required=True)
    r = sub.add_parser("run", help="quiz an agent on a codebase")
    r.add_argument("quiz")
    r.add_argument("--codebase", help="overrides `codebase:` in the quiz file")
    r.add_argument("--timeout", type=float, help="seconds per question (default: quiz's, else 120)")
    r.add_argument("--trials", type=int, default=1, help="runs per question (variance / pass@k)")
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--pass-threshold", type=float, default=0.8)
    r.add_argument("--token-budget", type=int, default=500_000,
                   help="tokens per question at which the token discount bottoms out (default 500k)")
    r.add_argument("--agent-cmd", help="shell template with {prompt}; runs in the read-only snapshot")
    r.add_argument("--out", default="quiz-out")
    r.set_defaults(fn=run)
    g = sub.add_parser("grade", help="grade one response string against a question")
    g.add_argument("quiz")
    g.add_argument("id")
    g.add_argument("response")
    g.set_defaults(fn=grade_only)
    a = p.parse_args()
    a.fn(a)
