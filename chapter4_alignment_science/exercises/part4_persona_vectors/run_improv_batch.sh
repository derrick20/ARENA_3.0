#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-/venv/arena-env/bin/python}"
RESULTS_PATH="${RESULTS_PATH:-$ROOT_DIR/improv_results.jsonl}"
HTML_PATH="${HTML_PATH:-$ROOT_DIR/improv_transcripts.html}"

if [[ "$#" -eq 0 ]]; then
  SCENARIOS=(
    "therapist_patient_adlerian_vs_mi"
    "relationship_post_fight_withdrawal"
    "adult_sibling_parent_care_resentment"
    "sobriety_near_relapse_weekend"
    "cofounder_trust_break_release"
    "chronic_pain_partner_distance"
    "grief_avoidance_work_overload"
  )
else
  SCENARIOS=("$@")
fi

echo "Running ${#SCENARIOS[@]} scenarios..."
for scenario_id in "${SCENARIOS[@]}"; do
  echo ""
  echo "=== ${scenario_id} ==="
  "$PYTHON_BIN" "$ROOT_DIR/improv_therapy_mvp.py" \
    --scenario-id "$scenario_id" \
    --out "$RESULTS_PATH"
done

echo ""
echo "Rendering viewer..."
"$PYTHON_BIN" "$ROOT_DIR/render_transcripts.py" \
  --in "$RESULTS_PATH" \
  --out "$HTML_PATH"

echo "Done."
echo "Results: $RESULTS_PATH"
echo "Viewer:  $HTML_PATH"
