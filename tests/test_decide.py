"""Regression tests for the decision rules and the guards. Run: python -m unittest -v"""

import json
import unittest
from pathlib import Path

from triage.decide import decide
from triage.extract import extract
from triage.guards import MAX_BODY_CHARS, find_injection, guard_call, guard_input, validate_rule

EMAILS = {e["id"]: e for e in json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "test_emails.json").read_text(encoding="utf-8"))}


def extraction(output, email, supported=True, problems=None):
    """A controlled extraction, so the rules are tested independently of any model output."""
    return {"output": output, "supported": supported, "problems": problems or [],
            "notes": [], "injection_found": find_injection(email)}


def output(deadline=None, acts=False, sender="person", evidence=(), instructions=()):
    return {"deadline_text": deadline, "asks_for_action": acts, "sender_type": sender,
            "evidence": list(evidence), "instructions_in_email": list(instructions)}


class DecisionRules(unittest.TestCase):

    def test_deadline_and_request_need_you(self):
        email = EMAILS["E01"]
        d = decide(email, extraction(output("by Thursday 5pm", True,
                                            evidence=["Please reply by Thursday 5pm"]), email))
        self.assertEqual(d["section"], "needs_you")
        self.assertEqual(d["headline"], "Deadline: by Thursday 5pm")

    def test_event_time_without_request_is_not_a_deadline(self):
        email = EMAILS["E10"]
        d = decide(email, extraction(output("Friday at 10:00", False), email))
        self.assertEqual(d["section"], "can_wait")
        self.assertTrue(any("Friday at 10:00" in note for note in d["not_used"]))

    def test_unsupported_extraction_is_not_sure(self):
        email = EMAILS["E05"]
        d = decide(email, extraction(None, email, False, ["deadline is not in the email"]))
        self.assertEqual(d["section"], "not_sure")
        self.assertEqual(d["ask"], "Can this wait?")

    def test_unreadable_attachment_without_deadline_is_not_sure(self):
        email = EMAILS["E03"]
        d = decide(email, extraction(output(None, True), email))
        self.assertEqual(d["section"], "not_sure")
        self.assertTrue(any("scan_0042.pdf" in line for line in d["used"]))

    def test_label_never_claims_unused_history(self):
        email = EMAILS["E01"]
        d = decide(email, extraction(output("by Thursday 5pm", True), email))
        self.assertFalse(any("replied" in line or "sender" in line for line in d["used"]))


class Guards(unittest.TestCase):

    def test_injected_text_never_changes_the_section(self):
        email = EMAILS["E07"]
        clean = dict(email, body="Save 40% on headphones this weekend only.")
        with_text = decide(email, extraction(output(sender="organisation"), email))
        without = decide(clean, extraction(output(sender="organisation"), clean))
        self.assertEqual(with_text["section"], without["section"])
        self.assertTrue(with_text["warnings"])

    def test_injection_found_without_the_model(self):
        self.assertTrue(find_injection(EMAILS["E07"]))
        for key in EMAILS:
            if key != "E07":
                self.assertEqual(find_injection(EMAILS[key]), [], key)

    def test_failed_model_call_is_not_sure(self):
        def broken(_email):
            raise TimeoutError
        record, failure = guard_call(broken, EMAILS["E01"])
        self.assertIsNone(record)
        self.assertIn("could not read", failure)

    def test_long_email_is_shortened_and_noted(self):
        email = dict(EMAILS["E02"], body="x" * (MAX_BODY_CHARS + 50))
        sent, note = guard_input(email)
        self.assertEqual(len(sent["body"]), MAX_BODY_CHARS)
        self.assertIsNotNone(note)

    def test_rules_only_come_from_the_person(self):
        rule = {"id": "R1", "condition": {"deadline": True}, "section": "needs_you",
                "created": "2026-11-02", "source": "email"}
        self.assertTrue(validate_rule(rule, []))
        rule["source"] = "person"
        self.assertEqual(validate_rule(rule, []), [])
        rule["condition"] = {"delete_everything": True}
        self.assertTrue(validate_rule(rule, []))

    def test_learned_rule_overrides_the_default(self):
        email = EMAILS["E08"]
        rule = {"id": "R1", "condition": {"asks_for_action": True, "deadline": False},
                "section": "can_wait", "created": "2026-11-02", "source": "person"}
        d = decide(email, extraction(output(None, True), email), [rule])
        self.assertEqual(d["section"], "can_wait")
        self.assertEqual(d["rule_id"], "R1")


class ReplayEndToEnd(unittest.TestCase):

    def test_every_test_email_is_placed_safely(self):
        """Each email reaches its expected section; "not_sure" counts as safe only where the
        correct section is Needs you, because "not_sure" is shown there."""
        for key, email in EMAILS.items():
            d = decide(email, extract(email, live=False))
            expected = email["expected"]["section"]
            safe = d["section"] == expected or (d["section"] == "not_sure" and expected == "needs_you")
            self.assertTrue(safe, f"{key}: got {d['section']}, expected {expected}")


if __name__ == "__main__":
    unittest.main()
