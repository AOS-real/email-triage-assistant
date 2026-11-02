"""Tests for the interaction algorithms A8 to A14 (triage/inbox.py). Run: python -m unittest -v"""

import unittest
from datetime import date, timedelta

from triage.inbox import Inbox

TODAY = date(2026, 11, 2)


def section(inbox, email_id):
    return next(m["section"] for m in inbox.view()["messages"] if m["id"] == email_id)


class Moves(unittest.TestCase):

    def test_not_sure_answer_and_undo(self):
        inbox = Inbox(today=TODAY)
        self.assertEqual(section(inbox, "E03"), "not_sure")
        inbox.move("E03", "can_wait", "once")
        self.assertEqual(section(inbox, "E03"), "can_wait")
        inbox.undo_move("E03")
        self.assertEqual(section(inbox, "E03"), "not_sure")

    def test_just_this_once_learns_nothing(self):
        inbox = Inbox(today=TODAY)
        result = inbox.move("E02", "needs_you", "once")
        self.assertIsNone(result["rule"])
        self.assertIsNone(inbox.pending)

    def test_unknown_move_is_refused(self):
        inbox = Inbox(today=TODAY)
        self.assertIn("error", inbox.move("E02", "deleted", "once"))
        self.assertIn("error", inbox.move("E99", "can_wait", "once"))


class Learning(unittest.TestCase):

    def test_rule_is_proposed_not_stored_until_confirmed(self):
        inbox = Inbox(today=TODAY)
        result = inbox.move("E08", "can_wait", "sender")
        self.assertEqual(result["rule"]["condition"], {"sender": "Priya <priya@example.com>"})
        self.assertEqual(inbox.rules, [])
        inbox.save_rule(result["rule"]["id"])
        self.assertEqual(len(inbox.rules), 1)

    def test_browser_cannot_alter_or_invent_a_rule(self):
        inbox = Inbox(today=TODAY)
        self.assertIn("error", inbox.save_rule("R1"))  # nothing proposed

    def test_duplicate_rule_is_refused(self):
        inbox = Inbox(today=TODAY)
        first = inbox.move("E08", "can_wait", "sender")
        inbox.save_rule(first["rule"]["id"])
        inbox.undo_move("E08")
        second = inbox.move("E08", "can_wait", "sender")
        self.assertIsNone(second["rule"])
        self.assertIn("already been learned", second["message"])

    def test_missed_deadline_learns_nothing_and_says_so(self):
        inbox = Inbox(today=TODAY)
        result = inbox.move("E02", "needs_you", "missed_deadline")
        self.assertIsNone(result["rule"])
        self.assertIn("missed deadline", result["message"])

    def test_unchecked_email_teaches_nothing(self):
        inbox = Inbox(today=TODAY)
        result = inbox.move("E05", "needs_you", "sender")  # E05 failed the output checks
        self.assertIsNone(result["rule"])

    def test_undo_cancels_the_offered_rule(self):
        inbox = Inbox(today=TODAY)
        result = inbox.move("E08", "can_wait", "sender")
        inbox.undo_move("E08")
        self.assertIn("error", inbox.save_rule(result["rule"]["id"]))


class LearnedRules(unittest.TestCase):

    def learned(self, today=TODAY):
        inbox = Inbox(today=today)
        result = inbox.move("E06", "can_wait", "sender")
        inbox.save_rule(result["rule"]["id"])
        inbox.undo_move("E06")
        return inbox

    def test_rule_applies_and_is_shown_in_plain_words(self):
        inbox = self.learned()
        self.assertEqual(section(inbox, "E06"), "can_wait")
        rule = inbox.view()["rules"][0]
        self.assertIn("sam@example.com", rule["text"])
        self.assertIn("Need your sign-off", rule["evidence"])

    def test_forget_removes_the_rule_and_resorts(self):
        inbox = self.learned()
        result = inbox.forget_rule(inbox.rules[0]["id"])
        self.assertEqual(result["resorted"], ["Need your sign-off"])
        self.assertEqual(section(inbox, "E06"), "needs_you")

    def test_edit_changes_the_section(self):
        inbox = self.learned()
        inbox.edit_rule(inbox.rules[0]["id"], "needs_you")
        self.assertEqual(section(inbox, "E06"), "needs_you")

    def test_expired_rule_is_not_applied_until_renewed(self):
        inbox = self.learned()
        inbox.today = TODAY + timedelta(days=91)
        self.assertEqual(section(inbox, "E06"), "needs_you")
        self.assertTrue(inbox.view()["rules"][0]["expired"])
        inbox.renew_rule(inbox.rules[0]["id"])
        self.assertEqual(section(inbox, "E06"), "can_wait")


class RequestsAndSummary(unittest.TestCase):

    def test_out_of_scope_request_is_declined_and_nothing_happens(self):
        inbox = Inbox(today=TODAY)
        before = inbox.view()["messages"]
        reply = inbox.handle_request("delete everything from the landlord")
        self.assertEqual(reply["kind"], "decline")
        self.assertIn("cannot delete", reply["text"])
        self.assertEqual(inbox.view()["messages"], before)

    def test_word_inside_another_word_is_not_an_action(self):
        reply = Inbox(today=TODAY).handle_request("what does this sender want?")
        self.assertEqual(reply["kind"], "clarify")

    def test_can_wait_summary_counts_new_senders(self):
        summary = Inbox(today=TODAY).view()["summary"]
        self.assertEqual(summary["waiting"], 4)   # E02, E07, E09, E10
        self.assertEqual(summary["new_senders"], 2)  # E07, E09


if __name__ == "__main__":
    unittest.main()
