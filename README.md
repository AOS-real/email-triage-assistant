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
| Decision rules, reason labels, web interface, learned rules | Not started |

Earlier work from Phase 1 is in `phase1/` (see below).

## Technology stack

- Python standard library web server and plain HTML (planned).
- Claude Sonnet 5.5 at medium effort for extracting deadlines and requests from email text
  (planned, live mode only). A replay mode with recorded model outputs is the default, so no API
  key is needed to inspect the work.

## Running or inspecting the work

Requires Python 3.10 or later. Replay mode needs no packages and no key.

```bash
python evaluate.py
```

This scores the ten test emails in `data/test_emails.json` against criteria C1 to C6 and writes
`results/extraction_v1.md`. Live mode (optional) needs `pip install anthropic` and the reviewer's
own key:

```bash
TRIAGE_MODE=live ANTHROPIC_API_KEY=<your key> python evaluate.py
```

Live mode overwrites the simulated files in `recorded_runs/` with real outputs.

## Development record

To be written by stage, with links to the relevant commits.

## AI assistance

Claude Code drafted the entries in this table from the project history. I then reviewed each
entry, approving some as drafted and changing others.

| Stage | Tool | What I asked for | What came back | My decision (kept, changed or removed) and check |
|---|---|---|---|---|
| Planning | Claude Code (Claude Opus 5.5) | A careful reading of the lab work on the email-triage assistant (`phase1/`), and an account of what it understood | An accurate summary of the problem, the artefacts and the open issues | Kept. I checked the summary against the Lab 3 specification before moving on |
| Design | Claude Code (Claude Opus 5.5) | Possible designs for a prototype, compared | Three options (web prototype, Python simulation, screen walkthrough), with the web prototype recommended and Claude Haiku 5.5 suggested for extraction | Changed. I compared the options against the marking criteria and chose the recommended web prototype, but replaced the suggested Claude Haiku 5.5 with Claude Sonnet 5.5 at medium effort for extraction |
| Repository | Claude Code (Claude Opus 5.5) | The relevant lab work copied into `phase1/`, a `.gitignore` with recommended exclusions, and a README with the sections below | The files, created as requested | Kept. I checked that `phase1/` holds no personal data and that the README matches the brief |
| Extraction | Claude Code (Claude Opus 5.5) | The extraction call, with the success criteria written first, then a task specification, a schema with checks, ten test emails and replay files | The specification, the code and an evaluation script. No API key was available, so the replay files are simulated, and two of them contain deliberate errors to test the checks | Kept, and I labelled the simulated files as such. The evaluation run showed that the checks caught the reformatted date in E05 automatically, but the meeting time in E10 passed them and was still wrong |

## Additional files

- `phase1/`: reused work from Phase 1 (Labs 1 to 3): the problem statement and related-work map,
  the interaction loop and storyboards, the specification, system path diagrams v1 and v2, the
  Python simulation and its outputs, and the Phase 1 prompt log. It is kept unchanged as the
  starting point of this project.

## API keys

No key is stored in this repository. For live mode, a reviewer supplies their own key in the
`ANTHROPIC_API_KEY` environment variable (instructions to follow).
