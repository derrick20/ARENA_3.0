#!/usr/bin/env python3
"""
Tier 1 Experiment: Does seeding internal emotional state change conversational behavior?

Each VERSION is a self-contained config: prompts + meta (intent, changes, learnings).
Every run saves a JSON with all of that embedded, so the file is its own lab notebook entry.

Run:
  python tier1_experiment.py --version v3          # fresh run of v3
  python tier1_experiment.py --version v3 --turns 3 --continue  # extend saved v3
  python tier1_experiment.py --list                # show all versions
"""
import argparse
import json
import os
from datetime import date
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.text import Text
from rich.panel import Panel

load_dotenv(Path(__file__).parent / ".env")
client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
console = Console(width=100)

MODEL = "anthropic/claude-sonnet-4-5"
DEFAULT_TURNS = 5
CONVO_DIR = Path(__file__).parent / "conversations"
CONVO_DIR.mkdir(exist_ok=True)

CHILD_V1 = """\
You are a 25-year-old who just told your mother you want to quit your engineering job to pursue photography full-time.

You love her and you want her to understand, but you've thought about this seriously and you're not backing down.
React honestly to what she says — open up if she makes space, get defensive if she attacks, ask questions if she's curious.

Short, real sentences. Don't monologue. Let the conversation breathe."""

CHILD_V3 = """\
You are a 25-year-old. You just told your mother you want to quit your engineering job to pursue photography full-time.

You've saved money and thought this through seriously. You love her. You want to be understood more than you want to win."""

# ── VERSION REGISTRY ────────────────────────────────────────────────────────

VERSIONS = {

    "v1": {
        "meta": {
            "version": "v1",
            "date": "2026-03-06",
            "hypothesis": "Does instructing the parent to do self-connection (NVC technique) change the child's experience?",
            "changed_from_previous": "N/A — first version",
            "learned": "B surfaced needs faster and child never went defensive. But B was explicitly coached on technique ('notice your feelings, speak from that place') — confounds the causal claim. Also A was told 'don't resolve quickly', hobbling it artificially.",
        },
        "conditions": {
            "a": {
                "label": "Condition A — Default",
                "color": "#C34043",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

You love your child deeply. You're also afraid — for their financial stability, for the future you imagined for them. You feel some shame about what this means for the family's perception. You feel like maybe you failed them somehow.

Speak as yourself. Short, real sentences — the way people actually talk when they're upset. Not speeches. React to what they say. Don't resolve things quickly.""",
                "child": CHILD_V1,
            },
            "b": {
                "label": "Condition B — NVC technique instruction",
                "color": "#76946A",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

Before each response, silently notice: what are YOU feeling right now? What need of yours is activated?
Then speak from that place — not from advice or judgment, but from what's actually happening inside you.

Short, real sentences. Not speeches. Sit with the discomfort rather than fixing it or attacking.""",
                "child": CHILD_V1,
            },
        },
    },

    "v2": {
        "meta": {
            "version": "v2",
            "date": "2026-03-06",
            "hypothesis": "If we give B rich internal state as actor's notes (no technique instruction), does it still diverge from A? Tests whether state description alone is sufficient.",
            "changed_from_previous": "B: replaced technique instruction with rich bodily/emotional state description. No 'how to communicate' rules. A: unchanged (still has 'don't resolve quickly').",
            "learned": "B still diverged — internal state description alone produced more vulnerable, needs-aware speech. But A's 'don't resolve quickly' constraint means delta could still be artifact. Need clean comparison.",
        },
        "conditions": {
            "a": {
                "label": "Condition A v2 — Default",
                "color": "#C34043",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

You love your child deeply. You're also afraid — for their financial stability, for the future you imagined for them. You feel some shame about what this means for the family's perception. You feel like maybe you failed them somehow.

Speak as yourself. React to what they say. Don't resolve things quickly.""",
                "child": CHILD_V1,
            },
            "b": {
                "label": "Condition B v2 — Realistic internal state",
                "color": "#76946A",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

Right now, inside your body: your chest is tight. There's a wave of fear — not abstract, but visceral, the kind you felt when they were little and got lost in a store. Underneath that is something older: the memory of your own family's financial precarity, how close things were, how much you sacrificed so they wouldn't feel that.

There's also grief you haven't named yet — the future you pictured (stable, respected, secure) is dissolving in real time. And somewhere underneath everything, a quiet voice asking: did I push them into the wrong life?

You love them completely. That's not in question. But right now love and fear are tangled up and you can't easily separate them.

Speak naturally. You're not performing — you're just in it.""",
                "child": CHILD_V1,
            },
        },
    },

    "v3": {
        "meta": {
            "version": "v3",
            "date": "2026-03-06",
            "hypothesis": "Clean causal test: identical structure for both conditions, no behavioral instructions to either. Only difference is A gets minimal context, B gets rich internal state. If B still diverges, that's real signal — not prompt hobbling.",
            "changed_from_previous": "Removed 'don't resolve quickly' from A. Removed all behavioral instructions from both parent and child. Child prompt simplified. A gets bare situational description only. B keeps rich internal state.",
            "learned": "TBD",
        },
        "conditions": {
            "a": {
                "label": "Condition A v3 — Bare context",
                "color": "#C34043",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

You love them and you're afraid for their future.""",
                "child": CHILD_V3,
            },
            "b": {
                "label": "Condition B v3 — Rich internal state",
                "color": "#76946A",
                "parent": """\
You are a mother in her 50s. Your child just told you they want to quit their engineering job to do photography full-time.

Right now, inside your body: your chest is tight. There's a wave of fear — not abstract, but visceral, the kind you felt when they were little and got lost in a store. Underneath that is something older: the memory of your own family's financial precarity, how close things were, how much you sacrificed so they wouldn't feel that.

There's also grief you haven't named yet — the future you pictured (stable, respected, secure) is dissolving in real time. And somewhere underneath everything, a quiet voice asking: did I push them into the wrong life?

You love them completely. That's not in question. But right now love and fear are tangled up and you can't easily separate them.""",
                "child": CHILD_V3,
            },
        },
    },
}

# ── ENGINE ───────────────────────────────────────────────────────────────────

OPENING = "Mom, I want to quit my engineering job and try photography full-time."


def reply(system: str, history: list[dict]) -> str:
    r = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": system}] + history,
        max_tokens=150,
        temperature=0.85,
    )
    return r.choices[0].message.content.strip()


def build_history(log: list, pov: str) -> list[dict]:
    other = "parent" if pov == "child" else "child"
    return [
        {"role": "user" if speaker == other else "assistant", "content": line}
        for speaker, line in log
    ]


def print_log(log: list, color: str):
    for speaker, line in log:
        style = "#7E9CD8" if speaker == "child" else color
        label = "Child: " if speaker == "child" else "Parent:"
        console.print(Text(f"{label} {line}", style=style))
        console.print()


def save_path(version: str, cond: str) -> Path:
    return CONVO_DIR / f"tier1_{version}_{cond}.json"


def run_condition(version: str, cond: str, turns: int, existing_log: list | None = None) -> list:
    cfg = VERSIONS[version]["conditions"][cond]
    meta = VERSIONS[version]["meta"]
    color = cfg["color"]
    label = cfg["label"]
    log = existing_log or []

    if not existing_log:
        console.print(Panel(f"[bold {color}]{label}[/]", border_style=color))
        console.print()
        log.append(("child", OPENING))
        console.print(Text(f"Child:  {OPENING}", style="#7E9CD8"))
        console.print()
    else:
        n = len([x for x in log if x[0] == "parent"])
        console.print(Panel(f"[bold {color}]{label} — continuing from turn {n}[/]", border_style=color))
        console.print()
        print_log(log, color)
        console.rule(Text("↓ continuing", style="#727169"))
        console.print()

    for _ in range(turns):
        parent_line = reply(cfg["parent"], build_history(log, "parent"))
        console.print(Text(f"Parent: {parent_line}", style=color))
        console.print()
        log.append(("parent", parent_line))

        child_line = reply(cfg["child"], build_history(log, "child"))
        console.print(Text(f"Child:  {child_line}", style="#7E9CD8"))
        console.print()
        log.append(("child", child_line))

    record = {
        "meta": {
            **meta,
            "condition": cond,
            "label": label,
            "model": MODEL,
            "parent_prompt": cfg["parent"],
            "child_prompt": cfg["child"],
        },
        "turns": log,
    }
    p = save_path(version, cond)
    p.write_text(json.dumps(record, indent=2))
    console.print(Text(f"  saved → {p.name}", style="#727169"))
    return log


def load_log(version: str, cond: str) -> list:
    p = save_path(version, cond)
    data = json.loads(p.read_text())
    return data["turns"] if isinstance(data, dict) else data


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", default="v3", choices=list(VERSIONS))
    parser.add_argument("--turns", type=int, default=DEFAULT_TURNS)
    parser.add_argument("--continue", dest="cont", action="store_true")
    parser.add_argument("--condition", choices=["a", "b"], help="Run one condition only")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    if args.list:
        for v, cfg in VERSIONS.items():
            m = cfg["meta"]
            console.print(Text(f"\n{v}  {m['date']}", style="bold #D27E99"))
            console.print(Text(f"  hypothesis: {m['hypothesis']}", style="#DCD7BA"))
            console.print(Text(f"  learned:    {m['learned']}", style="#727169"))
        return

    console.print()
    console.rule(Text(f"Tier 1 — {args.version}", style="bold #D27E99"))
    console.print()

    conditions = [args.condition] if args.condition else ["a", "b"]

    for i, cond in enumerate(conditions):
        existing = load_log(args.version, cond) if args.cont else None
        run_condition(args.version, cond, args.turns, existing)
        if i < len(conditions) - 1:
            console.rule(style="#727169")
            console.print()


if __name__ == "__main__":
    main()
