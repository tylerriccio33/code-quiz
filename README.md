# code-quiz

How easy is a codebase for an agent to work with? Give it a quiz: questions + gold answers.
An agent answers each one with **read-only** access under a **time limit**. Every response is
graded **deterministically** (no LLM judge), and you get a simplicity report.

```bash
uv run code-quiz run examples/self.yaml --model haiku --trials 3 --out quiz-out   # model: haiku (default) | sonnet | opus
uv run code-quiz grade examples/self.yaml graders "<answer>exact, set</answer>"   # test a grader spec
```

## Choosing the agent
Think of the agent as a **junior dev** being handed the repo. The default is `--model haiku`; `sonnet` is a
reasonable second opinion. A strong model like Opus answers almost anything given enough turns, which hides the
difference between a clear codebase and a confusing one. A quiz file can pin a model with `model: sonnet`, and
`--model` overrides it. For a non-Claude agent, use `--agent-cmd 'my-agent --model {model} {prompt}'`.

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
takes off up to 25%. Tokens used, up to `--token-budget` (default 150k), takes off up to 25%. So a correct
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

## Writing a quiz

A good quiz asks what a new teammate would actually ask in their first weeks. Its answers must be **checkable
without judgment**: a number, a name, a file, a set of files, or a multiple-choice letter. Three question types
carry most of the signal. Lookup questions ("where is X") saturate on every codebase, because grep answers them.

**1. How do I add X?** Tests whether extension points are obvious.
```yaml
- id: howto_binop
  question: I want to add a binary operator to the parser. Which two functions hold precedence tables that must agree?
  answer: [binop, fold_prec]
  grader: keywords
  evidence: [crates/parser/src/shared.rs, crates/parser/src/expr.rs]
```
Grade with `set` ("which files must change"), scored by F1 against the files a real change touched. Use
`keywords` for "which functions/tables". Mine these from real commits: `git show --stat <a feature commit>`
gives you the true file set.

**2. Does this rule fire?** Tests whether behavior can be predicted from reading the code.
```yaml
- id: rule_rowlocal_symput
  question: >-
    In a step that also does `call symput('rate', ...)`, is `y = x * &rate;` row-local?
    A) yes  B) no, it reads a macro var in a step that rebinds macro vars  C) ...  D) ...
  answer: B
  grader: choice
```
Prefer concrete inputs: "what total does this order produce" (`numeric`), "which rules apply to this input"
(`set`). Make the wrong options plausible, e.g. what the docs say, or what a similar-looking function does.
**Verify every answer by running the code**, never from memory or docs (see `fixtures/check_equivalence.py`).

**3. My X fails like this. Where is it coming from?** Tests whether failures can be traced back to their source.
```yaml
- id: debug_hash_method
  question: >-
    Compiling `declare hash h(); rc = h.frobnicate();` fails with "LoweringError: h.frobnicate(): no such
    method on a hash object". Which file raises it, and which file holds the method list it checks?
  answer: [row_loop.py, objects.py]
  grader: keywords
```
Paste the **real error text** a user would see. Reproduce it first, then grep for where it's raised. Avoid
errors raised from many places (e.g. one exception class used in 8 files), because there's no single right answer.

**Principles**
- **One fact per question.** If you can't write the answer key in under 10 words, split the question.
- **Prefer behavior over location.** "What does it do" separates codebases; "where is it" doesn't.
- **Phrase the answer format the way the grader parses it.** Ask for "file names" when grading with `keywords`, a
  letter when grading with `choice`, and a list when grading with `set`.
- **Avoid unique strings in the question.** If the question contains `FRAME_FUNCS`, grep finds the answer in one
  turn. Describe the concept instead: "the set of functions opt can translate to polars".
- **Always give `evidence:`.** Evidence recall shows whether the agent found the answer or guessed it.
- **Expect drift.** When the agent is wrong and cites only docs, check the docs before blaming the agent
  (marked ⚠ in the report).
- **Tag questions** (`easy`/`medium`/`hard`, `howto`/`rule`/`debug`). The per-tag table shows *which kind* of
  understanding the codebase makes hard.
- **Answer keys go stale.** Code moves under a live repo. When a codebase changes, re-check the keys, or quiz a
  pinned commit. (Haiku "failed" a sas-ir question by correctly finding a function that had just moved to a new
  file.)
- **Verify the key, then run the quiz with `--trials 2+`.** If pass^k < pass@k, the agent is unreliable on that
  question, which is a signal in itself.

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

With the default **Haiku** agent and a 150k token budget (1 trial):

| codebase | index | correct | mean turns | median tokens |
|---|---|---|---|---|
| `fixtures/clean` | 87.2 | 100% | 4.1 | 65k |
| `fixtures/tangled` | 80.0 | 100% | 9.4 | 89k |
| sas-ir (21 q, incl. how-to / rule / debug) | 77.3* | 95%* | 2.5 | 93k |

\* The one sas-ir miss was a stale answer key (the function had moved), since fixed. sas-ir's token count is
high even at 2.5 turns because its AGENTS.md alone is about 25k tokens. Haiku costs about $0.05–0.17 per run, versus
about $2–9 on Opus.

**Lessons:**
1. Lookup questions ("where is X", "list X") saturate: grep answers them in about 2 turns on any codebase.
2. Behavioral questions ("what does this input produce") are the ones that separate codebases.
3. With a strong agent, effort (turns, time, cost) discriminates before correctness does. Use tighter budgets or a weaker model to push the gap into correctness.

```bash
scripts/fetch_corpora.sh                 # clone polars/numpy at the verified commits
uv run python fixtures/check_equivalence.py
uv run code-quiz run examples/tangled.yaml --trials 2
```
