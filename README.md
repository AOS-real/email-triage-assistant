# Email triage assistant with honest reasons

README prose word count: to be stated at submission.

An intelligent interactive system that sorts incoming email into "Needs you" and "Can wait", shows
the signals behind each decision, asks when it is unsure, and turns the person's corrections into
rules the person can inspect, edit and forget.

## Project status

Set-up stage. Nothing is implemented yet. Earlier work from Phase 1 is in `phase1/` (see below).

## Technology stack

- Python standard library web server and plain HTML (planned).
- Claude Sonnet 5.5 at medium effort for extracting deadlines and requests from email text
  (planned, live mode only). A replay mode with recorded model outputs is the default, so no API
  key is needed to inspect the work.

## Running or inspecting the work

To be added with the first runnable version.

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

## Additional files

- `phase1/`: reused work from Phase 1 (Labs 1 to 3): the problem statement and related-work map,
  the interaction loop and storyboards, the specification, system path diagrams v1 and v2, the
  Python simulation and its outputs, and the Phase 1 prompt log. It is kept unchanged as the
  starting point of this project.

## API keys

No key is stored in this repository. For live mode, a reviewer supplies their own key in the
`ANTHROPIC_API_KEY` environment variable (instructions to follow).
