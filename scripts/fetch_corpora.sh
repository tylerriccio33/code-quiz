#!/usr/bin/env bash
# Clone the external codebases the example quizzes point at, at the commits their answers were verified against.
set -euo pipefail
cd "$(dirname "$0")/.." && mkdir -p corpora && cd corpora
fetch() { [ -d "$1" ] || { git clone -q https://github.com/$2.git "$1" && git -C "$1" checkout -q "$3"; }; }
fetch polars pola-rs/polars 3f2ccbd
fetch numpy numpy/numpy 474f0d6
