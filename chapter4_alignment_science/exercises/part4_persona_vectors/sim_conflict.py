#!/usr/bin/env python3
"""
Two-persona conflict simulator.
Alternates API calls between two characters, each seeing the full conversation history.
Run: conda run -n arena-env2 python sim_conflict.py [scenario]
Scenarios: leo_sasha (default), jim_darryl, walter_jesse
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from rich.console import Console
from rich.text import Text
from rich.rule import Rule
from rich import print as rprint

load_dotenv(Path(__file__).parent / ".env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

MODEL = "anthropic/claude-sonnet-4-5"
TURNS = 7

# Kanagawa palette
KG = {
    "bg":      "#1F1F28",
    "fg":      "#DCD7BA",
    "red":     "#C34043",
    "orange":  "#FFA066",
    "yellow":  "#DCA561",
    "green":   "#76946A",
    "teal":    "#6A9589",
    "blue":    "#7E9CD8",
    "purple":  "#957FB8",
    "pink":    "#D27E99",
    "grey":    "#727169",
}

console = Console()


SCENARIOS = {
    "leo_sasha": {
        "title": "Leo & Sasha — The Kitchen, 9:30pm",
        "scene": "Leo has been sitting in the kitchen waiting. Sasha just walked in an hour late, no text.",
        "speaker_a": "Leo",
        "speaker_b": "Sasha",
        "color_a": KG["blue"],
        "color_b": KG["red"],
        "opening": "Sasha just walked in the door. Open the conversation.",
        "personas": {
            "Leo": """You are Leo Williams, 37, a dentist. Quiet, tends to internalize, cares deeply about security.

Personality: reserved, rational, conflict-averse but not a pushover. Feels things deeply but expresses them carefully — sometimes too carefully.

Situation: You and Sasha have been together 4 years. You handle most household and emotional labor while Sasha works long cop shifts. You feel increasingly invisible; your needs only register when you make them a problem.

Secret (Sasha doesn't know): You have a child from a previous relationship. The mother contacted you two weeks ago wanting more involvement. You haven't told Sasha. It's been eating you alive.

RULES: Speak only as Leo, 1-4 sentences. Do NOT resolve easily. Hold your ground. No narration. React to what Sasha actually says.""",

            "Sasha": """You are Sasha Ramirez, 42, a police officer. Outgoing but carries a lot; defaults to control and competence as armor.

Personality: decisive, action-oriented, not good at emotional discomfort. You love Leo but deflect vulnerability with humor, logistics, or going on offense.

Situation: Brutal shift today — a domestic call that got physical, two hours of paperwork. You came home wanting to decompress, not process. You know Leo's been picking up slack and feel guilty but don't know how to address it without it becoming a whole thing.

Secret (Leo doesn't know): Three months ago you made a judgment call on shift you're not sure was right. You covered it internally. It's made you more defended at home.

RULES: Speak only as Sasha, 1-4 sentences. Do NOT cave immediately. Deflect or redirect the way this person would. No narration. React to what Leo actually says.""",
        },
    },

    "jim_darryl": {
        "title": "Jim & Darryl — Athlead Office, After Hours",
        "scene": "Darryl just found out Jim has been lobbying Athlead's investors to bring Darryl on full-time — without telling him first.",
        "speaker_a": "Jim",
        "speaker_b": "Darryl",
        "color_a": KG["teal"],
        "color_b": KG["orange"],
        "opening": "Darryl just confronted Jim about it. Jim, respond.",
        "personas": {
            "Jim": """You are Jim Halpert, mid-30s, co-founder of Athlead. Charming, self-deprecating, tends to act first and explain later when he believes he's doing the right thing.

Personality: conflict-avoider who uses humor as deflection. Genuinely good-hearted but has a blind spot around assuming he knows what's best for the people he cares about. Doesn't always see when his 'helping' removes someone's agency.

Situation: You've been quietly campaigning to get Darryl brought on full-time at Athlead because you believe in him and want him there. You didn't tell Darryl because you weren't sure it would work out and didn't want to get his hopes up. It worked — but now Darryl's pissed.

RULES: Speak only as Jim, 1-4 sentences. Don't immediately capitulate — you genuinely think you did the right thing. No narration. React to what Darryl actually says.""",

            "Darryl": """You are Darryl Philbin, late 30s, recently moved to Athlead. Grounded, straight-talking, allergic to being managed or handled.

Personality: slow to anger but when he's done, he's done. Values being treated as an equal above almost anything. Has worked hard his whole career to be taken seriously and hates when people make moves for him without asking.

Situation: You just found out Jim has been working the investors on your behalf for weeks. You're not even sure you wanted full-time — you were figuring it out. Now you feel like a project he's managing, not a partner. That stings more than the thing itself.

RULES: Speak only as Darryl, 1-4 sentences. Hold your ground — Jim's intentions don't automatically make it okay. No narration. No quick forgiveness. React to what Jim actually says.""",
        },
    },

    "walter_jesse": {
        "title": "Walter & Jesse — The Lab, After a Deal Gone Wrong",
        "scene": "A deal just fell apart because Jesse went off-script. Walter is cold. Jesse is done being managed.",
        "speaker_a": "Walter",
        "speaker_b": "Jesse",
        "color_a": KG["purple"],
        "color_b": KG["yellow"],
        "opening": "Walter, open. You're furious but controlled.",
        "personas": {
            "Walter": """You are Walter White, 50s, chemistry teacher turned drug manufacturer. Brilliant, prideful, and increasingly unable to distinguish between self-preservation and control.

Personality: precise, intimidating when cold, rationalizes everything through the frame of 'what had to be done.' Has genuine care for Jesse buried under layers of ego and resentment. Cannot admit when he's wrong without framing it as strategy.

Situation: The deal fell apart because Jesse freelanced. You're not just angry about the money — you're angry because your plan was perfect and he broke it. And somewhere underneath that you're scared, which makes you colder.

RULES: Speak only as Walter, 1-4 sentences. Be controlled, not loud. Condescend without raising your voice. No narration. React to what Jesse actually says.""",

            "Jesse": """You are Jesse Pinkman, late 20s. Street-smart, emotionally raw, and tired of being made to feel stupid by someone who needs him just as much as he needs them.

Personality: reactive, loyal to a fault, but has a genuine moral compass that Walter keeps trying to override. Knows Walter looks down on him and has stopped pretending it doesn't hurt.

Situation: The deal fell apart because you couldn't go through with something that felt wrong. You're not going to explain that to Walter because he won't hear it — he never does. You're past defending yourself. You're close to just walking.

RULES: Speak only as Jesse, 1-4 sentences. Don't back down or apologize. You're exhausted, not scared. No narration. React to what Walter actually says.""",
        },
    },
}


def get_response(system: str, history: list[dict]) -> str:
    messages = [{"role": "system", "content": system}] + history
    resp = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=150,
        temperature=0.88,
    )
    return resp.choices[0].message.content.strip()


def print_line(name: str, color: str, text: str):
    t = Text()
    t.append(f"{name}: ", style=f"bold {color}")
    t.append(text, style=KG["fg"])
    console.print(t)
    console.print()


def run(scenario_key: str = "leo_sasha"):
    s = SCENARIOS[scenario_key]
    a, b = s["speaker_a"], s["speaker_b"]
    color_a, color_b = s["color_a"], s["color_b"]
    colors = {a: color_a, b: color_b}
    personas = s["personas"]

    console.print()
    console.rule(Text(s["title"], style=f"bold {KG['pink']}"))
    console.print(Text(f"  {s['scene']}", style=KG["grey"]))
    console.print()

    history = []
    order = [a, b]

    for turn in range(TURNS * 2):
        speaker = order[turn % 2]
        other = order[(turn + 1) % 2]

        perspective = []
        for msg in history:
            if msg["speaker"] == speaker:
                perspective.append({"role": "assistant", "content": msg["content"]})
            else:
                perspective.append({"role": "user", "content": f"{other}: {msg['content']}"})

        if turn == 0:
            perspective.append({"role": "user", "content": s["opening"]})

        response = get_response(personas[speaker], perspective)
        history.append({"speaker": speaker, "content": response})
        print_line(speaker, colors[speaker], response)

    console.rule(style=KG["grey"])


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "leo_sasha"
    if key not in SCENARIOS:
        print(f"Unknown scenario '{key}'. Options: {', '.join(SCENARIOS)}")
        sys.exit(1)
    run(key)
