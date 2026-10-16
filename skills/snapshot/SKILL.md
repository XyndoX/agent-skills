---
name: snapshot
description: Take one slice of the software — a feature, flow, screen, endpoint, CLI command or module — and test it deeply the way real humans use and misuse it, then freeze that behaviour into lasting tests. Explores it hands-on (real UI, real API, real CLI), writes scenario tests in the project's own framework, captures golden snapshots of outputs, and reports the bugs found. Use when the user says "snapshot", "/snapshot", "test this part deeply", "human tests", "teste das richtig", "test it like a real user would", "lock this feature down", "make sure X really works", or before refactoring a part that has thin tests. For a whole-app product verdict use hyper-user-tester instead.
argument-hint: "<the slice, e.g. 'checkout flow', 'apps/web/app/sets/[id]', 'the export command'>"
---

# Snapshot

Pick one slice, understand it completely, use it like ten different people would, and leave behind tests that keep it working. The deliverable is a set of committed tests that a human would recognise as "yes, that's how people really use this", plus a short list of what broke.

A "human test" is a test written from a person's intent, not from the code's structure: *"a returning user pastes a URL with trailing spaces and hits enter twice"*, not *"test parseUrl"*. It goes through the same surface the person uses (the page, the endpoint, the command), uses realistic data, and checks what the person would check: what they see, what got saved, what they can do next.

## 1. Frame the slice

Pin down exactly what's in scope: the entry point (route, endpoint, command, public function), the files behind it (trace from the entry point inward; `MAP.md` helps if the repo has one), its inputs, its outputs and side effects (DB rows, files, emails, network calls). Write this as five lines at most and show it to the user if the slice was vague.

Find the project's test setup and gate (`npm test`, `pytest`, `gate.sh`, Playwright, Vitest, XCTest…) and run the existing tests for the slice to get a baseline. Note how thin or thick they are; that decides how much to write.

## 2. Cast the humans

List 5–8 people who use this slice, each with a goal and a habit, for example:

- **First-timer**: no data yet, reads nothing, clicks the most prominent thing.
- **Power user**: lots of data, keyboard shortcuts, does it fast and repeatedly.
- **Distracted user**: starts, leaves mid-way, comes back later or in another tab, double-clicks, hits back.
- **Messy input**: pastes from Word or Excel, trailing spaces, emoji, umlauts, very long text, empty fields, wrong formats, the wrong file type.
- **Bad connection or slow machine**: slow responses, a request that fails half-way, a retry.
- **Wrong person**: logged out, another user's ID in the URL, an expired session, missing permissions.
- **Edge of the world**: zero items, one item, the maximum, dates around midnight, time zones, leap years, locale (German decimals `1,5`), dark mode, phone width.

Keep the ones that fit the slice; add the ones specific to the domain.

## 3. Explore by hand first

Before writing any test, use the slice as each person, for real:

- UI: drive a real browser (chrome-devtools MCP, Playwright, or claude-in-chrome) at desktop and phone width, screenshot what each person sees at the key moments.
- API: real requests (`curl`, httpie) against the running dev server, including malformed and unauthorised ones.
- CLI or library: run it with real-looking arguments and files.

Write down every surprise: crashes, wrong output, confusing messages, silent failures, things that are slow, states you can't get out of. These become the first tests and the bug list. Don't fix anything yet.

## 4. Write the tests

Write the scenarios in the project's own framework and conventions, next to its existing tests. Don't introduce a new test framework; if the slice has a UI and the project has no browser-test setup, ask before adding one.

- **One test per human scenario**, named as the sentence it proves: `"returning user who pastes a URL with spaces still lands on the set page"`.
- **Through the real surface** where the project allows it (route handler, rendered component, CLI entry), with the fewest mocks possible. Mock only what's outside the slice: payment providers, email, third-party APIs, the clock.
- **Realistic fixtures**: data that looks like production (real-looking names, German text, long lists), built in one small fixture file, never 200 lines of inline JSON.
- **Check what the human checks**: visible text and state, saved records, the next possible action, the error message they'd read. Not internal function calls.
- **Golden snapshots** for outputs that are large and stable (rendered HTML fragments, generated files, API response bodies, CLI output): use the framework's snapshot feature or a `__snapshots__/` file, with volatile parts (IDs, timestamps) normalised first. Snapshots freeze *current* behaviour; review each one by eye before committing, because a snapshot of a bug protects the bug.
- **Known bugs** from step 3 get a test that asserts the correct behaviour, marked as expected to fail (`test.fails`, `xfail`, `skip` with the bug in the reason) so the suite stays green and the bug stays visible.

Aim for depth over breadth: 10–25 strong scenarios for one slice beat 100 shallow ones.

## 5. Verify the net

- Run the gate: everything green except the marked known-bug tests.
- Prove the tests bite: break the slice on purpose in two or three places (flip a condition, drop a field, change a message), confirm tests fail with readable messages, then revert. A test that never fails is decoration.
- Check runtime: the new tests shouldn't slow the gate noticeably. Move slow browser scenarios to the project's e2e suite if it has one.

Commit the tests on their own (`snapshot: <slice> human tests`).

## 6. Report

Short, in chat:

1. **Slice**: the five-line frame.
2. **Bugs found**: ranked by user pain, each `[severity] scenario — what happened — what should happen`, with the failing test's name and screenshot refs.
3. **Net**: number of scenarios, which humans they cover, snapshot files written, the mutation check result, gate before and after.
4. **Not covered**: what couldn't be tested here (real payments, push delivery, device hardware) and why.

Then offer to fix the bugs one at a time, each fix turning its expected-failure test green.
