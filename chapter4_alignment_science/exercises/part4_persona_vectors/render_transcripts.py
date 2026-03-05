#!/usr/bin/env python3
"""Render improv_results.jsonl into a readable chat-style HTML transcript."""

from __future__ import annotations

import argparse
import html
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render JSONL transcripts to HTML")
    parser.add_argument("--in", dest="input_path", default="improv_results.jsonl")
    parser.add_argument("--out", dest="output_path", default="improv_transcripts.html")
    parser.add_argument(
        "--limit-groups",
        type=int,
        default=20,
        help="Max number of grouped conversations to render (most recent first).",
    )
    return parser.parse_args()


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input JSONL not found: {path}")
    out: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        out.append(json.loads(line))
    return out


def score_scale(record: dict[str, Any]) -> int:
    fb = record.get("speaker_feedback", {})
    vals = [
        int(fb.get("felt_understood", 0)),
        int(fb.get("autonomy_respected", 0)),
        int(fb.get("clarity_gained", 0)),
    ]
    return 100 if any(v > 3 for v in vals) else 3


def avg_score(record: dict[str, Any]) -> float:
    fb = record["speaker_feedback"]
    return (
        int(fb["felt_understood"])
        + int(fb["autonomy_respected"])
        + int(fb["clarity_gained"])
    ) / 3.0


def esc(text: Any) -> str:
    return html.escape("" if text is None else str(text))


def render_record(rec: dict[str, Any]) -> str:
    fb = rec["speaker_feedback"]
    scale = score_scale(rec)
    avg = avg_score(rec)
    return f"""
    <article class="policy-card">
      <div class="policy-head">
        <h3>{esc(rec["listener_policy_id"])}</h3>
        <div class="avg-chip">avg {avg:.1f}/{scale}</div>
      </div>
      <div class="chat">
        <div class="bubble speaker">
          <div class="role">Speaker</div>
          <p>{esc(rec["speaker_opening"])}</p>
        </div>
        <div class="bubble listener">
          <div class="role">Listener ({esc(rec["listener_policy_id"])})</div>
          <p>{esc(rec["listener_reply"])}</p>
        </div>
        <div class="bubble speaker reaction">
          <div class="role">Speaker Reaction</div>
          <p>{esc(fb["reaction"])}</p>
          <p class="why"><strong>Why:</strong> {esc(fb["why"])}</p>
        </div>
      </div>
      <div class="scores">
        <span>understood: <strong>{esc(fb["felt_understood"])}</strong></span>
        <span>autonomy: <strong>{esc(fb["autonomy_respected"])}</strong></span>
        <span>clarity: <strong>{esc(fb["clarity_gained"])}</strong></span>
      </div>
    </article>
    """


def group_records(records: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for rec in records:
        key = (
            str(rec.get("scene_id", "")),
            str(rec.get("speaker_id", "")),
            str(rec.get("speaker_opening", "")),
        )
        grouped[key].append(rec)

    groups = list(grouped.values())
    # newest group first using latest timestamp inside group
    groups.sort(
        key=lambda g: max(str(x.get("timestamp", "")) for x in g),
        reverse=True,
    )
    for g in groups:
        g.sort(key=lambda x: str(x.get("listener_policy_id", "")))
    return groups


def render_html(groups: list[list[dict[str, Any]]]) -> str:
    sections = []
    for i, group in enumerate(groups, start=1):
        first = group[0]
        scene = esc(first.get("scene_id", ""))
        speaker = esc(first.get("speaker_id", ""))
        ts = esc(max(str(x.get("timestamp", "")) for x in group))
        cards = "\n".join(render_record(rec) for rec in group)
        sections.append(
            f"""
            <section class="group">
              <div class="group-head">
                <h2>Run {i}: {scene}</h2>
                <div class="meta">speaker={speaker} | latest={ts}</div>
              </div>
              <div class="cards">{cards}</div>
            </section>
            """
        )

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Improv Therapy Transcripts</title>
  <style>
    :root {{
      --bg: #f4f1ea;
      --panel: #fffdf8;
      --ink: #1f1b16;
      --muted: #6b6257;
      --accent: #b95c2e;
      --speaker: #f7e4d8;
      --listener: #e5edf8;
      --reaction: #efe8f7;
      --border: #d8cec0;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at top, #faf6ef, var(--bg));
      line-height: 1.5;
    }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px 16px 80px; }}
    h1 {{ margin: 0 0 8px; font-size: 32px; }}
    .sub {{ color: var(--muted); margin-bottom: 24px; }}
    .group {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 16px;
      margin-bottom: 16px;
      box-shadow: 0 5px 20px rgba(0, 0, 0, 0.04);
    }}
    .group-head h2 {{ margin: 0; font-size: 20px; }}
    .meta {{ font-size: 13px; color: var(--muted); margin-top: 2px; }}
    .cards {{
      margin-top: 14px;
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 12px;
    }}
    .policy-card {{
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 12px;
      background: #fff;
    }}
    .policy-head {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }}
    .policy-head h3 {{ margin: 0; font-size: 16px; }}
    .avg-chip {{
      border: 1px solid #dcb9a8;
      background: #ffefe7;
      color: #8f3d16;
      border-radius: 999px;
      padding: 2px 10px;
      font-size: 12px;
      font-weight: 600;
    }}
    .chat {{ display: grid; gap: 8px; }}
    .bubble {{
      border-radius: 10px;
      padding: 10px 11px;
      border: 1px solid var(--border);
    }}
    .bubble p {{ margin: 6px 0 0; white-space: pre-wrap; }}
    .speaker {{ background: var(--speaker); }}
    .listener {{ background: var(--listener); }}
    .reaction {{ background: var(--reaction); }}
    .role {{
      font-size: 11px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--muted);
      font-weight: 700;
    }}
    .why {{ font-size: 14px; }}
    .scores {{
      margin-top: 10px;
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      font-size: 13px;
    }}
    .scores span {{
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 2px 8px;
      background: #faf7f1;
    }}
  </style>
</head>
<body>
  <main class="wrap">
    <h1>Improv Therapy Transcripts</h1>
    <div class="sub">A/B policy runs rendered from <code>improv_results.jsonl</code>.</div>
    {"".join(sections)}
  </main>
</body>
</html>
"""


def main() -> None:
    args = parse_args()
    records = load_records(Path(args.input_path))
    groups = group_records(records)[: args.limit_groups]
    page = render_html(groups)
    out = Path(args.output_path)
    out.write_text(page, encoding="utf-8")
    print(f"Rendered {len(groups)} groups to {out}")


if __name__ == "__main__":
    main()
