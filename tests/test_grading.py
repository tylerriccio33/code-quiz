from code_quiz.agent import extract_answer
from code_quiz.grading import grade, token_f1


def test_token_f1_squad_normalization():
    assert token_f1("The Parser!", "parser") == 1.0


def test_set_partial_and_path_suffix():
    g = grade("src/a.py, b.py, c.py", {"answer": ["a.py", "b.py"], "grader": "set"})
    assert 0.79 < g.score < 0.81


def test_numeric_tolerance():
    assert grade("about 1,000 lines", {"answer": 990, "grader": "numeric", "rel_tol": 0.05}).score == 1


def test_choice_and_keywords():
    assert grade("B", {"answer": "b", "grader": "choice"}).score == 1
    assert grade("uses a copy", {"answer": ["copy", "chmod"], "grader": "keywords"}).score == 0.5


def test_extract_answer():
    assert extract_answer("blah <answer>x</answer> <answer>y</answer>") == "y"


def test_evidence_and_drift():
    from code_quiz.agent import extract_evidence
    from code_quiz.grading import evidence_recall
    from code_quiz.report import doc_only_miss
    ev = extract_evidence("<evidence>src/x/runtime_modify.py, AGENTS.md</evidence>")
    assert evidence_recall(ev, ["runtime_modify.py", "y.py"]) == 0.5
    assert doc_only_miss({"score": 0, "evidence": ["AGENTS.md"]})
    assert not doc_only_miss({"score": 0, "evidence": ["a.py", "AGENTS.md"]})


def test_choice_letter():
    from code_quiz.grading import choice_letter
    assert choice_letter("B") == "B"
    assert choice_letter("b) union") == "B"
    assert choice_letter("I think the answer is C") == "C"


def test_timeout_kills_agent(tmp_path):
    from code_quiz.agent import ask
    r = ask({"question": "q"}, tmp_path, 1, "sleep 30; echo {prompt}")
    assert r.timed_out and r.seconds < 5


def test_tokens_parsed_and_discounted():
    from code_quiz.agent import _parse
    from code_quiz.report import efficiency
    out = '{"result": "x", "num_turns": 3, "total_cost_usd": 0.1, "usage": {"input_tokens": 10,' \
          ' "cache_creation_input_tokens": 100, "cache_read_input_tokens": 1000, "output_tokens": 5}}'
    assert _parse(out) == ("x", 3, 0.1, 1115)
    assert efficiency({"seconds": 0, "tokens": 0}, 100, 1000) == 1.0
    assert efficiency({"seconds": 100, "tokens": 5000}, 100, 1000) == 0.5
