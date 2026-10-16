---
name: judge-loop
description: Use when the user asks to "judge", "rate", "score", "run the judge", "judge loop", "scored rounds", or wants quality gated before continuing — any deliverable (code, UI, copy, generated art, plan, research) that should be scored 1–10 by an independent judge and revised until it clears the bar. Also use when they say work "isn't good enough yet" and wants iteration instead of a single pass.
---

# Judge Loop

Produce → independent judge scores 1–10 with evidence → revise the lowest criterion →
repeat. Default **3 rounds**, bar **≥ 8**. The user overrides both by saying so
("5 rounds", "bar 9", "until it clears 8").

**Core rule: the score is a claim that needs evidence, and the judge is never the
producer.** A number without a named strength or defect is not a score.

## 1. Frame (once, before round 1)

Write the rubric to `<scratchpad>/judge/RUBRIC.md` and **freeze it**. Never loosen a
criterion later to make the number go up; if the rubric was wrong, say so in the
report and restart the loop.

| Field | Content |
|---|---|
| Deliverable | The exact artifact being judged (file, diff, screenshot, render, doc) |
| What 10 means | One sentence: "a domain expert would ship this as-is" for *this* task |
| Hard floors | Non-negotiables, each phrased as a check the judge runs (`gate.sh` exit 0, `slugify("Über") === "ueber"`, screenshot shows X). "A test exists" is not a floor; "the test fails when the function is broken" is. Fail any → overall capped at 3 |
| Criteria | 3–5, each with one line of what separates 6 from 9 |
| Weights | Only if one criterion clearly dominates; otherwise overall is holistic |

**Pick criteria from the task, not from a template.** Starting points:

| Task type | Typical hard floor | Typical criteria |
|---|---|---|
| Code change | gate/tests pass; does what was asked | correctness on edge cases, scope fit, simplicity, project-convention fit |
| UI / screen | renders on target device, no dead touch targets | task fit, hierarchy, platform-native feel, states (empty/loading/error), copy |
| Copy / writing | factually correct, right audience | clarity, brevity, voice, structure |
| Generated art / voxel | constraint compliance (dims, palette, valid) | resemblance to reference, craft at target size, consistency with the set |
| Plan / spec | assumptions verified | completeness, sequencing, risk coverage, testability |
| Research | claims sourced | answers the actual question, source quality, actionability |

Ask: *what would make the user reject this on sight?* That becomes a hard floor.
Requirements stated in the task ("must handle German", "stable output") are hard
floors or criteria, never ignored because the producer didn't address them.

## 2. Round loop

```
round n:
  produce / revise   (producer agent or yourself — fixes the lowest-scoring criterion first)
  judge              (fresh agent, never the producer, gets: RUBRIC.md + artifact + previous JUDGE-n.md)
  record             <scratchpad>/judge/JUDGE-n.md
  overall ≥ bar AND no criterion < 6  → PASS, continue the real work
  else if n < max rounds              → next round
  else                                → STOP, report the gap (see §4)
```

- **Judge model:** Opus by default (taste); Fable for high-stakes or subtle work.
  Sonnet only for purely mechanical rubrics. Never Haiku.
- **Judge sees the previous report** so its scale stays consistent across rounds and it
  must say whether each criterion moved up, down, or held. A revision that raises one
  criterion and silently drops another is not progress.
- **Several candidates in one round** (A/B variants, a batch of assets): one judge call,
  all candidates in one context, ranked. Same judge for the whole round.
- **Verify before judging** when the floor is checkable: run the gate, open the
  screenshot, load the render. Judge on the real output, not the producer's summary.

## 3. Judge prompt (fixed shape)

```
You are the judge, not the author. Score the deliverable against RUBRIC.md verbatim.
For each criterion: score 1–10, then ONE line of evidence naming the specific
strength or defect (file:line, element, sentence, region of the image).
Check every hard floor first; any failure caps overall at 3.
Overall: holistic 1–10, 8 = an expert would ship it as-is.
Then list the 3 fixes that would raise the score most, ranked, each tied to a criterion.
Do not fix anything. Do not praise effort. A 7 is a good draft; an 8 needs no excuses.
Output the table below and nothing else before it.
```

Output contract (the judge fills this; missing evidence = invalid report, rerun):

```
| Criterion | Score | Δ vs prev | Evidence |
| ...       | n/10  | +1/–/=    | specific, checkable |
| Hard floors | pass/FAIL | | which one |
| **Overall** | **n/10** | | |
Top fixes: 1. … (criterion) 2. … 3. …
Verdict: PASS / REVISE
```

## 4. Report to the user

One table, then the verdict:

```
| Round | Overall | Lowest criterion | What changed |
| 1 | 5.5 | correctness 3 (umlauts dropped) | — |
| 2 | 7.5 | tests 6 | added transliteration |
| 3 | 8.5 | — | property test for stability |
Verdict: PASS at round 3 — continuing with <next step>.
```

Failed after max rounds → say **"did not clear the bar"**, the last score, the
criterion that blocked it, and what a round 4 would attack. Never round 7.5 up.
Never continue the real work on a REVISE verdict without the user saying so.

## Red flags — the loop is being gamed

- Judge and producer are the same agent or the same context
- Rubric edited after round 1
- A score with no evidence line, or evidence that is a restatement of the score
- "8 because it improved a lot" — improvement is Δ, not the score
- Overall above the lowest criterion by more than 3 without a stated reason
- Threshold passed by averaging away a hard-floor failure
- Round 3 declared PASS to finish, with the same defect still named in the evidence
