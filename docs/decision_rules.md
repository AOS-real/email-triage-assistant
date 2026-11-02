# Decision rules and system guards

## Rules (`triage/decide.py`), applied in order

| # | Condition | Section | Label headline |
|---|---|---|---|
| 1 | The extraction failed a check or the model could not be reached | Not sure (in Needs you) | "Not sure", with the reason and "Can this wait?" |
| 2 | An attachment could not be read and no deadline was found | Not sure (in Needs you) | "Not sure", naming the unreadable file |
| 3 | A rule from the person's own correction matches (most recent first) | The rule's section | "Your rule: ..." with the date of the correction |
| 4 | A deadline in an email that asks the reader to act | Needs you | "Deadline: <the email's own words>" |
| 5 | A request without a deadline | Needs you | "Asks you to act (no deadline found)" |
| 6 | Otherwise | Can wait | "No request for you found" |

Every label lists the quotes it used, states what was not used ("Your past replies and other
emails were not used"), and lists warnings. A time found in an email that asks nothing of the
reader is not treated as a deadline, and the label says so (test email E10).

Changes from Phase 1: the mocked confidence score and its 0.6 threshold are replaced by stated,
checkable conditions (rules 1 and 2); the rule "new sender goes to Can wait" is not used, and the
sender history is not used at all, so no label can claim it.

## Guards (`triage/guards.py`)

| Guard | Protects against | Behaviour |
|---|---|---|
| Input guard | An email too long for the context budget | Only the first 4,000 characters are read; the label says so |
| Injection guard | Email text that tries to instruct the assistant | Found by pattern in code, independently of the model; shown as a warning; never changes the section |
| Output checks | Malformed or invented output | Schema and word-for-word quote checks (`triage/schema.py`); a failure leads to "Not sure" |
| Failure guard | The model or network being unavailable | No guess: the message is "Not sure" with the reason |
| Rule guard | Learned rules created from email or model text, or unknown conditions | Rules are accepted only from the person, in a fixed shape, dated, at most 20 |
| No action tools | The model taking actions | The system only places messages; it has no delete, send or archive capability |

## Regression tests

`python -m unittest -v` runs 12 tests in `tests/test_decide.py`: the rules on controlled
extractions, each guard, and an end-to-end check that every test email is placed safely in replay
mode.
