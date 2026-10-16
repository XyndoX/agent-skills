---
name: voxel-artist-loop
description: Use when commissioning an agent to build visual game art — voxel characters, scenes, dioramas, UI-rendered 3D — or any generated artifact where tests can pass while the output looks wrong to a human.
---

# Voxel Artist Loop

## Overview

Green tests do not mean good art. In the project that produced this skill, every artist agent passed 100% of its tests while shipping a wolf that read as "a human in a purple morphsuit" and wings that read as earmuffs. **The render is the deliverable; the screenshot review IS the test.** Spend the strongest model you have on the artist (the top tier produced a step-change over the next one down on the same prompts), and never commit art you haven't looked at yourself.

## The Loop

1. **Reference first.** Give the agent an actual image file (agents that can read images will look at it) and name the bar: "match this pack". Order it to study the reference BEFORE reading code. No reference → agents anchor on the existing (bad) art.
2. **Contract + fences.** State the hard invariants of your engine (for example: limbs stay inside their columns, feet at y=0, palette-only colors, no module-level state) and exact file ownership. Shared files are append-only.
3. **Mandatory look-iterate.** The prompt must require: screenshot → look at the screenshot → compare to reference → iterate, with an expected round count ("expect 2–4 rounds"). Say explicitly: *"a green test with an ugly character is a failure."*
4. **Report format** demanded up front: files + net lines, per-item voxel/size budgets, iteration log (what changed each round), palette/shared-file additions, gate output lines, and at least 5 enumerated mismatches vs the reference per round.
5. **Orchestrator reviews the pixels.** Open every final render yourself before committing. Send delta feedback naming the exact defect and the fix direction ("fur must dominate — garment becomes a torso-only vest").

## Prompt ingredients that mattered

- Resolution ceiling stated as fact: detail is capped by grid density; artists cannot stamp a monocle into a 7-voxel face. Fix the engine headroom before blaming artistry.
- Palette before modeling: all colors from a shared palette module; artists may append ramps, never edit existing exports.
- Perf budget as a number ("<20k voxels per figure", "60 ms mesh time"), not "keep it fast".
- Poses/builds sweep: require a robustness pass across every body build, pose and animation frame — it caught adornments floating mid-air in one pose that all default-pose screenshots missed.
- Gates before renders: a clearance check (no part intersects another across all clips) and a perf check must pass before any render is shown.
- Determinism: generators use hash-based noise, never `Math.random`, so re-running a generator gives the same model.

## Observed failures this skill counters

| Failure (verbatim from baseline runs) | Counter |
|---|---|
| All tests green, wolf = "morphsuit with a wolf head" | Orchestrator opens renders; visual sign-off gates commit |
| Wings authored below the shoulder line vanished ("earmuffs") — the partition was x-column only, no z-check | Put geometry constraints IN the contract; artists document new ones they discover |
| A top-level import of shared rig state broke the whole module graph (circular import) | "Types only at module top level" in every model-file prompt |
| Two agents appending one palette file | Append-only rule + "on write conflict re-read and re-apply" |
| Agent report crossed orchestrator feedback in flight | Compare file mtimes/renders before accepting "already fixed"; re-send outstanding items as a delta list |
| Agent idle without report | Demand the report; silence is not success |

## Lessons from a full art audit

- **Render-pipeline parity first.** Judge art only in the renderer that ships. An unlit, fixed-shade, black-background stage made a purchased pro asset pack look as muddy as home-made boxes; a lit path lifted every model by about a point. Fix the stage before another art round: real lights (Lambert + hemisphere + a warm front-top key), a soft contact shadow, neutral tone mapping, a gradient backdrop.
- **Procedural boxes plateau around 5/10.** Seven rounds of parametric painter code never passed 5. Every charming voxel humanoid (Crossy Road, Kenney, Minecraft, commercial packs) is hand-authored geometry; code only picks parts, swaps palette and places them. Commission hand-made `.vox` parts, not more painter tweaks.
- **Score against a fixed bar.** 0–10 where a reference asset's store render = 7; re-score ALL models after each renderer or art change, in a table. "Looks better" without a number is not a review (see the `judge-loop` skill).
- **Measured sculpt rules for a small voxel human:** 10-wide face + 1-voxel hair shell; nose 1 voxel proud with its own shaded side; eyes 3×1 white/pupil/white with a 2-voxel bridge; 3×1 brows 2 rows up; 4-wide neck with 2–3 skin rows visible; garments 1 voxel proud with a 1-voxel dark gap; limbs detached at joints. Hair and headwear never intersect: headwear trims the hair under its band, and the full hair × headwear matrix is tested, not spot-checked.

## Red flags — stop and review the pixels

- "Tests pass, committing" without opening a render
- Accepting a report's self-assessment of visual quality
- Reference described in words instead of an image file
- Artist prompt without an iteration requirement or round count
