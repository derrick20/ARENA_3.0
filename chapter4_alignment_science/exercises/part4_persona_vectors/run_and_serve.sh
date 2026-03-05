#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCENARIO_ID="${1:-therapist_patient_adlerian_vs_mi}"
PORT="${PORT:-8000}"

"$ROOT_DIR/run_improv_pipeline.sh" "$SCENARIO_ID"

echo ""
echo "Serving viewer on http://localhost:${PORT}/improv_transcripts.html"
echo "Press Ctrl+C to stop."
cd "$ROOT_DIR"
/venv/arena-env/bin/python -m http.server "$PORT"
