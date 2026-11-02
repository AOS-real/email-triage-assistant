"""Inbox state and the interaction algorithms of the concept design (docs/concept-design-algorithms.md):
moves with undo (A8, A12), learning from a correction with preview and confirmation (A9),
the learned-rules panel with expiry, edit and forget (A10), declining out-of-scope requests (A11)
and the Can wait summary (A14).

State is held in memory for one session; restarting the server resets it.
"""

import json
import re
from datetime import date, timedelta
from pathlib import Path

from triage.decide import decide, describe_rule, facts_from, matches
from triage.extract import extract
from triage.guards import validate_rule

ROOT = Path(__file__).resolve().parent.parent
RULE_EXPIRY_DAYS = 90
SECTION_NAMES = {"needs_you": "Needs you", "can_wait": "Can wait", "not_sure": "Needs you"}

# Reasons offered when the person moves a message, and what each one may teach.
REASONS = {
    "needs_you": [("sender", "This sender matters"),
                  ("missed_deadline", "It has a deadline the assistant missed"),
                  ("once", "Just this once")],
    "can_wait": [("sender", "This sender can always wait"),
                 ("once", "Just this once")],
}

OUT_OF_SCOPE = ["delete", "remove", "send", "reply", "forward", "archive", "unsubscribe", "block"]
CAPABILITIES = ["sort mail into Needs you and Can wait",
                "show why each message was placed where it is",
                "learn a rule about a sender when you move a message and confirm it"]


class Inbox:

    def __init__(self, emails=None, today=None):
        self.emails = emails or json.loads(
            (ROOT / "data" / "test_emails.json").read_text(encoding="utf-8"))
        self.today = today or date.today()
        self.extractions = {e["id"]: extract(e, live=False) for e in self.emails}
        self.rules = []
        self.moves = {}      # email id -> {"section", "reason"}, the person's own placements
        self.undo = {}       # email id -> the move that the last action replaced (None if none)
        self.next_rule = 1
        self.pending = None  # a proposed rule awaiting the person's confirmation

    # ---- reading the inbox -------------------------------------------------------------

    def active_rules(self):
        return [r for r in self.rules if date.fromisoformat(r["expires"]) >= self.today]

    def decision(self, email):
        return decide(email, self.extractions[email["id"]], self.active_rules())

    def section_of(self, email):
        move = self.moves.get(email["id"])
        return move["section"] if move else self.decision(email)["section"]

    def view(self):
        """Everything the interface shows, built fresh on every request (no cached copies)."""
        messages = []
        for email in self.emails:
            d = self.decision(email)
            move = self.moves.get(email["id"])
            messages.append({
                "id": email["id"], "from": email["from"], "subject": email["subject"],
                "body": email["body"], "attachments": email["attachments"],
                "sender_known": email["sender_known"],
                "section": move["section"] if move else d["section"],
                "moved_by_you": move["reason"] if move else None,
                "label": d,
                "can_undo": email["id"] in self.undo,
                "reasons": REASONS["can_wait" if (move["section"] if move else d["section"])
                                   in ("needs_you", "not_sure") else "needs_you"],
                "source": self.extractions[email["id"]]["record"].get("mode", "unknown"),
            })
        return {"messages": messages, "rules": self.rules_view(), "summary": self.summary(),
                "today": self.today.isoformat()}

    def summary(self):
        """A14: keep Can wait from being treated as already checked."""
        waiting = [e for e in self.emails if self.section_of(e) == "can_wait"]
        new = [e for e in waiting if not e["sender_known"]]
        return {"waiting": len(waiting), "new_senders": len(new),
                "text": f"{len(waiting)} messages are waiting in Can wait; "
                        f"{len(new)} {'is' if len(new) == 1 else 'are'} from new senders."}

    def rules_view(self):
        rows = []
        for rule in reversed(self.rules):
            expired = date.fromisoformat(rule["expires"]) < self.today
            rows.append(dict(rule, text=describe_rule(rule), expired=expired))
        return rows

    # ---- moving messages (A8, A12) -------------------------------------------------------

    def move(self, email_id, section, reason_key):
        email = self.email(email_id)
        if email is None or section not in REASONS or reason_key not in dict(REASONS[section]):
            return {"error": "That move is not available."}
        allowed = REASONS[section]
        self.undo[email_id] = self.moves.get(email_id)
        self.moves[email_id] = {"section": section, "reason": dict(allowed)[reason_key]}
        result = {"moved": True, "to": SECTION_NAMES[section]}
        result.update(self.propose_rule(email, section, reason_key))
        return result

    def undo_move(self, email_id):
        if email_id not in self.undo:
            return {"error": "There is nothing to undo for this message."}
        self.pending = None  # undoing a move also cancels the rule it offered (A12)
        previous = self.undo.pop(email_id)
        if previous is None:
            self.moves.pop(email_id, None)
        else:
            self.moves[email_id] = previous
        return {"undone": True}

    # ---- learning (A9) -----------------------------------------------------------------------

    def propose_rule(self, email, section, reason_key):
        """Propose the narrowest rule the reason supports; nothing is stored until confirmed."""
        facts = facts_from(email, self.extractions[email["id"]])
        if reason_key == "once":
            return {"rule": None, "message": "Moved for this message only. Nothing was learned."}
        if reason_key == "missed_deadline":
            return {"rule": None, "message": (
                "Moved. The assistant found no deadline in this email, so there is no safe rule "
                "to learn; this is recorded as a missed deadline.")}
        if facts is None:
            return {"rule": None, "message": (
                "Moved. The assistant could not check this email, so nothing is learned from it.")}
        rule = {"id": f"R{self.next_rule}", "condition": {"sender": email["from"]},
                "section": section, "created": self.today.isoformat(),
                "expires": (self.today + timedelta(days=RULE_EXPIRY_DAYS)).isoformat(),
                "source": "person",
                "evidence": f"Your move of \"{email['subject']}\" ({dict(REASONS[section])[reason_key]})"}
        problems = self.rule_problems(rule)
        if problems:
            return {"rule": None, "message": "Moved. " + " ".join(problems)}
        affected = [e["subject"] for e in self.emails
                    if e["id"] != email["id"] and self.would_move(rule, e)]
        self.pending = rule  # held on the server; the browser can only confirm it, not alter it
        return {"rule": dict(rule, text=describe_rule(rule)), "affected": affected,
                "message": None}

    def rule_problems(self, rule, ignore_id=None):
        others = [r for r in self.rules if r["id"] != ignore_id]
        problems = validate_rule(rule, others)
        if any(r["condition"] == rule["condition"] and r["section"] == rule["section"]
               for r in others):
            problems.append("This rule has already been learned.")
        return problems

    def would_move(self, rule, email):
        facts = facts_from(email, self.extractions[email["id"]])
        return (facts is not None and matches(rule, facts) and email["id"] not in self.moves
                and self.section_of(email) != rule["section"])

    def save_rule(self, rule_id):
        """Store the proposed rule only after the person confirms it; checked again here."""
        rule = self.pending
        if rule is None or rule["id"] != rule_id:
            return {"error": "There is no rule waiting for confirmation."}
        problems = self.rule_problems(rule)
        if problems:
            return {"error": " ".join(problems)}
        self.rules.append(rule)
        self.pending = None
        self.next_rule += 1
        return {"saved": True, "rule": dict(rule, text=describe_rule(rule))}

    def discard_rule(self):
        self.pending = None
        return {"discarded": True}

    # ---- What I've learned (A10) -------------------------------------------------------------

    def edit_rule(self, rule_id, section):
        rule = self.rule(rule_id)
        if rule is None:
            return {"error": "That rule no longer exists."}
        changed = dict(rule, section=section)
        problems = self.rule_problems(changed, ignore_id=rule_id)
        if problems:
            return {"error": " ".join(problems)}
        rule["section"] = section
        return {"edited": True, "rule": dict(rule, text=describe_rule(rule))}

    def renew_rule(self, rule_id):
        rule = self.rule(rule_id)
        if rule is None:
            return {"error": "That rule no longer exists."}
        rule["expires"] = (self.today + timedelta(days=RULE_EXPIRY_DAYS)).isoformat()
        return {"renewed": True}

    def forget_rule(self, rule_id):
        """Delete the rule; decisions are rebuilt on every request, so no copy of it survives."""
        rule = self.rule(rule_id)
        if rule is None:
            return {"error": "That rule no longer exists."}
        before = {e["id"]: self.section_of(e) for e in self.emails}
        self.rules.remove(rule)
        resorted = [e["subject"] for e in self.emails if self.section_of(e) != before[e["id"]]]
        return {"forgotten": True, "resorted": resorted}

    # ---- requests (A11) --------------------------------------------------------------------

    def handle_request(self, text):
        action = next((w for w in OUT_OF_SCOPE
                       if re.search(rf"\b{w}\b", text, re.IGNORECASE)), None)
        if action:
            return {"kind": "decline",
                    "text": (f"I cannot {action} mail. I can only "
                             + "; ".join(CAPABILITIES) + ". You can select messages in your mail "
                             "client and do this yourself."),
                    "stored": False}
        return {"kind": "clarify",
                "text": "I can " + "; ".join(CAPABILITIES) + ". Which of these would help?",
                "stored": False}

    # ---- helpers -----------------------------------------------------------------------------

    def email(self, email_id):
        return next((e for e in self.emails if e["id"] == email_id), None)

    def rule(self, rule_id):
        return next((r for r in self.rules if r["id"] == rule_id), None)
