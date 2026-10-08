"""Run an agent on one question with read-only access and a wall-clock limit."""
from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import signal
import stat
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path

PROMPT = """You are taking a timed quiz about the codebase in the current directory.
You have READ-ONLY access. Do not attempt to modify anything.
Answer the question as concisely as possible.
{format_hint}
End your reply with the files you based the answer on and the final answer, exactly like:
<evidence>path/one.py, path/two.rs</evidence>
<answer>YOUR ANSWER</answer>

Question: {question}"""

FORMAT_HINTS = {
    "set": "The answer is a list: give items comma-separated (e.g. file paths or symbol names).",
    "numeric": "The answer is a single number.",
    "choice": "Answer with the single letter of the correct option.",
    "exact": "Answer with just the identifier/value, no explanation inside the tags.",
}

# claude CLI: only read tools, no Bash/Edit/Write/Web.
CLAUDE_CMD = (
    "claude -p {prompt} --output-format json "
    "--allowedTools Read,Grep,Glob,LS "
    "--disallowedTools Bash,Edit,Write,MultiEdit,NotebookEdit,WebFetch,WebSearch"
)


@dataclass
class Run:
    raw: str
    answer: str
    seconds: float
    timed_out: bool
    error: str = ""
    evidence: list[str] | None = None
    turns: int | None = None
    cost_usd: float | None = None


def extract_answer(text: str) -> str:
    m = re.findall(r"<answer>(.*?)</answer>", text, re.S | re.I)
    if m:
        return m[-1].strip()
    lines = [ln for ln in text.strip().splitlines() if ln.strip()]
    return lines[-1].strip() if lines else ""  # fallback: last line


DEFAULT_IGNORE = [".git", "node_modules", ".venv", "target", "__pycache__", "*.so", ".claude", ".fuzz", ".hypothesis"]


def extract_evidence(text: str) -> list[str]:
    m = re.findall(r"<evidence>(.*?)</evidence>", text, re.S | re.I)
    if not m:
        return []
    return [x.strip(" `") for x in re.split(r"[,\n]+", m[-1]) if x.strip(" `")]


def _parse(stdout: str) -> tuple[str, int | None, float | None]:
    """Accept either plain text or the claude CLI's --output-format json envelope."""
    try:
        d = json.loads(stdout)
        return d.get("result", ""), d.get("num_turns"), d.get("total_cost_usd")
    except (json.JSONDecodeError, AttributeError):
        return stdout, None, None


def readonly_snapshot(src: Path, ignore: list[str] = DEFAULT_IGNORE) -> Path:
    """Copy the codebase to a temp dir and strip write bits (defense in depth beside tool limits)."""
    dst = Path(tempfile.mkdtemp(prefix="code-quiz-")) / src.name
    shutil.copytree(src, dst, symlinks=True, ignore=shutil.ignore_patterns(*ignore))
    for root, dirs, files in os.walk(dst):
        for n in files + dirs:
            p = Path(root, n)
            if not p.is_symlink():
                p.chmod(p.stat().st_mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
    return dst


def make_writable(path: Path) -> None:
    for root, dirs, files in os.walk(path):
        for n in [*dirs, *files]:
            p = Path(root, n)
            if not p.is_symlink():
                p.chmod(p.stat().st_mode | stat.S_IWUSR)
    Path(path).chmod(Path(path).stat().st_mode | stat.S_IWUSR)


def ask(question: dict, cwd: Path, timeout: float, cmd_template: str = CLAUDE_CMD) -> Run:
    prompt = PROMPT.format(
        question=question["question"],
        format_hint=FORMAT_HINTS.get(question.get("grader", ""), ""),
    )
    cmd = cmd_template.format(prompt=shlex.quote(prompt))
    t0 = time.monotonic()
    # own process group so a timeout kills the agent too, not just the shell
    p = subprocess.Popen(cmd, shell=True, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                         stdin=subprocess.DEVNULL, start_new_session=True)
    try:
        stdout, stderr = p.communicate(timeout=timeout)
        dt = time.monotonic() - t0
        text, turns, cost = _parse(stdout)
        return Run(text, extract_answer(text), dt, False, stderr.strip()[-500:] if p.returncode else "",
                   extract_evidence(text), turns, cost)
    except subprocess.TimeoutExpired:
        os.killpg(p.pid, signal.SIGKILL)
        out, _ = p.communicate()
        return Run(out or "", "", time.monotonic() - t0, True)
