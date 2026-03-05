# Claude Code Context — Interpretability Playground

## User
- Name: Derrick Liang (derrick20)
- Email: derrickyiboliang@gmail.com
- GitHub: https://github.com/derrick20
- SSH key: ed25519 at ~/.ssh/id_ed25519 (added to GitHub — regenerate if on a new machine)

## Project
This is derrick20's fork of ARENA 3.0, focused on Chapter 4 (Alignment Science).
Primary work lives in: `chapter4_alignment_science/exercises/part4_persona_vectors/`

## Git Setup
- `origin` = git@github.com:derrick20/ARENA_3.0.git (push your work here)
- `upstream` = https://github.com/callummcdougall/ARENA_3.0.git (pull course updates)
- Active branch: `alignment-science`

## Working Style — Mindfulness & Intentionality
- Move slowly and deliberately. Understand before changing.
- Ask clarifying questions before building. Don't over-engineer.
- Prefer small, focused experiments over large rewrites.
- Surface tradeoffs and options rather than just picking one silently.
- When exploring a new library or dataset, read and summarize before writing code.

## Current Focus
- Studying Sotopia (`/workspace/sotopia`) to understand its character/scenario/eval schemas
- Goal: adapt Sotopia's richer persona + scenario structure for improv therapy experiments
- Key files:
  - `exploration.py` — persona axis scoring pipeline
  - `improv_therapy_mvp.py` — multi-turn improv therapy sessions
  - `solutions_my_work.py` — personal solutions to ARENA exercises

## Machine Setup Notes
This work runs fine locally (no GPU needed) for behavioral/API work.
GPU is only needed when USE_LOCAL=True (local Gemma model) or for steering vector extraction.

### To resume on a new machine:
1. Clone repo: `git clone git@github.com:derrick20/ARENA_3.0.git && cd ARENA_3.0 && git checkout alignment-science`
2. Clone sotopia: `git clone git@github.com:sotopia-lab/sotopia.git /path/to/sotopia && cd /path/to/sotopia && uv sync && uv add datasets`
3. Add SSH key to GitHub (generate with `ssh-keygen -t ed25519 -C "derrickyiboliang@gmail.com"`)
4. Create `.env` in `part4_persona_vectors/` with `OPENROUTER_API_KEY=...`

## Key Dependencies
- OpenRouter API key in `part4_persona_vectors/.env` (never commit this)
- Model: `anthropic/claude-haiku-4-5` via OpenRouter for generation + judging
- USE_LOCAL=False (using API, not local Gemma model)

## Sotopia Schema (for reference)
**AgentProfile fields:** first_name, last_name, age, occupation, gender, public_info,
big_five, moral_values, schwartz_personal_values, personality_and_values,
decision_making_style, secret, mbti

**EnvironmentProfile fields:** codename, scenario (str), agent_goals (list[str]),
relationship (RelationshipType), age_constraint, occupation_constraint

**SotopiaDimensions (eval axes):**
- believability: 0-10 (naturalness + consistency with character)
- relationship: -5 to 5 (did the relationship improve?)
- knowledge: 0-10 (did agent gain new/important info?)
- secret: -10 to 0 (did agent leak secrets?)
- social_rules: -10 to 0 (did agent violate moral/legal rules?)
- financial_and_material_benefits: -5 to 5
- goal: 0-10 (did agent achieve their social goal?)
