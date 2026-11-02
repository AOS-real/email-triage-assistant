"""Run the fixed test set through the extraction call and score it against criteria C1 to C6.

Usage:  python evaluate.py            (replay mode, no key needed)
        TRIAGE_MODE=live python evaluate.py   (live mode, needs ANTHROPIC_API_KEY)

Writes results/extraction_<prompt version>.md.
"""

import json
from pathlib import Path

from triage.extract import PROMPT_VERSION, extract
from triage.schema import shape_problems, support_problems

ROOT = Path(__file__).resolve().parent
CRITERIA = ["C1", "C2", "C3", "C4", "C5", "C6"]


def score(email, result):
    """Return pass (True) or fail (False) for each criterion."""
    out = result["output"]
    if out is None or shape_problems(out):
        return {c: False for c in CRITERIA}
    unsupported = support_problems(out, email)
    expected = email["expected"]
    return {
        "C1": True,
        "C2": not any(p.startswith("deadline") for p in unsupported),
        "C3": (out["deadline_text"] is not None) == expected["deadline"],
        "C4": out["asks_for_action"] == expected["asks_for_action"],
        "C5": not any(p.startswith("evidence") for p in unsupported),
        "C6": bool(out["instructions_in_email"]) == expected["instructions"],
    }


def main():
    emails = json.loads((ROOT / "data" / "test_emails.json").read_text(encoding="utf-8"))
    rows, totals, modes = [], {c: 0 for c in CRITERIA}, set()
    for email in emails:
        result = extract(email)
        modes.add(result["record"].get("mode", "unknown"))
        marks = score(email, result)
        for c in CRITERIA:
            totals[c] += marks[c]
        cells = " | ".join("pass" if marks[c] else "**fail**" for c in CRITERIA)
        status = "supported" if result["supported"] else "unsupported: " + "; ".join(result["problems"])
        rows.append(f"| {email['id']} | {email['case']} | {cells} | {status} |")

    n = len(emails)
    lines = [
        f"# Extraction results, prompt {PROMPT_VERSION}",
        "",
        f"Mode of the outputs scored: {', '.join(sorted(modes))}.",
    ]
    if "simulated" in modes:
        lines += ["", "These outputs are SIMULATED. The scores test the checks and the pipeline, "
                      "not the model; live results will replace them when a key is available."]
    lines += ["", "| Case | Description | " + " | ".join(CRITERIA) + " | Check result |",
              "|---|---|" + "---|" * len(CRITERIA) + "---|", *rows,
              "| | **Passed** | " + " | ".join(f"{totals[c]}/{n}" for c in CRITERIA) + " | |", ""]
    out_dir = ROOT / "results"
    out_dir.mkdir(exist_ok=True)
    path = out_dir / f"extraction_{PROMPT_VERSION}.md"
    path.write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    print(f"Written to {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
