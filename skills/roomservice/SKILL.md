---
name: roomservice
description: Clean up a repo so humans and agents find things instantly — sort files into a structure that makes sense, delete dead files, split oversized files and cut needless complexity, and write a MAP.md "building plan" (Gebäudeplan / Fluchtweg) that tells an agent exactly where to make each kind of change. Use when the user says "roomservice", "/roomservice", "räum das Repo auf", "aufräumen", "sort the repo", "clean up the repo", "the repo is a mess", "make it navigable for agents", "write a map", or when files have grown past ~700 lines. Proposes every move and deletion first; changes nothing until approved; keeps the project's tests green.
argument-hint: "[path, default: current repo] [focus, e.g. 'map only' or 'complexity only']"
---

# Roomservice

Leave the repo like a well-run building: every room labelled, nothing in the hallways, and a plan by the door. The test of success is simple: a fresh agent reading only `MAP.md` can name the file to edit for any common change without searching.

Work in four passes, measured before and after. Each pass ends with a proposal the user approves before anything moves.

## 0. Ground rules

- The repo must be under git with a clean working tree (or the user's changes committed first). Every pass is its own commit, so any one can be reverted.
- Find the project's gate before touching anything: `gate.sh`, `npm test`, `pnpm test`, `pytest`, `make test`, or what `CLAUDE.md` / `ROADMAP.md` names. Run it once to get a baseline. If it's already red, say so and only fix what you break.
- Moves use `git mv`, never copy-and-delete. After every batch of moves, update imports and references, then run the gate. Red means fix or revert before continuing.
- Never delete what you can't prove is dead. "Nothing imports it" is a candidate, not proof: check scripts in `package.json`, CI workflows, Dockerfiles, docs, cron entries, and dynamic imports.

## 1. Survey and baseline

```sh
python3 -I "<this skill's directory>/scripts/survey.py" <repo> --out ~/.claude/roomservice/<repo-name>/<YYYY-MM-DD>-before.json
```

It returns: file and line counts per top-level directory, `too_big` code files (`split` at 700+ lines, `watch` at 400+), `root_clutter` (stray files at the root), `orphan_candidates` (code whose name appears nowhere else), exact `duplicates`, and `map` drift (paths in `MAP.md` that no longer exist, top-level folders it doesn't mention). It reads `git ls-files`, so ignored files never show up.

It also computes a **chaos score** (0 = tidy, 100 = chaos) from weighted parts: share of code in oversized files, the biggest file, the most crowded folder, root clutter, orphans, duplicates, and a missing or stale map. The score is a trend line for the same repo, not a grade across repos.

Then read the tree yourself (`git ls-files | head -300`, the README, any `CLAUDE.md`/`AGENTS.md`) to understand what the project is and how it's organised today. The script finds symptoms; the structure needs judgment.

## 1b. Navigation benchmark (before)

This measures how fast an agent arriving cold finds where to make a change. Run it before anything moves.

1. Write 8 questions of the form "Where would you change … ?" that a real contributor would ask, each with the file (or files) that is the right answer. Mix them: 3 common changes, 2 "where does this bug live", 2 "where is this setting or config", 1 change that touches several places. Take them from the README, recent commits (`git log --oneline -40`) and open issues, so they reflect real work. Save to `~/.claude/roomservice/<repo-name>/<date>-quiz.json` as `[{"q": "...", "answer": ["path"]}]`.
2. For each question, spawn a **fresh** subagent (`Explore`, model `sonnet`), all 8 in parallel, with exactly this prompt and nothing else: *"In the repo at `<path>`, find the file you would edit to: `<q>`. Search as you normally would. Reply with only the path(s), one per line."*
3. From each result, record: correct (the answer contains an expected path), tool calls, tokens, and duration, as shown in the agent's result. Save as `<date>-nav-before.json`.

The baseline is the evidence; skip it only if the user asks for a quick run.

## 1c. The plan file (for repos too big for one session)

Write the work as a checklist in `~/.claude/roomservice/<repo-name>/plan.md`: one line per proposal (a batch of moves, one file split, the map), each tagged **[auto]** (mechanical, proven safe by the gate: moves with references updated, re-export splits) or **[decide]** (needs the user: deletions, a new folder scheme, anything that changes behaviour or public paths). Work at most one area per session on a large repo, tick lines off with the commit sha, and start each later session from this file. Small repos can do everything in one go.

## 2. Sort (Umzugsplan)

Design the target structure from what the code *does*, not from file types. Good structure:

- follows the conventions of the framework already in use (Next.js `app/`, Python `src/<pkg>/`, monorepo `apps/` + `packages/`); don't invent a new scheme over a known one;
- groups by feature or domain once a folder passes ~15 files of mixed purpose;
- keeps the root to entry docs and config: README, LICENSE, CLAUDE.md, MAP.md, package/project files. Everything else lives in a folder;
- separates source, tests, scripts, docs and generated output. Generated output belongs in `.gitignore`, not in git;
- puts one-off scripts and experiments in `scripts/` or deletes them; dated specs and old plans go to `docs/archive/`.

Present the plan as a table: `current path → new path → why`, plus a `delete` list, each with its evidence. Keep it to moves that make a real difference: ten good moves beat eighty cosmetic ones. Wait for approval, apply in batches, run the gate after each, commit (`roomservice: sort <area>`).

## 3. Simplify (Komplexität)

For every `too_big` file and anything else that reads as tangled:

1. Read it. Find the seams: separate responsibilities, a cluster of helpers, a big lookup table, a section that only one caller uses.
2. Split along those seams into files with names that say what they hold. A 1000-line file becomes three to five focused files, not twenty tiny ones. Keep the public import path working (re-export from the old module) unless the user wants callers updated.
3. While inside, flag needless complexity: dead branches and unused exports, wrappers that only forward a call, abstractions with one implementation, config for values that never change, copy-pasted blocks that should be one function, hand-rolled versions of something the standard library or an existing dependency does.

Propose per file: the split (new files and what moves into each) and the deletions. Behaviour must not change; this pass is structure only. Apply after approval, gate, commit (`roomservice: split <file>`). Leave real bugs you notice in the report rather than fixing them silently.

Limits that keep files easy for agents: aim for under 400 lines per file, treat 700 as the point where splitting is due, and keep functions under ~60 lines. Tests may run longer when they're a flat list of cases.

## 4. Map (Gebäudeplan)

Write `MAP.md` at the repo root. It's for an agent arriving cold, so it's about *where to change things*, not a tour. The map is an **index, not a store**: it points at files and gives a one-line gist; it never restates what the code, README or specs already say, so it can't drift out of sync with them. Keep it under ~120 lines; it must stay true, so only write what the code shows.

```markdown
# MAP — <project>

<One sentence: what this is. One line: how to run it, how to test it (the gate).>

## Layout
- `apps/web/` — Next.js site. Routes in `app/`, UI components in `components/`.
- `packages/engine/src/` — the build engine; pure TypeScript, no I/O.
- ...one line per folder that matters, with its key files in backticks.

## Where to change things
| To change… | Edit | Then check |
|---|---|---|
| a page's layout | `apps/web/app/<route>/page.tsx` | `pnpm --filter web test` |
| how slopes are placed | `packages/engine/src/slopes.ts` | `pnpm --filter engine test` |
| ... 8–15 rows for the most common changes |

## Rules of the house
- <Invariants a newcomer would break: generated files not to edit, a boundary between packages, naming conventions.>

## Danger zones
- <Files that are fragile, slow to test, or touch production (migrations, deploy config, secrets handling).>

## Not mapped yet
- <Areas you looked at but couldn't pin down honestly (unclear ownership, legacy code nobody calls, generated code). Better an admitted gap than a guessed row.>

## Kept on purpose
- <Things that look like clutter but stay, with why (seasonal script, vendored file, fixture). Re-runs don't re-flag these.>
```

Wrap every path in backticks: the survey script checks those paths for drift next time. Then add one line to `CLAUDE.md` (and `AGENTS.md` if the repo has one), creating it if missing: `Read MAP.md first: it says where each kind of change lives.` For big subfolders (30+ files or their own domain), a short `README.md` in that folder with the same "where to change" table is worth it; don't scatter more map files than that.

Verify the map: pick three rows of the "Where to change" table and confirm the named file really holds that logic. Commit (`roomservice: map`).

## 5. Measure again

1. Survey again into `<date>-after.json`, then print the comparison table:
   ```sh
   python3 -I "<this skill's directory>/scripts/survey.py" --compare <before.json> <after.json>
   ```
2. Re-run the navigation benchmark with the **same 8 questions**. Expected answers follow the moves: map each old path to its new one with `git diff --name-status -M <baseline-sha> HEAD`; for split files, either piece that holds the logic counts. Same subagent type, model and prompt as before. Save `<date>-nav-after.json`.
3. Build the navigation table: per question, before → after for correct, tool calls, and seconds; then totals and averages. Speed-up = average tool calls before ÷ after.

If a number got worse, say so and why. A worse score is a finding, not something to hide.

## 6. Report

End with a short summary in chat: the chaos table (before → after), the navigation table (accuracy, average tool calls, average seconds, speed-up), what moved, what was deleted, which files were split (before → after line counts), the gate result before and after, and anything left for later (suspected bugs, risky deletions you held back). On a repo with a `ROADMAP.md`, add leftovers there instead of losing them.

## Re-runs

Earlier surveys, quizzes and the plan file live in `~/.claude/roomservice/<repo-name>/`. Re-use the last quiz (with paths updated) so the navigation numbers stay comparable across runs, and show the chaos score's trend. On a repo that already has `MAP.md`, start with the survey's `map` section: fix stale paths and unmapped folders first, then only look at what changed since the map's last commit (`git log --since` on MAP.md). Roomservice should get cheaper every time.
