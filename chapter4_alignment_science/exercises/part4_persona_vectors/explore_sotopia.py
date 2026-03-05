"""
Quick exploration of the Sotopia HuggingFace dataset.
Loads characters and scenarios, pretty-prints a few examples.
Run: python explore_sotopia.py
"""
import json
from datasets import load_dataset


def print_section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def explore_agents(n: int = 5):
    print_section(f"AGENTS (first {n})")
    ds = load_dataset("cmu-lti/sotopia", "agents", split="train", streaming=True)
    for i, row in enumerate(ds):
        if i >= n:
            break
        print(f"\n--- Agent {i+1}: {row.get('first_name')} {row.get('last_name')} ---")
        for key in ["age", "occupation", "gender", "big_five", "mbti",
                    "moral_values", "personality_and_values", "decision_making_style",
                    "public_info", "secret"]:
            val = row.get(key)
            if val:
                print(f"  {key}: {val}")


def explore_scenarios(n: int = 5):
    print_section(f"SCENARIOS (first {n})")
    ds = load_dataset("cmu-lti/sotopia", "environments", split="train", streaming=True)
    for i, row in enumerate(ds):
        if i >= n:
            break
        print(f"\n--- Scenario {i+1}: {row.get('codename')} ---")
        print(f"  relationship: {row.get('relationship')}")
        print(f"  scenario: {row.get('scenario')}")
        goals = row.get("agent_goals", [])
        for j, goal in enumerate(goals):
            print(f"  agent{j+1} goal: {goal}")


def explore_episodes(n: int = 2):
    print_section(f"EPISODES (first {n})")
    try:
        ds = load_dataset("cmu-lti/sotopia", "episodes", split="train", streaming=True)
        for i, row in enumerate(ds):
            if i >= n:
                break
            print(f"\n--- Episode {i+1} ---")
            print(f"  keys: {list(row.keys())}")
            # Print a truncated view
            for key, val in row.items():
                s = str(val)
                print(f"  {key}: {s[:120]}{'...' if len(s) > 120 else ''}")
    except Exception as e:
        print(f"  (episodes config not available: {e})")


if __name__ == "__main__":
    print("Loading Sotopia dataset from HuggingFace (cmu-lti/sotopia)...")

    # Check what configs (subsets) are available
    from datasets import get_dataset_config_names
    configs = get_dataset_config_names("cmu-lti/sotopia")
    print(f"\nAvailable configs: {configs}")

    explore_agents(n=5)
    explore_scenarios(n=5)
    explore_episodes(n=2)
