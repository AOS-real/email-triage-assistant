#!/usr/bin/env python3
"""
triage_sim.py: small runnable simulation of the AI email-triage system path.

Usage:  python3 triage_sim.py v1      (path as first specified)
        python3 triage_sim.py v2      (revised path, Phase 4)

What is real and what is mocked (also marked in the output):
  IMPLEMENTED  regex extraction, rule classifier, reason text, confidence check, correction handling
  SIMULATED    the inbox (printed text), sender history (a Python dict), learned rules (a list in memory)
  MOCKED       confidence numbers (simple hand-made formula), the "LLM" (a regex stands in for it)
No real email, model or network is used. All names and addresses are placeholders.
"""
import json
import re
import sys

VERSION = sys.argv[1] if len(sys.argv) > 1 else "v1"
assert VERSION in ("v1", "v2"), "use v1 or v2"

# SIMULATED data source: what the assistant knows about the owner's past behaviour.
OWNER_HISTORY = {
    "newsletter@example.com": {"replies": 0, "opens": 2},
    "colleague@example.com": {"replies": 14, "opens": 40},
}
LEARNED_RULES = []  # SIMULATED memory; filled when the person corrects the system

DAYS = r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)"
DEADLINE_RE = re.compile(
    rf"\b(by {DAYS}( \d{{1,2}}(:\d\d)?\s?(am|pm))?|by (today|tomorrow)|asap|urgent|deadline)\b", re.I
)
ASK_RE = re.compile(r"\b(please|can you|could you|would you)\b", re.I)


def extract(msg):
    """EXTRACT step (IMPLEMENTED with regex; stands in for an LLM)."""
    m = DEADLINE_RE.search(msg["body"] + " " + msg["subject"])
    hist = OWNER_HISTORY.get(msg["from"])
    unreadable = [a["name"] for a in msg.get("attachments", []) if not a["readable"]]
    info = {
        "deadline_found": m.group(0) if m else None,
        "asks_for_something": bool(ASK_RE.search(msg["body"])),
        "sender_known": hist is not None,
        "owner_replies_to_sender": hist["replies"] if hist else None,
        "unreadable_attachments": unreadable,
    }
    return info


def confidence(info):
    """MOCKED confidence: a hand-made formula, not a trained model."""
    c = 0.5
    if info["deadline_found"]:
        c += 0.3
    if info["sender_known"]:
        c += 0.2
    c -= 0.2 * len(info["unreadable_attachments"])
    return round(max(0.0, min(1.0, c)), 2)


def classify_v1(info):
    """CLASSIFY step, first design. Weak point: a new sender lowers priority."""
    for rule in LEARNED_RULES:
        if rule == "deadline+new_sender" and info["deadline_found"] and not info["sender_known"]:
            return "Needs you", "Deadline from a new sender (learned from your correction)", "learned rule applied"
    if not info["sender_known"]:
        return "Can wait", "New sender, no past replies", "rule: new sender -> Can wait"
    if info["owner_replies_to_sender"] == 0:
        return "Can wait", "Owner has never replied to this sender", "rule: never replied -> Can wait"
    return "Needs you", "You often reply to this sender", "rule: replies > 0 -> Needs you"


def classify_v2(info):
    """VALIDATE then CLASSIFY, revised. Low confidence abstains instead of guessing; a deadline raises priority."""
    c = confidence(info)
    if c < 0.6:  # VALIDATION step (new in v2): too little information to decide
        missing = []
        if not info["deadline_found"]:
            missing.append("no deadline found")
        for a in info["unreadable_attachments"]:
            missing.append(f"could not read attachment {a}")
        if not info["sender_known"]:
            missing.append("new sender")
        return "Needs you (Not sure)", "Not sure: " + "; ".join(missing), f"abstain: confidence {c} < 0.6"
    if info["deadline_found"]:
        return "Needs you", f"Deadline found: {info['deadline_found']}", "rule: deadline -> Needs you"
    if info["owner_replies_to_sender"] == 0:
        return "Can wait", "Owner has never replied to this sender", "rule: never replied -> Can wait"
    return "Needs you", "You often reply to this sender", "rule: replies > 0 -> Needs you"


def triage(msg):
    info = extract(msg)
    section, reason, rule = (classify_v1 if VERSION == "v1" else classify_v2)(info)
    return info, section, reason, rule


def correction(choice, free_text=None):
    """CORRECTION + LEARN steps."""
    if choice == "Urgent deadline":
        LEARNED_RULES.append("deadline+new_sender")
        return "Got it. I'll show messages like this in Needs you.", "learned rule added: deadline+new_sender -> Needs you"
    if choice == "Other":
        # Both versions: free text is stored but not understood.
        return "Got it. I'll show messages like this in Needs you.", f"free text stored, NOT parsed: {free_text!r}; no rule added"
    return "Got it.", "no rule added"


def show(title, msg, extra_next):
    print(f"\n### {title}\n")
    print("**1. Input (verbatim)**\n")
    print(f"- From: {msg['name']} <{msg['from']}>\n- Subject: {msg['subject']}\n- Body: \"{msg['body']}\"")
    if msg.get("attachments"):
        print("- Attachments: " + ", ".join(f"{a['name']} (readable: {a['readable']})" for a in msg["attachments"]))
    info, section, reason, rule = triage(msg)
    hist = OWNER_HISTORY.get(msg["from"], "not available (no past messages)")
    print("\n**2. What the system receives**\n")
    print(f"- Message fields as above\n- Sender history [SIMULATED dict]: {hist}")
    print(f"- Learned rules [SIMULATED memory]: {LEARNED_RULES or 'none'}")
    print("\n**3. Extracted information** [IMPLEMENTED regex; confidence is MOCKED]\n")
    print("```json\n" + json.dumps({**info, "confidence": confidence(info)}, indent=2) + "\n```")
    print("\n**4. Processing steps**\n")
    print("1. EXTRACT: regex finds deadline words, checks sender history, checks attachments")
    if VERSION == "v2":
        print(f"2. VALIDATE (v2): confidence {confidence(info)} against threshold 0.6")
        print(f"3. CLASSIFY: {rule}")
    else:
        print(f"2. CLASSIFY: {rule}")
    print("\n**5. System response** [SIMULATED text output]\n")
    print(f"- Section: **{section}**\n- Label shown: \"{reason}\"")
    print("\n**6. Next action**\n")
    print(extra_next(section))
    return section


def person_options(section):
    if "Not sure" in section:
        return ("- Person sees: \"Not sure\" label and a question: \"Can this wait?\"\n"
                "- Options: [Keep in Needs you] [Move to Can wait]. The message stays visible in Needs you until they choose.")
    if section == "Can wait":
        return ("- Person can: leave it, tap the label to read the reason, or tap [Move back to Needs you].\n"
                "- If moved back, the system asks \"Why was this wrong?\" with [Urgent deadline] [Important sender] [Other].")
    return "- Person can: open and reply, or tap the label to read the reason. No correction needed."


A1 = {"from": "landlord@example.com", "name": "Landlord", "subject": "Rent review - reply by Thursday",
      "body": "Hi, we are reviewing rents. Please reply by Thursday 5pm to confirm you are happy to continue. Thanks.",
      "attachments": []}
A2 = {"from": "agent@example.com", "name": "Letting Agent", "subject": "Inspection - please confirm",
      "body": "Please confirm by Friday that Saturday morning works for the inspection.", "attachments": []}
B1 = {"from": "jsmith@example.com", "name": "J. Smith", "subject": "Quick thing",
      "body": "Hi, could you take a look at this when you get a chance? Thanks, J",
      "attachments": [{"name": "scan_0042.pdf", "readable": False}]}

if __name__ == "__main__":
    print(f"# Simulation run: path {VERSION}\n")
    print("Labels: IMPLEMENTED = runs as code here; SIMULATED = printed text or in-memory stand-in; MOCKED = invented numbers.")

    print("\n## Test A: standard input (full failure-and-recovery path)")
    s = show("A1: first message from a new sender with a clear deadline", A1, person_options)
    if s == "Can wait":
        print("\n**Person's correction (step in the use case):** taps [Move back to Needs you], then [Urgent deadline]")
        resp, learned = correction("Urgent deadline")
        print(f"- System response: \"{resp}\"\n- What changed [SIMULATED]: {learned}")
    show("A2: later similar message from another new sender (did it learn?)", A2, person_options)

    print("\n## Test B: problem input")
    s = show("B1: vague message, new sender, unreadable attachment", B1, person_options)
    print("\n### B2: out-of-scope request typed into the correction box")
    print("\n**1. Input (verbatim)**\n\n- Person chooses [Other] and types: \"delete everything from the landlord\"")
    resp, learned = correction("Other", "delete everything from the landlord")
    print("\n**2-4. What the system receives / extracts / processing**\n")
    print(f"- Receives: option 'Other' with free text. No deletion command exists in this system (out of scope).\n- Processing: {learned}")
    print(f"\n**5. System response** [SIMULATED]\n\n- \"{resp}\"")
    print("\n**6. Next action**\n\n- Person can do nothing further here. Nothing was deleted and no rule was added, "
          "but the confirmation message does not say so.")
