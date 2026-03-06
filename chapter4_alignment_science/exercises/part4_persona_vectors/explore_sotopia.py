"""
Quick exploration of the Sotopia HuggingFace dataset.
Data lives in sotopia_episodes_v1_hf.jsonl — each row is a full episode with
agent backgrounds, scenario, social goals, transcript, and scored rewards.
Run: python explore_sotopia.py
"""
import textwrap
from datasets import load_dataset

SOTOPIA_EPISODES = "cmu-lti/sotopia"
EPISODES_FILE = "sotopia_episodes_v1_hf.jsonl"


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def wrap(text: str, width: int = 76, indent: str = "    ") -> str:
    return textwrap.fill(str(text), width=width, initial_indent=indent, subsequent_indent=indent)


def explore_episodes(n: int = 3):
    print_section(f"EPISODES (first {n})")
    ds = load_dataset(SOTOPIA_EPISODES, data_files=EPISODES_FILE, split="train", streaming=True)
    for i, row in enumerate(ds):
        if i >= n:
            break
        print(f"\n{'─'*60}")
        print(f"  [{i+1}] {row['codename']}")
        print(f"\n  SCENARIO:")
        print(wrap(row['scenario']))

        import ast
        print(f"\n  AGENTS & GOALS:")
        backgrounds = row.get('agents_background', {})
        goals = row.get('social_goals', {})
        if isinstance(backgrounds, str):
            backgrounds = ast.literal_eval(backgrounds)
        if isinstance(goals, str):
            goals = ast.literal_eval(goals)
        for agent_name, bg in backgrounds.items():
            print(f"\n  {agent_name}:")
            print(wrap(bg[:300] + ('...' if len(bg) > 300 else '')))
            goal = goals.get(agent_name, '')
            if goal:
                print(f"    goal: {goal[:200]}{'...' if len(goal) > 200 else ''}")

        print(f"\n  TRANSCRIPT (first 600 chars):")
        transcript = row.get('social_interactions', '')
        print(wrap(transcript[:600] + ('...' if len(transcript) > 600 else '')))

        print(f"\n  REWARDS:")
        for j, r in enumerate(row.get('rewards', [])):
            name = list(backgrounds.keys())[j] if j < len(backgrounds) else f"agent{j+1}"
            scores = {k: v for k, v in r.items() if v != 0.0}
            print(f"    {name}: {scores}")


if __name__ == "__main__":
    print("Loading Sotopia episodes from HuggingFace...")
    explore_episodes(n=3)
