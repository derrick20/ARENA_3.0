#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/venv/arena-env/bin/python}"
SCENARIO_ID="${1:-parent_son_school_conflict}"
RESULTS_PATH="${RESULTS_PATH:-$ROOT_DIR/improv_results.jsonl}"
HTML_PATH="${HTML_PATH:-$ROOT_DIR/improv_transcripts.html}"

echo "Running real A/B scenario: ${SCENARIO_ID}"
"$PYTHON_BIN" "$ROOT_DIR/improv_therapy_mvp.py" \
  --scenario-id "$SCENARIO_ID" \
  --out "$RESULTS_PATH"

echo "Rendering transcript viewer: ${HTML_PATH}"
"$PYTHON_BIN" "$ROOT_DIR/render_transcripts.py" \
  --in "$RESULTS_PATH" \
  --out "$HTML_PATH"

echo "Done."
echo "Results: ${RESULTS_PATH}"
echo "Viewer:  ${HTML_PATH}"
