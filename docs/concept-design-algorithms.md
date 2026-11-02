# Concept design: algorithms

Pseudocode for version 2 of the concept (`concept-design.md`). Each algorithm lists the expected
errors it prevents (ER numbers) and its status. Guards are marked **[G1]** to **[G5]**.

Conventions: `section` is one of NEEDS_YOU, NOT_SURE (shown in Needs you) or CAN_WAIT. Constants:
`MAX_BODY = 4000` characters, `MAX_RULES = 20`, `RULE_EXPIRY = 90` days.

---

## A1. Process an incoming email (pipeline)

Prevents ER1 to ER8. IMPLEMENTED (`triage/extract.py`, `triage/decide.py`).

```
procedure PROCESS(email, rules):
    show_acknowledgement(email)                      # A13
    (sent, note) <- INPUT_GUARD(email)               # A2  [G1]
    extraction <- EXTRACT(sent)                      # A3  [G2], A4 [G3]
    extraction.injected <- FIND_INJECTION(email)     # A5  [G4]
    decision <- DECIDE(email, extraction, rules)     # A6
    decision.label <- COMPOSE_LABEL(decision, note)  # A7
    place(email, decision.section, decision.label)
    log(email.id, decision)                          # dated record of what was decided and why (PLANNED)
```

## A2. Input guard and context assembly [G1]

Prevents ER5, ER7. IMPLEMENTED (`guards.guard_input`, `extract.email_as_data`).

```
procedure INPUT_GUARD(email):
    if length(email.body) > MAX_BODY:
        return (copy of email with body cut to MAX_BODY,
                "only the first MAX_BODY characters were read")
    return (email, none)

procedure ASSEMBLE_CONTEXT(email):
    system <- read versioned instruction file          # trusted, written in advance
    user   <- "<email>" + sender + subject + attachment names and readability
              + body + "</email>"                      # untrusted data, never instructions
    # not sent: sender history, learned rules, other emails (data minimisation)
    return (system, user)
```

## A3. Extract facts with a failure guard [G2]

Prevents ER1, ER6. IMPLEMENTED (`extract.extract`, `guards.guard_call`); live model output not yet
run, recorded outputs SIMULATED.

```
procedure EXTRACT(email):
    try:
        if mode = LIVE:
            output <- call model (Claude Sonnet 5.5, medium effort,
                                  structured output with SCHEMA, context from A2)
        else:
            output <- recorded output for email.id
    except any failure:
        return {supported: false, problems: ["the assistant could not read this email"]}
    problems <- CHECK_OUTPUT(output, email)            # A4
    return {output, supported: (problems is empty), problems}
```

## A4. Check the output [G3]

Prevents ER3. IMPLEMENTED (`triage/schema.py`).

```
procedure CHECK_OUTPUT(output, email):
    problems <- schema violations of output          # keys, types, allowed values
    if problems not empty: return problems
    source <- email.subject + email.body
    if output.deadline_text is not null and output.deadline_text not in source:
        add "deadline is not in the email" to problems
    for each quote in output.evidence:
        if quote not in source: add "evidence is not in the email" to problems
    return problems
```

## A5. Find injected instructions [G4]

Prevents ER5. IMPLEMENTED (`guards.find_injection`).

```
procedure FIND_INJECTION(email):
    found <- empty list
    for each sentence in email.body:
        if sentence matches any of:
               "assistant:", "ai:", "ignore previous instructions",
               "(mark|move|archive|delete|forward) (this|all|every) ... mail"
            add sentence to found
    return found                     # reported as a warning; never used by DECIDE to choose
```

## A6. Decide the section

Prevents ER1, ER2, ER8, and applies learned rules. IMPLEMENTED (`triage/decide.py`).

```
procedure DECIDE(email, extraction, rules):
    if not extraction.supported:
        return NOT_SURE with reason extraction.problems[0]
    facts.asks     <- extraction.output.asks_for_action
    facts.deadline <- extraction.output.deadline_text if facts.asks else null    # ER2
    facts.ignored_time <- extraction.output.deadline_text if not facts.asks else null
    unreadable <- attachments of email that could not be read
    if unreadable not empty and facts.deadline is null:
        return NOT_SURE with reason "could not read " + unreadable              # ER8
    for each rule in rules, most recent first:
        if every condition of rule equals the matching fact:
            return rule.section with reason "your rule from " + rule.created
    if facts.deadline is not null: return NEEDS_YOU with headline "Deadline: " + facts.deadline
    if facts.asks:                 return NEEDS_YOU with headline "Asks you to act"
    return CAN_WAIT with headline "No request for you found"
```

## A7. Compose the label

Prevents ER4. IMPLEMENTED (`triage/decide.py`).

```
procedure COMPOSE_LABEL(decision, note):
    label.headline <- decision.headline
    label.used     <- quotes from the email that the rule read
    label.not_used <- ["Your past replies and other emails were not used."]
    if decision.ignored_time: add "the time was found but not treated as a deadline" to not_used
    label.warnings <- injected text (A5) and the input note (A2)
    label.change   <- "Move back" button; for NOT_SURE, "Can this wait?" with two buttons
    return label                     # written by code from the facts used; never by the model
```

## A8. Answer "Can this wait?"

Prevents ER1, ER6, ER8 reaching the person unseen. IMPLEMENTED (`triage/inbox.py`, `static/`).
Changed during the build: answering "Can this wait?" places the message for this time only and
offers no rule, because a Not sure message has no checked facts to learn from.

```
procedure ANSWER_NOT_SURE(email, answer):
    if answer = "Keep in Needs you": MOVE(email, NEEDS_YOU, "Just this once")
    if answer = "Move to Can wait":  MOVE(email, CAN_WAIT, "Just this once")
    show "Undo last move"                                        # A12
```

## A9. Turn a correction into a rule [G5]

Prevents ER9, ER11, ER12, ER13. IMPLEMENTED (`triage/inbox.py`, `guards.validate_rule`).
Changed during the build: version 2 proposed rules on deadline and sender type. Building it showed
that a deadline rule repeats what the default rule already does, and that a sender-type rule
("all organisations") is the over-broad rule of ER9. Rules are therefore learned only about one
sender address; a missed deadline is recorded but teaches nothing; free text is not offered.
The proposed rule is held on the server, so the page can confirm it but cannot alter it.

```
procedure LEARN_FROM_CORRECTION(email, new_section, reason):
    facts <- facts of email used by DECIDE
    if reason = "Just this once":                 return "Nothing was learned"
    if reason = "It has a deadline the assistant missed":
                                                  return "Recorded as a missed deadline; no safe rule"
    if facts is unknown (the email failed its checks): return "Nothing is learned from it"
    condition <- {sender: email.from}             # "This sender matters" / "can always wait"
    rule <- {id, condition, section: new_section, created: today,
             expires: today + RULE_EXPIRY, source: "person", evidence: subject + reason}
    problems <- VALIDATE_RULE(rule, rules)                                   # [G5]
    if a rule with the same condition and section exists: problems += "already learned"   # ER12
    if problems not empty: show problems beside the button; stop
    affected <- count of current messages that rule would move
    show "Mail that <rule in plain words> goes to <section>. This would move <affected> messages."
         with buttons "Save rule" and "Not now"                              # ER9, ER11
    if person presses "Save rule": store rule; show it in What I've learned (A10)

procedure VALIDATE_RULE(rule, rules):
    reject if rule.source is not "person"                  # ER13: never from email or model text
    reject if rule.condition uses a signal outside {sender, deadline, asks_for_action, sender_known, sender_type}
    reject if rule.section is not NEEDS_YOU or CAN_WAIT
    reject if count(rules) >= MAX_RULES
    reject if rule.created is not a valid date
```

## A10. What I've learned: inspect, edit, forget

Prevents ER10, ER13. IMPLEMENTED (`triage/inbox.py`, `static/`). Editing is limited to sending
the sender's mail to the other section.

```
procedure SHOW_LEARNED(rules):
    for each rule, most recent first:
        show plain-language text, evidence ("Because: your move of <subject> (<reason>)"),
             learned and expiry dates, and buttons "Send to <other section> instead" and Forget
        if today > rule.expires: mark expired, offer Renew, and stop applying it   # ER10

procedure EDIT(rule, new_section):
    validate with VALIDATE_RULE and the duplicate check; change the section

procedure FORGET(rule):
    delete the rule; decisions are rebuilt on every request, so no derived copy survives
    re-run DECIDE on every message; show "Forgotten. Re-sorted: <subjects>."
```

## A11. Decline an out-of-scope request

Prevents ER15. IMPLEMENTED (`inbox.handle_request`), by matching whole action words in code;
no model is involved, so a request can never cause an action.

```
procedure HANDLE_REQUEST(text):
    if text asks to delete, send, forward, archive or reply:
        say "I can only sort mail into Needs you and Can wait. I cannot <action>."
        offer the matching manual control ("Select these messages")   # hand back control
        store nothing
    else:
        say what the assistant can do, as a short list of options     # clarify, not "rephrase"
```

## A12. Undo a move

Prevents ER11. IMPLEMENTED (`inbox.move`, `inbox.undo_move`). Changed during the build: the undo
button stays until the next move of that message instead of disappearing after 10 seconds, so a
slow reader is not rushed.

```
procedure MOVE(email, section, reason):
    remember the previous placement of email
    place(email, section)
    show "Undo last move" beside the message
    if Undo pressed: restore the previous placement; cancel any rule offer from this move
```

## A13. Feedback timing

Prevents ER16. PARTLY IMPLEMENTED: the page shows "Sorting..." at once and every action
redraws the inbox; per-message progress and the 10-second fallback are PLANNED, because replay
mode answers instantly and the delays cannot yet be observed.

```
procedure SHOW_ACKNOWLEDGEMENT(email):
    within 0.1 s: show the email in the inbox with "Sorting..."
    if not placed within 1 s: keep "Sorting..." visible with a progress indicator
    when placed: replace with the section and label
    if not placed within 10 s: place as NOT_SURE "The assistant is taking too long"   # with A3
```

## A14. Keep Can wait from being treated as checked

Prevents ER14. PARTLY IMPLEMENTED: the summary line is shown at the top of the inbox; the daily
reminder is PLANNED.

```
procedure CAN_WAIT_SUMMARY(messages):
    n <- count of messages in CAN_WAIT
    new <- count of those from new senders
    show at the top of the inbox: "<n> messages are waiting; <new> are from new senders"
    once a day, if n > 0: show the same line as a reminder (never more often)   # avoid cry wolf
```
