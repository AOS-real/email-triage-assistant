# Email triage assistant with honest reasons

README prose word count: to be stated at submission.

An intelligent interactive system that sorts incoming email into "Needs you" and "Can wait", shows
the signals behind each decision, asks when it is unsure, and turns the person's corrections into
rules the person can inspect, edit and forget.

## Project status

| Part | Status |
|---|---|
| Extraction call: specification, success criteria, schema, checks | Implemented (`docs/extraction_spec.md`, `prompts/`, `triage/`) |
| Live calls to Claude Sonnet 5.5 | Implemented but not yet run (no key) |
| Recorded outputs for the ten test emails | Simulated (`recorded_runs/`, each file labelled) |
| Evaluation of the test set against criteria C1 to C6 | Implemented (`evaluate.py`, `results/`) |
| Decision rules and reason labels | Implemented (`triage/decide.py`, `docs/decision_rules.md`) |
| Guards protecting the system (input, injection, output, failure, learned rules) | Implemented (`triage/guards.py`) |
| Regression tests (28) | Implemented (`tests/`) |
| Concept design: version 1, sixteen expected errors, version 2 redesign with guards | Written (`docs/concept-design.md`, pseudocode in `docs/concept-design-algorithms.md`) |
| Web prototype: inbox, reason labels, "Can this wait?", moves with undo, rule preview and confirmation, What I've learned (edit, renew, forget, expiry), decline of out-of-scope requests, Can wait summary | Implemented (`app.py`, `triage/inbox.py`, `static/`) |
| Per-message progress for slow model calls, daily Can wait reminder, decision log | Planned (`docs/concept-design-algorithms.md`, A1, A13, A14) |

Earlier work from Phase 1 is in `phase1/` (see below).

## Technology stack

- Python standard library web server (`app.py`) and plain HTML, CSS and JavaScript (`static/`),
  with a strict Content Security Policy; the server listens on this computer only.
- Claude Sonnet 5.5 at medium effort for extracting deadlines and requests from email text
  (live mode only, not yet run). A replay mode with recorded model outputs is the default, so no API
  key is needed to inspect the work.

## Running or inspecting the work

Requires Python 3.10 or later. Replay mode needs no packages and no key.

To use the prototype:

```bash
python app.py
```

Then open http://localhost:8000. "Reset demo" restores the ten test emails. To score the
extraction and decisions:

```bash
python evaluate.py
```

This scores the ten test emails in `data/test_emails.json` against criteria C1 to C6, shows the
decision and label for each, and writes `results/extraction_v1.md`. The regression tests run with:

```bash
python -m unittest -v
```

Live mode (optional) needs `pip install anthropic` and the reviewer's
own key:

```bash
TRIAGE_MODE=live ANTHROPIC_API_KEY=<your key> python evaluate.py
```

Live mode overwrites the simulated files in `recorded_runs/` with real outputs.

## AI Assistance and Development Record

Claude Code drafted the entries in this table from the project history. I then reviewed each
entry, approving some as drafted and changing others.

| Commit | Stage | Tool | What I asked for | What came back | My decision (kept, changed or removed) and check |
|---|---|---|---|---|---|
| [`2be0402`](https://github.com/AOS-real/email-triage-assistant/commit/2be0402) | Planning | Claude Code (Claude Opus 5.5) | A careful reading of the lab work on the email-triage assistant (`phase1/`), and an account of what it understood | An accurate summary of the problem, the artefacts and the open issues | Kept. I checked the summary against the Lab 3 specification before moving on |
| [`2be0402`](https://github.com/AOS-real/email-triage-assistant/commit/2be0402) | Design | Claude Code (Claude Opus 5.5) | Possible designs for a prototype, compared | Three options (web prototype, Python simulation, screen walkthrough), with the web prototype recommended and Claude Haiku 5.5 suggested for extraction | Changed. I compared the options against the marking criteria and chose the recommended web prototype, but replaced the suggested Claude Haiku 5.5 with Claude Sonnet 5.5 at medium effort for extraction |
| [`0edb8c8`](https://github.com/AOS-real/email-triage-assistant/commit/0edb8c8) | Extraction | Claude Code (Claude Opus 5.5) | The extraction call, with the success criteria written first, then a task specification, a schema with checks, ten test emails and replay files | The specification, the code and an evaluation script. No API key was available, so the replay files are simulated, and two of them contain deliberate errors to test the checks | Kept, and I labelled the simulated files as such. The evaluation run showed that the checks caught the reformatted date in E05 automatically, but the meeting time in E10 passed them and was still wrong |
| [`3740fa8`](https://github.com/AOS-real/email-triage-assistant/commit/3740fa8) | Decision rules | Claude Code (Claude Opus 5.5) | Decision rules, reason labels, and guards to protect the system itself | Six ordered rules, labels listing what was used and what was not, five guards (input length, injected instructions, output checks, model failure and learned rules) and 12 regression tests | Changed. I allowed guards beyond the original plan. The E10 error is now fixed in the rules: a time counts as a deadline only when the email asks for action. I corrected the expected result for E05 to Needs you, so its "Not sure" counts as a safe fallback and not as a pass. I ran the tests and the evaluation myself |
| [`7a5a0ab`](https://github.com/AOS-real/email-triage-assistant/commit/7a5a0ab) | Concept design | Claude Code (Claude Opus 5.5) | A concept design to be written before the web interface, with its expected errors and a redesign that avoids them using guards, as a design document and a separate file of pseudocode | Version 1 of the concept, sixteen expected errors placed on the conceptual spine with their type and cost, version 2 with an error-to-guard map, and fourteen algorithms, each marked implemented or planned | Changed the plan. I chose a concept design before the interface so that the expected errors shape what is built. I checked that each implemented algorithm matches the code |
| [`e460530`](https://github.com/AOS-real/email-triage-assistant/commit/e460530) | Prototype | Claude Code (Claude Opus 5.5) | The working web prototype, built from the planned algorithms of the concept design | A local web inbox with reason labels, "Can this wait?", moves with undo, a rule preview that must be confirmed, a learned-rules panel with edit, renew, forget and expiry, a decline for out-of-scope requests and a Can wait summary, together with 16 new tests (28 in total) | Changed. Building it showed that the deadline and sender-type rules were redundant or too broad, so rules are now learned only about one sender. The undo button also stays until the next move. Both changes are recorded in the algorithms file. I used every interaction in the browser and ran the tests myself |
| pending | Diagram and storyboards | Claude Code (Claude Opus 5.5) | A system diagram showing components, flows and the status of each part, and storyboards of the interaction | A diagram that labels each component as implemented, simulated or planned and matches the code modules, and three four-frame storyboards built from automated screenshots of the running prototype, with each frame marking who acts | Kept. Two frames were first too small to read, so they were cropped tighter. I checked that the diagram matches the code and that its statuses match the README |

## Additional files

- `report/figures/`: the system diagram (`system-diagram.svg`, with a PNG render) and three
  storyboards (`storyboard-1-reasons.png`, `storyboard-2-unsure.png`,
  `storyboard-3-learning.png`). Every storyboard frame is a screenshot of the running
  prototype, taken automatically with Playwright; the frames are in `report/figures/frames/`.
- `phase1/`: reused work from Phase 1 (Labs 1 to 3): the problem statement and related-work map,
  the interaction loop and storyboards, the specification, system path diagrams v1 and v2, the
  Python simulation and its outputs, and the Phase 1 prompt log. It is kept unchanged as the
  starting point of this project.

## API keys

No key is stored in this repository. For live mode, a reviewer supplies their own key in the
`ANTHROPIC_API_KEY` environment variable (instructions to follow).
