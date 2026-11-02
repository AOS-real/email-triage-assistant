"""Decision rules: choose the inbox section and write the reason label.

The rules read only checked facts, so the label states exactly the signals that were used
(what was used, what was not used, and how to change the result). A model never writes the label.

Sections: "needs_you", "can_wait", and "not_sure" (shown in Needs you with a question).
"""

NOT_USED = "Your past replies and other emails were not used."
ASK = "Can this wait?"


def facts_from(email, extraction):
    """The signals the rules may use. Returns None when the extraction cannot be trusted."""
    out = extraction["output"] if extraction["supported"] else None
    if out is None:
        return None
    acts = out["asks_for_action"]
    return {
        # E10: a time in an email that asks nothing of the reader is not a deadline.
        "deadline": out["deadline_text"] if acts else None,
        "asks_for_action": acts,
        "sender_known": email["sender_known"],
        "sender_type": out["sender_type"],
        "evidence": out["evidence"],
        "ignored_time": out["deadline_text"] if not acts else None,
    }


def describe_rule(rule):
    """Plain-language text of a learned rule, as shown to the person."""
    parts = []
    cond = rule["condition"]
    if cond.get("deadline"):
        parts.append("has a deadline")
    if "asks_for_action" in cond:
        parts.append("asks you to act" if cond["asks_for_action"] else "asks nothing of you")
    if "sender_known" in cond:
        parts.append("is from a known sender" if cond["sender_known"] else "is from a new sender")
    if "sender_type" in cond:
        parts.append(f"is from a {cond['sender_type']} sender")
    where = "Needs you" if rule["section"] == "needs_you" else "Can wait"
    return f"Mail that {' and '.join(parts)} goes to {where}"


def matches(rule, facts):
    for key, wanted in rule["condition"].items():
        value = bool(facts["deadline"]) if key == "deadline" else facts[key]
        if value != wanted:
            return False
    return True


def decide(email, extraction, rules=()):
    unreadable = [a["name"] for a in email["attachments"] if not a["readable"]]
    injected = list(dict.fromkeys(
        (extraction["output"] or {}).get("instructions_in_email", []) + extraction["injection_found"]))
    warnings = [f'Text addressed to an assistant was ignored: "{text}"' for text in injected]
    warnings += extraction.get("notes", [])
    label = {"warnings": warnings, "not_used": [NOT_USED], "ask": None, "rule_id": None}

    facts = facts_from(email, extraction)
    if facts is None:
        return dict(label, section="not_sure", headline="Not sure",
                    used=[f"The email could not be checked: {extraction['problems'][0]}"], ask=ASK)

    used = [f'The email says: "{quote}"' for quote in facts["evidence"]]
    if facts["ignored_time"]:
        label["not_used"].append(
            f'"{facts["ignored_time"]}" was found, but the email asks nothing of you, '
            "so it was not treated as a deadline.")

    if unreadable and not facts["deadline"]:
        return dict(label, section="not_sure", headline="Not sure",
                    used=used + [f"Could not read {', '.join(unreadable)}, which may say more"],
                    ask=ASK)

    for rule in reversed(list(rules)):  # the most recent correction wins
        if matches(rule, facts):
            return dict(label, section=rule["section"], rule_id=rule["id"],
                        headline=f"Your rule: {describe_rule(rule)}",
                        used=used + [f"Rule from your correction on {rule['created']}"])

    if facts["deadline"]:
        return dict(label, section="needs_you", headline=f"Deadline: {facts['deadline']}", used=used)
    if facts["asks_for_action"]:
        return dict(label, section="needs_you", headline="Asks you to act (no deadline found)",
                    used=used)
    if facts["sender_type"] == "automated":
        used.append("Sent by an automated service")
    return dict(label, section="can_wait", headline="No request for you found", used=used)
