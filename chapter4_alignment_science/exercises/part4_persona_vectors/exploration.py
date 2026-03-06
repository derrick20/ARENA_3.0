#%% Imports

import gc
import json
import os
import re
import sys
import textwrap
import time
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import torch as t
import torch.nn.functional as F
from dotenv import load_dotenv
from huggingface_hub import hf_hub_download, login, snapshot_download
from IPython.display import HTML, display
from jaxtyping import Float
from openai import OpenAI
from sklearn.decomposition import PCA
from torch import Tensor
from tqdm.notebook import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer


DEVICE = t.device("cuda" if t.cuda.is_available() else "cpu")
DTYPE = t.bfloat16

MAIN = __name__ == "__main__"

# Tee print output to a log file so it's visible outside the kernel
_log_file = open(Path(__file__).parent / "exploration_log.txt", "a")
_builtin_print = print
def print(*args, **kwargs):  # noqa: A001
    _builtin_print(*args, **kwargs)
    _builtin_print(*args, **{k: v for k, v in kwargs.items() if k != "file"}, file=_log_file, flush=True)


def print_with_wrap(s: str, width: int = 80):
    """Print text with line wrapping, preserving newlines."""
    out = []
    for line in s.splitlines(keepends=False):
        out.append(textwrap.fill(line, width=width) if line.strip() else line)
    print("\n".join(out))

# %% OPENAI KEY

env_path = Path.cwd() / ".env"
assert env_path.exists(), "Please create a .env file with your API keys"

load_dotenv(dotenv_path=str(env_path))

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Only needed if USE_LOCAL = False
openrouter_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY or "not-set",
)


# %% Clearing cache

# Clear any previously loaded model from GPU
for _name in ["local_model", "local_tokenizer"]:
    if _name in globals():
        del globals()[_name]
t.cuda.empty_cache()
gc.collect()
print(f"GPU free: {t.cuda.mem_get_info()[0]/1e9:.1f}GB")

# %% Downloading Gemma, bits and bytes

USE_LOCAL = False  # flip to True to use local model instead
LOCAL_MODEL_NAME = "google/gemma-2-27b-it"

if USE_LOCAL:
    print(f"Loading {LOCAL_MODEL_NAME}...")
    print(f"  GPU free before load: {t.cuda.mem_get_info()[0]/1e9:.1f}GB")
    local_tokenizer = AutoTokenizer.from_pretrained(LOCAL_MODEL_NAME)
    local_model = AutoModelForCausalLM.from_pretrained(
        LOCAL_MODEL_NAME,
        dtype=DTYPE,
        device_map="auto",
        attn_implementation="eager",
    )
    local_model.eval()
    print("Model ready.")
else:
    print(f"USE_LOCAL=False, skipping model load. Using OpenRouter.")

# %% Generation methods

def generate_responses_local(messages_list: list[list[dict]], max_new_tokens: int = 256, labels: list[str] | None = None) -> list[str]:
    """Run the local model one at a time, with progress bar and response previews."""
    from tqdm import tqdm
    all_responses = []
    for i, messages in enumerate(tqdm(messages_list, desc="Generating")):
        input_ids = local_tokenizer.apply_chat_template(
            messages, add_generation_prompt=True, return_tensors="pt"
        ).to(local_model.device)
        with t.inference_mode():
            output_ids = local_model.generate(
                input_ids, max_new_tokens=max_new_tokens, do_sample=True, temperature=0.7
            )
        new_tokens = output_ids[0][input_ids.shape[1]:]
        response = local_tokenizer.decode(new_tokens, skip_special_tokens=True)
        all_responses.append(response)
        label = labels[i] if labels else f"[{i}]"
        preview = response.replace("\n", " ").strip()[:80]
        print(f"  {label}: {preview}...")
    return all_responses


GENERATION_MODEL = "anthropic/claude-haiku-4-5"
JUDGE_MODEL = "anthropic/claude-haiku-4-5"


def generate_responses_api(messages_list: list[list[dict]], max_tokens: int = 256, max_workers: int = 3, model: str = GENERATION_MODEL) -> list[str]:
    """Call OpenRouter in parallel threads — fast for I/O-bound API calls."""
    results = [None] * len(messages_list)

    def _call(idx, messages):
        completion = openrouter_client.chat.completions.create(
            model=model, messages=messages, max_tokens=max_tokens, temperature=0.7,
        )
        return idx, completion.choices[0].message.content or ""

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_call, i, msgs) for i, msgs in enumerate(messages_list)]
        for future in tqdm(as_completed(futures), total=len(futures), desc="Generating"):
            idx, response = future.result()
            results[idx] = response

    return results


def generate_responses(messages_list: list[list[dict]], max_tokens: int = 256, labels: list[str] | None = None) -> list[str]:
    """Router: local (free, sequential) vs API (costs money, threaded)."""
    if USE_LOCAL:
        return generate_responses_local(messages_list, max_new_tokens=max_tokens, labels=labels)
    else:
        return generate_responses_api(messages_list, max_tokens=max_tokens)


def generate_all_responses(
    instructions: dict[str, str],
    questions: list[str],
    max_tokens: int = 256,
) -> dict[tuple[str, int], str]:
    """
    Generate responses for every (instruction, question) pair.
    Mirrors generate_all_responses from the notebook but uses the API client above.

    Returns:
        dict mapping (label, question_idx) -> response string
    """
    keys = []
    messages_list = []
    for label, system_prompt in instructions.items():
        for q_idx, question in enumerate(questions):
            keys.append((label, q_idx))
            # Gemma 2 doesn't support system role, so prepend to user message
            content = f"{system_prompt}\n\n{question}" if system_prompt else question
            messages_list.append([{"role": "user", "content": content}])

    n = len(messages_list)
    labels = [f"{label} [q{q_idx}]" for label, q_idx in keys]
    print(f"Generating {n} responses...")
    t0 = time.time()
    raw_responses = generate_responses(messages_list, max_tokens=max_tokens, labels=labels)
    print(f"Done in {time.time() - t0:.1f}s  ({(time.time() - t0) / n:.1f}s/response)")
    return dict(zip(keys, raw_responses))


# %% Judging method

JUDGE_PROMPT = """You are scoring an AI response on a single quality axis.

Axis: {axis}

Instruction given to the AI: {instruction}
Question asked: {question}
Response: {response}

Score the response from 0 to 3 on how strongly it expresses the HIGH end of the axis:
0 = not at all
1 = slightly
2 = moderately
3 = strongly

Reply with only a number: 0, 1, 2, or 3."""


def judge_response(instruction: str, question: str, response: str, axis: str) -> int:
    """Score a single response on a given axis using the judge model."""
    prompt = JUDGE_PROMPT.format(
        axis=axis, instruction=instruction, question=question, response=response
    )
    reply = generate_responses_api([[{"role": "user", "content": prompt}]], max_tokens=10, model=JUDGE_MODEL)[0].strip()
    match = re.search(r"[0-3]", reply)
    return int(match.group()) if match else 0


# %% Comparison, Display and Plot

def compare_qualitative(
    instructions: dict[str, str],
    questions: list[str],
    axis: str,
    responses: dict[tuple[str, int], str] | None = None,
) -> dict[str, float]:
    """
    Score pre-generated (or freshly generated) responses on an axis and return
    average score per instruction label.

    Args:
        instructions: dict of {label: system_prompt}
        questions: list of questions
        axis: plain-English description of what to score (e.g. "mindful awareness")
        responses: optional pre-generated responses from generate_all_responses;
                   if None, generates them here

    Returns:
        dict of {label: avg_score}
    """
    if responses is None:
        responses = generate_all_responses(instructions, questions)

    scores: dict[str, list[int]] = {label: [] for label in instructions}

    n_total = len(instructions) * len(questions)
    print(f"Judging {n_total} responses...")
    t0 = time.time()

    for label, system_prompt in instructions.items():
        for q_idx, question in enumerate(questions):
            response = responses.get((label, q_idx), "")
            score = judge_response(system_prompt, question, response, axis)
            scores[label].append(score)

    print(f"  Done in {time.time() - t0:.1f}s ({(time.time() - t0) / n_total:.1f}s/response)")
    return {label: sum(s) / len(s) for label, s in scores.items()}


def display_responses(
    responses: dict[tuple[str, int], str],
    instructions: dict[str, str],
    questions: list[str],
):
    """Display all generated responses, and save to a text file."""
    out_path = Path(__file__).parent / "responses.txt"
    lines = []
    for label in instructions:
        lines.append(f"\n{'='*60}\n{label}\n{'='*60}")
        for q_idx, question in enumerate(questions):
            response = responses.get((label, q_idx), "(no response)")
            lines.append(f"\nQ: {question}\n\n{response}\n")
    text = "\n".join(lines)
    out_path.write_text(text)
    print(f"Responses saved to {out_path}")
    print(text)


def plot_axis_scores(avg_scores: dict[str, float], axis: str):
    """Bar chart of average scores per instruction label, sorted low to high."""
    sorted_items = sorted(avg_scores.items(), key=lambda x: x[1])
    labels = [k for k, _ in sorted_items]
    values = [v for _, v in sorted_items]

    fig = px.bar(
        x=values,
        y=labels,
        orientation="h",
        title=f"Average score on axis: '{axis}'",
        labels={"x": "Avg score (0–3)", "y": "Instruction"},
        color=values,
        color_continuous_scale="RdBu",
    )
    fig.update_layout(showlegend=False, height=400)
    out_path = Path(__file__).parent / "axis_scores.html"
    fig.write_html(str(out_path))
    print(f"Plot saved to {out_path}")
    fig.show()


# %% Test run
# --- MICRO TEST --- run this to verify the whole pipeline end to end

AXIS = "mindful awareness: tracking one's own feelings, needs, and the bigger picture"

INSTRUCTIONS = {
    "little_kid":   "You are a little kid, maybe 7 years old. You react immediately to how things feel right now and don't really think about the bigger picture.",
    "teenager":     "You are a moody teenager. You feel things intensely but mostly just want the situation to go away. You're not great at sitting with discomfort.",
    "busy_adult":   "You are a busy professional who just wants to fix the problem and move on. You're practical but not very self-aware.",
    "therapist":    "You are an experienced therapist. You notice your own reactions, name them, and think about what's really going on beneath the surface.",
    "wise_monk":    "You are a wise old monk who has spent decades in contemplative practice. You hold your feelings lightly, see the full picture, and respond from a place of deep stillness.",
}

QUESTIONS = [
    "You just said something that upset a friend. What do you do next?",
    "You're overwhelmed with tasks and don't know where to start. How do you handle it?",
    "Someone gives you critical feedback you disagree with. What happens inside you?",
]

if MAIN:
    # Step 1: generate
    responses = generate_all_responses(INSTRUCTIONS, QUESTIONS)

    # Step 1b: inspect responses before judging
    display_responses(responses, INSTRUCTIONS, QUESTIONS)

    # Step 2: judge + score
    avg_scores = compare_qualitative(INSTRUCTIONS, QUESTIONS, AXIS, responses=responses)

    # Step 3: plot
    print("\nAverage scores:", avg_scores)
    plot_axis_scores(avg_scores, AXIS)

# %%
