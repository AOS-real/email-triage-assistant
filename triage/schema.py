"""Output schema for the extraction call, and the checks applied to every output.

The schema guarantees shape, not truth, so `support_problems` also checks that every quoted
span really appears in the email (criteria C2 and C5 in docs/extraction_spec.md).
"""

SENDER_TYPES = ["person", "organisation", "automated", "unknown"]

SCHEMA = {
    "type": "object",
    "properties": {
        "deadline_text": {"type": ["string", "null"]},
        "asks_for_action": {"type": "boolean"},
        "sender_type": {"type": "string", "enum": SENDER_TYPES},
        "evidence": {"type": "array", "items": {"type": "string"}},
        "instructions_in_email": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["deadline_text", "asks_for_action", "sender_type", "evidence",
                 "instructions_in_email"],
    "additionalProperties": False,
}


def shape_problems(output):
    """Return a list of schema violations (criterion C1); empty if the shape is valid."""
    if not isinstance(output, dict):
        return ["output is not a JSON object"]
    problems = []
    for key in SCHEMA["required"]:
        if key not in output:
            problems.append(f"missing field: {key}")
    for key in output:
        if key not in SCHEMA["properties"]:
            problems.append(f"unexpected field: {key}")
    if "deadline_text" in output and not (output["deadline_text"] is None
                                          or isinstance(output["deadline_text"], str)):
        problems.append("deadline_text must be text or null")
    if "asks_for_action" in output and not isinstance(output["asks_for_action"], bool):
        problems.append("asks_for_action must be true or false")
    if "sender_type" in output and output["sender_type"] not in SENDER_TYPES:
        problems.append("sender_type is not an allowed value")
    for key in ("evidence", "instructions_in_email"):
        value = output.get(key, [])
        if not (isinstance(value, list) and all(isinstance(item, str) for item in value)):
            problems.append(f"{key} must be a list of text")
    return problems


def support_problems(output, email):
    """Return quoted spans that do not appear word for word in the email (criteria C2, C5)."""
    source = f"{email['subject']}\n{email['body']}"
    problems = []
    deadline = output.get("deadline_text")
    if deadline is not None and deadline not in source:
        problems.append(f'deadline "{deadline}" is not in the email')
    for quote in output.get("evidence", []):
        if quote not in source:
            problems.append(f'evidence "{quote}" is not in the email')
    return problems
