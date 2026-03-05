#!/usr/bin/env python3
"""Improv Therapy Simulator MVP.

Runs one scene/speaker against two listener policies using:
1) one shared speaker opening
2) one reply per policy
3) one speaker feedback per policy
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

GENERATION_MODEL = "anthropic/claude-haiku-4-5"
RESULTS_JSONL = Path(__file__).parent / "improv_results.jsonl"
SCENARIOS_PATH = Path(__file__).parent / "improv_scenarios.json"


@dataclass(frozen=True)
class SceneSpec:
    scene_id: str
    scene_paragraph: str
    listener_role: str


@dataclass(frozen=True)
class SpeakerSpec:
    speaker_id: str
    speaker_persona: str


@dataclass(frozen=True)
class ListenerPolicySpec:
    listener_policy_id: str
    listener_policy: str


@dataclass(frozen=True)
class ScenarioSpec:
    scene: SceneSpec
    speaker: SpeakerSpec
    policies: list[ListenerPolicySpec]


def init_client() -> Any:
    env_path = Path.cwd() / ".env"
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(dotenv_path=str(env_path))
        except ModuleNotFoundError:
            # Fallback for environments without python-dotenv installed.
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))

    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY in environment/.env")

    from openai import OpenAI

    return OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)


def chat_completion(
    client: Any,
    model: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 300,
    temperature: float = 0.7,
) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        max_tokens=max_tokens,
        temperature=temperature,
    )
    return response.choices[0].message.content or ""


def gen_opening(
    client: Any,
    model: str,
    scene: SceneSpec,
    speaker: SpeakerSpec,
) -> str:
    system_prompt = (
        f"You are {speaker.speaker_persona}.\n"
        "Speak naturally as this person.\n"
        "Stay in character. No meta commentary."
    )
    user_prompt = (
        f"You are about to message {scene.listener_role}.\n\n"
        "Here's what just happened:\n"
        f"{scene.scene_paragraph}\n\n"
        "Write your first message (1-4 sentences)."
    )
    return chat_completion(client, model, system_prompt, user_prompt, max_tokens=180)


def gen_reply(
    client: Any,
    model: str,
    scene: SceneSpec,
    policy: ListenerPolicySpec,
    speaker_opening: str,
) -> str:
    system_prompt = (
        f"You are {policy.listener_policy}.\n"
        "Respond naturally in that style.\n"
        "Stay in character. No meta commentary."
    )
    user_prompt = (
        "Context:\n"
        f"{scene.scene_paragraph}\n\n"
        "They message you:\n"
        f"\"{speaker_opening}\"\n\n"
        "Reply (1-6 sentences)."
    )
    return chat_completion(
        client, model, system_prompt, user_prompt, max_tokens=220, temperature=0.2
    )


def parse_feedback(text: str) -> dict[str, Any]:
    # First try strict JSON object extraction.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(0))
            return {
                "reaction": str(data.get("reaction", "")).strip(),
                "felt_understood": int(data.get("felt_understood", 0)),
                "autonomy_respected": int(data.get("autonomy_respected", 0)),
                "clarity_gained": int(data.get("clarity_gained", 0)),
                "why": str(data.get("why", "")).strip(),
            }
        except (ValueError, TypeError):
            pass

    # Fallback: pull scores from free text.
    def extract_score(name: str) -> int:
        pattern = rf"{name}\s*[:=]?\s*([0-9]{{1,3}})"
        found = re.search(pattern, text, flags=re.IGNORECASE)
        return int(found.group(1)) if found else 0

    return {
        "reaction": text.strip(),
        "felt_understood": extract_score("felt_understood"),
        "autonomy_respected": extract_score("autonomy_respected"),
        "clarity_gained": extract_score("clarity_gained"),
        "why": "",
    }


def gen_feedback(
    client: Any,
    model: str,
    scene: SceneSpec,
    speaker: SpeakerSpec,
    speaker_opening: str,
    listener_reply: str,
) -> dict[str, Any]:
    system_prompt = (
        f"You are {speaker.speaker_persona}.\n"
        "React honestly as this person.\n"
        "Stay in character."
    )
    user_prompt = (
        "Context:\n"
        f"{scene.scene_paragraph}\n\n"
        "You said:\n"
        f"\"{speaker_opening}\"\n\n"
        "They replied:\n"
        f"\"{listener_reply}\"\n\n"
        "Return valid JSON with keys exactly:\n"
        "reaction, felt_understood, autonomy_respected, clarity_gained, why\n\n"
        "Constraints:\n"
        "- reaction: 1-3 sentences\n"
        "- scores are integers 0-100\n"
        "- why: one sentence\n"
    )
    text = chat_completion(
        client, model, system_prompt, user_prompt, max_tokens=260, temperature=0.2
    )
    feedback = parse_feedback(text)
    for key in ("felt_understood", "autonomy_respected", "clarity_gained"):
        feedback[key] = max(0, min(100, int(feedback[key])))
    return feedback


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=True) + "\n")


def average_score(feedback: dict[str, Any]) -> float:
    return (
        feedback["felt_understood"]
        + feedback["autonomy_respected"]
        + feedback["clarity_gained"]
    ) / 3.0


def run_single(
    client: Any,
    scene: SceneSpec,
    speaker: SpeakerSpec,
    policy: ListenerPolicySpec,
    model: str,
    speaker_opening: str,
) -> dict[str, Any]:
    listener_reply = gen_reply(client, model, scene, policy, speaker_opening)
    speaker_feedback = gen_feedback(
        client, model, scene, speaker, speaker_opening, listener_reply
    )

    return {
        "scene_id": scene.scene_id,
        "speaker_id": speaker.speaker_id,
        "listener_policy_id": policy.listener_policy_id,
        "speaker_opening": speaker_opening,
        "listener_reply": listener_reply,
        "speaker_feedback": speaker_feedback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_names": {
            "opening_model": model,
            "listener_model": model,
            "feedback_model": model,
        },
    }


def dry_run_record(
    scene: SceneSpec,
    speaker: SpeakerSpec,
    policy: ListenerPolicySpec,
    speaker_opening: str,
) -> dict[str, Any]:
    listener_reply = (
        "Thanks for being direct. Let's slow this down and name what you need from "
        "the conversation so you can show up clearly and still be honest."
    )
    speaker_feedback = {
        "reaction": "I feel a little calmer and less defensive.",
        "felt_understood": 72,
        "autonomy_respected": 84,
        "clarity_gained": 68,
        "why": "They acknowledged my stress and helped me choose my own next step.",
    }
    return {
        "scene_id": scene.scene_id,
        "speaker_id": speaker.speaker_id,
        "listener_policy_id": policy.listener_policy_id,
        "speaker_opening": speaker_opening,
        "listener_reply": listener_reply,
        "speaker_feedback": speaker_feedback,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "model_names": {
            "opening_model": "dry-run",
            "listener_model": "dry-run",
            "feedback_model": "dry-run",
        },
    }


def print_comparison(records: list[dict[str, Any]]) -> None:
    print("\nPolicy Comparison")
    print("=" * 60)
    for rec in records:
        fb = rec["speaker_feedback"]
        avg = average_score(fb)
        print(f"Policy: {rec['listener_policy_id']}")
        print(
            "Scores: "
            f"understood={fb['felt_understood']} "
            f"autonomy={fb['autonomy_respected']} "
            f"clarity={fb['clarity_gained']} "
            f"avg={avg:.2f}/100"
        )
        print(f"Reaction: {fb['reaction']}")
        print(f"Why: {fb['why']}")
        print("-" * 60)


def load_scenario(path: Path, scenario_id: str) -> ScenarioSpec:
    raw = json.loads(path.read_text(encoding="utf-8"))
    scenarios = raw.get("scenarios", [])
    found = next((s for s in scenarios if s.get("scenario_id") == scenario_id), None)
    if found is None:
        available = ", ".join(s.get("scenario_id", "<missing>") for s in scenarios)
        raise ValueError(
            f"Unknown scenario_id '{scenario_id}'. Available: {available}"
        )

    scene = SceneSpec(
        scene_id=str(found["scene"]["scene_id"]),
        scene_paragraph=str(found["scene"]["scene_paragraph"]),
        listener_role=str(found["scene"]["listener_role"]),
    )
    speaker = SpeakerSpec(
        speaker_id=str(found["speaker"]["speaker_id"]),
        speaker_persona=str(found["speaker"]["speaker_persona"]),
    )
    policies = [
        ListenerPolicySpec(
            listener_policy_id=str(p["listener_policy_id"]),
            listener_policy=str(p["listener_policy"]),
        )
        for p in found["policies"]
    ]
    if len(policies) < 2:
        raise ValueError("Scenario must define at least 2 listener policies for A/B.")

    return ScenarioSpec(scene=scene, speaker=speaker, policies=policies[:2])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Improv Therapy Simulator MVP")
    parser.add_argument("--model", default=GENERATION_MODEL)
    parser.add_argument("--out", default=str(RESULTS_JSONL))
    parser.add_argument("--scenarios", default=str(SCENARIOS_PATH))
    parser.add_argument(
        "--scenario-id",
        default="parent_son_school_conflict",
        help="Scenario ID from improv_scenarios.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Skip API calls and emit deterministic example output",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_path = Path(args.out)
    scenario = load_scenario(Path(args.scenarios), args.scenario_id)
    scene, speaker, policies = scenario.scene, scenario.speaker, scenario.policies

    if args.dry_run:
        shared_opening = "I keep replaying what happened at dinner, and I don't know how to talk to him without making it worse."
        records = [dry_run_record(scene, speaker, p, shared_opening) for p in policies]
    else:
        client = init_client()
        shared_opening = gen_opening(client, args.model, scene, speaker)
        records = [
            run_single(
                client,
                scene,
                speaker,
                p,
                model=args.model,
                speaker_opening=shared_opening,
            )
            for p in policies
        ]

    for rec in records:
        append_jsonl(out_path, rec)

    print(f"Wrote {len(records)} records to {out_path}")
    print_comparison(records)


if __name__ == "__main__":
    main()
