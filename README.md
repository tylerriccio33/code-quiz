# code-quiz

How easy is a codebase for an agent to work with? Give it a quiz: questions + gold answers.
An agent answers each one with **read-only** access under a **time limit**. Every response is
graded **deterministically** (no LLM judge), and you get a simplicity report.

```bash
uv run code-quiz run examples/self.yaml --timeout 120 --trials 3 --out quiz-out
uv run code-quiz grade examples/self.yaml graders "<answer>exact, set</answer>"   # test a grader spec
```

## Quiz format (YAML)
```yaml
codebase: ../my-repo      # relative to this file, or pass --codebase
timeout: 90               # seconds per question (per-question `timeout:` overrides it)
questions:
  - id: where_auth
    question: Which files implement token refresh?
    answer: [auth/refresh.py, auth/session.py]
    grader: set
    tags: [navigation]
```

| grader | answer | scoring | basis |
|---|---|---|---|
| `exact` | str or list of accepted strings | 1/0 after normalization | SQuAD EM |
| `contains` | str/list | 1 if a gold string appears | lenient EM |
| `token_f1` (default) | str/list | token-overlap F1 | SQuAD F1 |
| `set` | list | item P/R F1, path-suffix tolerant | retrieval / SWE-bench localization |
| `numeric` | number (+`rel_tol`, `abs_tol`) | 1/0 within tolerance | DROP |
| `choice` | letter | 1/0 | MMLU-style MCQ |
| `regex` | pattern | 1/0 | |
| `keywords` | list | fraction of rubric keywords present | checklist rubrics |

Write questions so their answers *can* be checked deterministically: prefer identifiers, paths,
numbers, lists and multiple choice over free prose. The agent must end with `<answer>…</answer>`.
Format hints are added to the prompt according to the grader.

## How the agent is run
For each question (and trial), `agent.ask()` starts the agent as a separate process inside the read-only snapshot:
`claude -p '<prompt>' --output-format json` by default, or your own command via `--agent-cmd '... {prompt}'`.
The prompt tells the agent three things:
- it is scored on correctness first, then on speed and token usage, with the time limit stated;
- it must end with `<evidence>` and `<answer>` tags;
- the expected answer format.

The process runs in its own process group, and the whole group is killed at the time limit (score 0).
From `claude`'s JSON envelope we record the answer text, **wall-clock seconds**, **turns**, **tokens**
(input + cache writes + cache reads + output) and **$ cost**. A custom agent that prints plain text gets
time only.

**Index** = mean over runs of correctness × efficiency. Efficiency starts at 1.0. Time used, up to the limit,
takes off up to 25%. Tokens used, up to `--token-budget` (default 500k), takes off up to 25%. So a correct
answer that maxes out both scores 0.5.

## Read-only enforcement
1. The codebase is copied to a temp snapshot (minus .git/.venv/node_modules/target) with write bits removed.
2. The default agent (`claude -p`) gets only `Read,Grep,Glob,LS`. Bash, Edit, Write and Web are disallowed.

To use another agent, pass `--agent-cmd 'my-agent --prompt {prompt}'`. It runs in the snapshot directory
and its stdout is graded.

## Report
`quiz-out/report.md` and `results.json` (with raw transcripts). The **simplicity index** (0–100) is
mean correctness discounted linearly by time used: full credit at 0s, half credit at the limit.
Timeouts score 0. Run `--trials N` to average out agent variance.

## Evidence, trials and drift
- The agent must also cite `<evidence>files</evidence>`. A question's `evidence:` list scores **evidence recall**.
- `--trials N` reports **pass@k** (any trial passes) and **pass^k** (all trials pass; τ-bench-style consistency).
- **Effort** is the agent's mean turns (from `claude --output-format json`), plus time and $ cost.
- ⚠ **doc-drift suspects** are wrong answers whose only cited evidence is `.md/.rst/.txt`.
  This caught real drift in sas-ir's AGENTS.md: the file named for the MODIFY table, and the macro type list.

## Results so far (claude, 2 trials)

| codebase | index | correct | mean turns | median time | evidence recall |
|---|---|---|---|---|---|
| `fixtures/clean` | 95.2 | 100% | **3.9** | 8s | 0.96 |
| `fixtures/tangled` (same behavior) | 90.2 | 100% | **10.2** | 15s | 0.76 |
| sas-ir (17 q) | 98.6 | 100% | 2.1 | 6s | 0.85 |
| polars (12 q) | 98.7 | 100% | 2.2 | 6s | 0.83 |
| numpy (12 q) | 98.7 | 100% | 2.1 | 6s | 0.92 |

`fixtures/clean` and `fixtures/tangled` are a controlled pair: identical behavior (`fixtures/check_equivalence.py`)
and one shared behavioral quiz. Tangled packs in real-world anti-patterns: import-time registries,
an `__init__` monkeypatch, layered config with a buried override, value-altering decorators, a stale README,
dead twins of live functions, and misleading names. A strong agent still gets everything right.
It needs **2.6× the turns**, though, and 22–28 turns on multi-step pricing questions against 8 on the clean code.

Rerun after telling the agent that time and tokens count (1 trial each):
- **clean:** 93.9, 100% correct, 4.1 turns, 64k tokens/question.
- **tangled:** 84.7, **93% correct**, 7.7 turns, 88k tokens/question.

Under pressure to be quick, the agent missed a tax total on the tangled code: 846 instead of 841. It read
`settings/defaults.py` but never found the override layered in `settings.json` and the `_compat.py` monkeypatch.

**Lessons:**
1. Lookup questions ("where is X", "list X") saturate: grep answers them in about 2 turns on any codebase.
2. Behavioral questions ("what does this input produce") are the ones that separate codebases.
3. With a strong agent, effort (turns, time, cost) discriminates before correctness does. Use tighter budgets or a weaker model to push the gap into correctness.

```bash
scripts/fetch_corpora.sh                 # clone polars/numpy at the verified commits
uv run python fixtures/check_equivalence.py
uv run code-quiz run examples/tangled.yaml --trials 2
```
