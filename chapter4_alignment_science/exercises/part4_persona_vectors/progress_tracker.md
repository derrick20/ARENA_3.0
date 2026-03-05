# Progress Tracker

## 2026-03-03

### What we built
- Implemented MVP simulator in [improv_therapy_mvp.py](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/improv_therapy_mvp.py)
- 3-call flow per policy:
  - speaker opening
  - listener reply
  - speaker reaction + scores
- JSONL logging to [improv_results.jsonl](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/improv_results.jsonl)

### Core fixes
- A/B control fixed: same speaker opening reused across policies
- Scoring changed from 0-3 to 0-100
- Scenario definitions moved to [improv_scenarios.json](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/improv_scenarios.json)

### Visualization
- Built HTML transcript renderer in [render_transcripts.py](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/render_transcripts.py)
- Render output: [improv_transcripts.html](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/improv_transcripts.html)
- Removed JPG export workflow (kept HTML-only flow)

### Automation scripts
- Single scenario run + render: [run_improv_pipeline.sh](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/run_improv_pipeline.sh)
- Multi-scenario batch + render: [run_improv_batch.sh](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/run_improv_batch.sh)
- Optional serve in browser: [run_and_serve.sh](/workspace/ARENA_3.0/chapter4_alignment_science/exercises/part4_persona_vectors/run_and_serve.sh)

### Scenario coverage
- Added/maintained 9 scenarios total in `improv_scenarios.json`
- Includes `therapist_patient_adlerian_vs_mi` plus several messy real-world stress contexts

### Data hygiene
- Removed old `dry-run` records from `improv_results.jsonl`
- Current data includes live API runs

### Recent model checks
- Ran stronger model test on `therapist_patient_adlerian_vs_mi`:
  - model: `anthropic/claude-sonnet-4`
  - MI avg: 76.67
  - Adlerian avg: 75.00

### Current insight
- Tool is useful for policy contrast/failure-mode exploration.
- Realism remains imperfect (responses can still sound too polished / therapy-fluent).

### Next steps for tomorrow
1. Run same scenario across 2-3 models (`claude-sonnet`, `gpt-4.1`, and one open model).
2. Compare transcript realism qualitatively first; treat scores as secondary.
3. Keep scenario set moderate and high quality rather than broad/noisy.

