"""Guards that protect the system itself, applied around the model call.

Each guard is deterministic code, so it holds whatever the model returns:
- input guard: caps the email length sent to the model (the context window is a budget);
- injection guard: finds text addressed to an assistant without relying on the model to report it;
- failure guard: turns a failed or missing model call into an honest "could not read" result;
- rule guard: accepts a learned rule only from the person's own correction, in a fixed shape.
"""

import re
from datetime import date

MAX_BODY_CHARS = 4000
MAX_RULES = 20

INJECTION_PATTERNS = [
    r"\bassistant\s*:",
    r"\bai\s*:",
    r"ignore (all |any )?(previous|prior|earlier) instructions",
    r"\b(mark|move|archive|delete|forward) (this|all|every)\b.*\b(mail|message|email)s?\b",
]

RULE_CONDITIONS = {"sender", "deadline", "asks_for_action", "sender_known", "sender_type"}
SECTIONS = {"needs_you", "can_wait"}


def guard_input(email):
    """Return the email to send and a note if it was shortened."""
    if len(email["body"]) <= MAX_BODY_CHARS:
        return email, None
    shortened = dict(email, body=email["body"][:MAX_BODY_CHARS])
    return shortened, f"only the first {MAX_BODY_CHARS} characters were read"


def find_injection(email):
    """Return lines of the email that address an assistant, found by pattern, not by the model."""
    found = []
    for sentence in re.split(r"(?<=[.!?])\s+|\n", email["body"]):
        if any(re.search(p, sentence, re.IGNORECASE) for p in INJECTION_PATTERNS):
            found.append(sentence.strip())
    return found


def guard_call(call, email):
    """Run the model call; any failure becomes an empty result with a stated reason."""
    try:
        return call(email), None
    except Exception as error:  # the model or network is unavailable: never guess
        return None, f"the assistant could not read this email ({type(error).__name__})"


def validate_rule(rule, existing):
    """Return problems with a proposed learned rule; empty if it may be stored."""
    problems = []
    if rule.get("source") != "person":
        problems.append("rules can only come from the person's own correction")
    if not rule.get("condition") or set(rule["condition"]) - RULE_CONDITIONS:
        problems.append("the condition uses an unknown signal")
    if rule.get("section") not in SECTIONS:
        problems.append("the section is not one of Needs you or Can wait")
    if len(existing) >= MAX_RULES:
        problems.append(f"at most {MAX_RULES} rules can be stored; forget one first")
    try:
        date.fromisoformat(rule.get("created", ""))
    except ValueError:
        problems.append("the rule has no valid date")
    return problems
