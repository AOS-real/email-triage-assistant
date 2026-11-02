"""The extraction call: assemble the context, call the model (live) or read a recorded output
(replay), and check the result before anything else uses it.
"""

import json
import os
from pathlib import Path

from triage.schema import SCHEMA, shape_problems, support_problems

ROOT = Path(__file__).resolve().parent.parent
PROMPT_VERSION = "v1"
PROMPT_FILE = ROOT / "prompts" / f"extract_{PROMPT_VERSION}.txt"
RUNS_DIR = ROOT / "recorded_runs"
MODEL = "claude-sonnet-5-5"


def email_as_data(email):
    """Wrap the email so the model receives it as untrusted data, not as instructions."""
    attachments = ", ".join(
        f"{a['name']} ({'readable' if a['readable'] else 'could not be read'})"
        for a in email["attachments"]) or "none"
    return ("<email>\n"
            f"From: {email['from']}\n"
            f"Subject: {email['subject']}\n"
            f"Attachments: {attachments}\n\n"
            f"{email['body']}\n"
            "</email>")


def call_live(email):
    """Call Claude Sonnet 5.5 at medium effort with structured output. Needs ANTHROPIC_API_KEY."""
    import anthropic  # imported here so replay mode needs no installed packages

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        system=PROMPT_FILE.read_text(encoding="utf-8"),
        messages=[{"role": "user", "content": email_as_data(email)}],
        output_config={"effort": "medium",
                       "format": {"type": "json_schema", "schema": SCHEMA}},
    )
    text = next(block.text for block in response.content if block.type == "text")
    output = json.loads(text)
    record = {"case": email["id"], "mode": "live", "model": MODEL,
              "prompt_version": PROMPT_VERSION, "output": output}
    (RUNS_DIR / f"{email['id']}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    return record


def read_replay(email):
    """Read the recorded output for this email."""
    path = RUNS_DIR / f"{email['id']}.json"
    if not path.exists():
        return {"case": email["id"], "mode": "replay", "output": None,
                "note": "no recorded output for this email"}
    return json.loads(path.read_text(encoding="utf-8"))


def extract(email, live=None):
    """Return the extraction and its check results.

    `supported` is False when the output fails the schema (C1) or quotes text that is not in
    the email (C2, C5); the decision rules must then treat the facts as unknown.
    """
    if live is None:
        live = os.environ.get("TRIAGE_MODE") == "live"
    record = call_live(email) if live else read_replay(email)
    output = record.get("output")
    problems = shape_problems(output) if output is not None else ["no output"]
    if not problems:
        problems = support_problems(output, email)
    return {"record": record, "output": output, "problems": problems,
            "supported": not problems}
