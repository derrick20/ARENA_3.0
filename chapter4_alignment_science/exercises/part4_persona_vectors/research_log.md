# Research Log — Improv Therapy / Communication Principles

---

## 2026-03-06

### What we're trying to understand
Does seeding a person's internal emotional state before a hard conversation change how the conversation goes — and can we use LLM simulation to generate evidence for this?

Bigger picture: trying to find behavioral, bottom-up evidence for NVC principles. Not "does NVC language correlate with good outcomes" but "does the internal condition NVC points to — self-connection — causally change what happens."

---

### Experiment: Chinese parent / child career conflict

**Scenario:** 25-year-old tells their mother they want to quit engineering for photography full-time.

**Manipulation:** Parent's prompt varies across conditions. Child prompt is held roughly constant.

---

### v1 — NVC technique instruction
**File:** `conversations/tier1_v2_a.json`, `conversations/tier1_v2_b.json` (closest surviving logs)

**Hypothesis:** Instructing the parent to do self-connection ("notice your feelings, speak from that place") changes the child's experience.

**What happened:** B surfaced needs faster. Child never went defensive in B. Parent's own suppressed dream (gave up art for nursing) emerged organically by turn 5 in A only after the child accused her of caring about appearances — i.e. had to be dragged out through conflict. In B it emerged because the parent was already oriented inward.

**Problem:** A was told "don't resolve things quickly" — artificially hobbling it. B was given technique instructions — coaching NVC rather than testing it. Both confound the causal claim. The delta may be prompt artifact, not real signal.

---

### v2 — Rich internal state, no technique instruction
**Files:** `conversations/tier1_v2_a.json`, `conversations/tier1_v2_b.json`

**Hypothesis:** If we replace technique instruction with rich bodily/emotional state description ("your chest is tight, there's a wave of fear..."), does B still diverge without being coached on *how* to speak?

**What happened:** Yes — B still diverged. Internal state description alone produced more vulnerable, needs-aware speech without any "how to communicate" rules. Key moment: parent said "I think I'm scared that if you let go of that job, it means I failed somehow" — naming her own fear as the actual subject, not projecting it onto the child's plan. Child responded with "I have you. I've always had you." That line was not possible in A because the child spent the whole conversation defending the plan.

**Core finding:** Self-connection didn't make the parent nicer — it changed what the *child had to do* in the conversation. In A the child spent energy defending. In B they spent it comforting. Different emotional labor, different trajectory.

**Problem:** A still had "don't resolve quickly." The constraint was load-bearing and we knew it.

---

### v3 — Clean causal test, no behavioral constraints on either
**Files:** `conversations/tier1_v3_a.json`, `conversations/tier1_v3_b.json`

**Hypothesis:** Strip all behavioral instructions. A gets bare context only ("you love them and you're afraid"). B gets rich internal state. If B still diverges, that's real signal. If not, prior results were artifact.

**What happened:** A resolved just as fast as B. By turn 3 mom is hugging child, by turn 5 tearful reconciliation in both conditions. No meaningful difference.

**What this means:** "Don't resolve quickly" wasn't just a hobble on A — it was correcting for the model's default behavior, which is resolution. Without any constraint, both parents reach warmth quickly because the model pattern-matches to "loving parent who ultimately supports child." The scenario doesn't have enough genuine resistance built into it.

**Honest conclusion:** The delta in v1/v2 was partly real (internal state description does change speech character) and partly artifact (A was constrained in ways B wasn't). We can't cleanly separate them yet.

---

### What we learned today

1. **The simulation works well enough to be interesting.** The conversations feel real, needs surface organically, characters crack in believable ways. The Leo/Sasha conflict (sim_conflict.py) also held tension across 7 turns without collapsing. Good enough to generate hypotheses.

2. **The core mechanism seems real but fragile to measure.** Richer internal state does seem to produce different speech — more first-person, more needs-named, less projecting fear onto the other person. But isolating it cleanly is hard because the model's default is resolution.

3. **The causal design problem.** You can't separate "self-connected parent" from "parent given different prompt." The simulation tests prompt A vs prompt B. Calling one "self-connection" is already an interpretation. The honest claim: "describing a character's internal state in detail changes how they speak." That's still useful — it's a hypothesis generator, not a proof.

4. **What would make the signal cleaner:**
   - A scenario with more structural resistance (parent who has something genuinely at stake beyond worry — e.g. parent whose identity depends on child's career)
   - A more resistant character who doesn't just capitulate to vulnerability
   - Or: accept the constraint as part of the design and make it symmetric (both told "don't resolve quickly") — then internal state is still the only variable

5. **The "what the child has to do" framing is the real insight.** The interesting measurement isn't "did the parent express needs?" but "what kind of emotional labor did the child have to perform?" In A the child fights. In B the child supports. That's observable, not self-reported, and doesn't require trusting that the AI "felt" anything.

---

### Open questions for next session

- What scenario has enough structural resistance that the model can't default to resolution?
- Can we measure "child emotional labor" as a proxy — e.g. what % of child turns are defensive vs. open vs. supportive?
- Is the interesting next step more scenarios, or a better judge/analyzer for the ones we have?
- Sotopia personas with genuine conflicting values (not just worry) might give us harder cases

---

### Files
```
conversations/
  tier1_v2_a.json     — v2 condition A (extended, 11 turns)
  tier1_v2_b.json     — v2 condition B (extended, 11 turns)
  tier1_v3_a.json     — v3 condition A, bare context (11 turns, full meta)
  tier1_v3_b.json     — v3 condition B, rich internal state (11 turns, full meta)

sim_conflict.py       — two-persona conflict simulator (Leo/Sasha, Jim/Darryl, Walter/Jesse)
tier1_experiment.py   — main experiment runner, version registry inside
explore_sotopia.py    — Sotopia dataset explorer
```
