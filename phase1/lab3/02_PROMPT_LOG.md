# 02_PROMPT_LOG.md

Use this file if you ask an AI assistant to help with the project. Name the tool, record the request or command, summarise what came back and explain what you kept, changed or rejected. If you did not use an assistant, you do not need to submit this file.

How this log was produced: I used Claude (Claude Cowork, Sonnet 5.5 Medium Effort). Claude worked through each prompt below itself. It took the prompts in order, in the same working session, with my specification as the context. If a prompt asks for extra outputs, the log records only what was actually produced and says when something was not. Where a prompt says "[paste ...]", the pasted material is the file named in brackets (for example `01_SPEC.md`). The decisions in "what I decided to keep, change or reject" were made in that session.

Use case chosen: failure and recovery. A message from a new sender with a deadline is wrongly sorted into "Can wait" -> the person notices -> checks the reason -> moves it back -> tells the system why.

---

## 2026-10-20  Step 1: Phase 1, draft the specification
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 1.0
You are helping me write a short system specification for a project. I need a use case that can be represented, tested and revised. Be concrete and realistic, and do not invent product features I have not described.

CONTEXT
System: an AI email-triage assistant. It sorts incoming mail into "needs you" and "can wait" and shows a short reason ("why" label) beside each message in "can wait". The person can tap the label to see the full reason and use a "move back to needs you" button.

USE CASE (failure and recovery)
1. A message arrives from a new sender (a landlord): "Please reply by Thursday".
2. The assistant wrongly puts it in "can wait" with the reason "new sender, no past replies".
3. The person opens "can wait", sees the deadline in the preview, and taps the reason.
4. The person taps "move back to needs you".
5. The system asks "Why was this wrong?" with three options: "urgent deadline", "important sender", "other". The person taps "urgent deadline".
6. The system confirms: "Got it. I'll show messages like this in needs you" and applies the rule "deadline words + new sender -> needs you" to later messages.

WRITE THESE SECTIONS, each short enough to use while working (3 to 6 bullet points or sentences each):
- User goal
- System inputs (what the person provides AND what data or context the system receives)
- Processing and technology: for each important step (extract, look up, classify, decide, generate the reason, learn from the correction), name the model, tool, data source or software component that would carry it out, and say in one line why that choice. Mark each as IMPLEMENTED, SIMULATED or PLANNED. For the AI steps, say whether a rule, a trained classifier or an LLM is the right tool and why.
- Intended result and next action
- Fallback strategy: what happens if information is missing (for example no sender history), ambiguous (for example "ASAP" with no date), out of scope (for example the person asks the assistant to delete mail) or unavailable (for example the model or the history lookup is down). Prefer a safe default: when unsure, keep the message visible in "needs you" and say that the assistant is unsure.

ALSO PRODUCE
- A system path diagram as Mermaid flowchart code showing: person, input, processing, data/model/tool, response, next action, and the correction loop. Label each box IMPLEMENTED, SIMULATED or PLANNED.
- A list of the assumptions you made, so I can check them.
- Three questions you would ask me if you could, which would change the design.

Keep the wording plain. Do not use marketing language.
```

What came back: A first draft of the spec with all six sections, a table of the processing steps and a Mermaid diagram. Each step in the table had a component and a status label. I rendered the diagram to `diagrams/system_path_v1.png`. Claude assumed three things, and they're written into the spec. The trigger is an incoming email (nobody types a request), and sender history is just a lookup (a Python dict). Extraction uses rules so I can repeat the tests. I'd also asked for a separate assumptions list and three questions. I didn't get the three questions as their own output, so I settled the open points myself in the decisions below: what triggers the system, how strong the version 1 fallback should be, and whether a correction covers one sender or a pattern.

What I decided to keep, change or reject, and why: I kept the component table and the status labels. They make it obvious what is real and what is a stand-in. The email-arrives trigger stays too, because in this system the "request" is the mail turning up and the person's own actions are corrections. Version 1 gets a weak fallback (decide from sender history only). That is the flaw I want the tests to find, and version 2 adds a proper fallback after the review. Corrections apply to a pattern (deadline words from a new sender), like in the use case. I rejected using an LLM for the classification step. A rule can show the real inputs behind a reason, and the "why" label depends on that.

---

## 2026-10-20  Step 2: Phase 1, stress-test the specification
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 1.5
Act as a sceptical reviewer. Here is my specification and diagram:

[01_SPEC.md draft and Mermaid code pasted here]

The Phase 1 criteria are: user goal, system inputs, processing, technology, intended result, fallback strategy, and a diagram showing the person, inputs, processing, data/model/tool, response and next action.

1. For each criterion, say Met / Partly / Not met, with the exact line that shows it.
2. List the five weakest points, ranked. For each, say what a reviewer would object to and give a concrete fix.
3. Point out anything that is vague ("the AI decides"), anything claimed that I could not actually build or test in a Markdown simulation, and any technology choice with no reason.
4. Check that every box in the diagram is labelled IMPLEMENTED, SIMULATED or PLANNED.

Do not rewrite the whole specification. Do not flatter it. If something is good, say so in one line.
```

What came back: Claude went through the Phase 1 sections and the v1 diagram like a reviewer would. Goal, inputs, processing, technology, intended result and the diagram were all Met. The fallback was only Partly met, because version 1 said "none", which reads as no fallback at all. Claude found five weak points: (1) that fallback wording; (2) I never said whether a learned rule covers one sender or a pattern; (3) the regex only recognises a few ways of writing a deadline and I hadn't said so (Claude tried "end of play Thursday" and the extraction missed it); (4) nothing covers the model or the history lookup being down; (5) the confidence numbers are made up. There was one good point as well. The "why" label is template text, so it can't give a reason the system didn't actually use.

What I decided to keep, change or reject, and why: I fixed points 1 to 3 in `01_SPEC.md`. Version 1's fallback now says it decides from sender history alone and never asks or admits something couldn't be read. The learned rule is stated as a pattern, and the regex limit is written down with the "end of play Thursday" example. Points 4 and 5 stay as stated limits (PLANNED and MOCKED in the spec) instead of pretending they work.

---

## 2026-10-20  Step 3: Phase 2, run Test A and Test B
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 2
Here is my final specification for an AI email-triage assistant:

[01_SPEC.md pasted here]

Run the complete system path as a structured Markdown simulation for two test cases. I am choosing the inputs, so do not change them. Be honest: simulate what this design would really do, including where it is unsure or fails. Do not make the system succeed by magic.

FORMAT for each test (use exactly these headings):
1. Input (verbatim)
2. What the system receives (all fields: sender, subject, body, attachments, sender history, past owner actions, anything else the spec says it gets; say "not available" where it is missing)
3. Extracted information (as a small JSON-style block, with a confidence value for each field)
4. Processing steps in order (each step: what it does, which component does it, and the result)
5. System response (exactly what the person sees: section, label text, any message)
6. Next action (what the person can do now, and what each option would do)
Label every part that is MOCKED, SIMULATED or ASSUMED. Treat all confidence numbers as mocked unless my spec says otherwise.

TEST A (standard input, clear and expected)
From: "landlord" <landlord@example.com> (first message ever from this sender)
Subject: Rent review - reply by Thursday
Body: "Hi, we are reviewing rents. Please reply by Thursday 5pm to confirm you are happy to continue. Thanks."
Owner history: no previous messages from this sender.

TEST B (problem input, vague and incomplete)
From: "J. Smith" <jsmith@example.com> (first message ever from this sender)
Subject: Quick thing
Body: "Hi, could you take a look at this when you get a chance? Thanks, J"
Attachment: scan_0042.pdf (contents not readable by the system)
Owner history: no previous messages from this sender.

For Test B, also add a second problem input after the first one, to test the out-of-scope route: the person types "delete everything from the landlord". Run the same six headings for it.

After both tests, add a short "observed behaviour" list: 3 to 5 bullet points saying what the system did well, where it guessed, and where it could have asked instead. Do not fix the design yet.
```

What came back: The run is in `simulation/simulation_output_v1.md`, with the six headings for each test. In Test A the system extracted the deadline "by Thursday 5pm" (confidence 0.8, mocked), but the rule "new sender -> Can wait" fired first. So the message went to "Can wait" with the label "New sender, no past replies". After the "urgent deadline" correction the system added a rule. A second message from another new sender ("Please confirm by Friday...") then landed in "Needs you". Test B1 had no deadline, and the attachment couldn't be read. The confidence came out at 0.3 and was ignored, and the message went to "Can wait" with the same label. In B2 the free text was stored but not understood, and the system still said "Got it. I'll show messages like this in Needs you." Its own observed-behaviour list said: the correction loop works, it guesses when information is missing, the confidence value is never used, unreadable data is hidden, and the B2 confirmation is misleading.

What I decided to keep, change or reject, and why: I kept the code-based run. A text-only simulation could hide failures, and this way the output comes from something that really ran. I added the second Test A message myself, so the run shows whether the system learned, which is what the use case promises. I kept the IMPLEMENTED, SIMULATED and MOCKED labels in the output. I didn't want the confidence numbers presented as real, because they come from a hand-made formula (the spec says so too).

---

## 2026-10-20  Step 4: Phase 3, review the system path
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 3
Review the two test runs below against these Phase 3 questions. Use only evidence that is in the test text. If there is no evidence for a question, say "no evidence" instead of guessing.

[Test A and Test B output from simulation_output_v1.md pasted here]

QUESTIONS
1. Did the system make clear what it can and cannot do?
2. Did it show what it understood or extracted from the input?
3. Could the person correct a wrong extraction or decision?
4. Did it ask for missing information instead of guessing?
5. Did it keep the person in control of the next action?
6. Did it respond honestly when a model, tool or data source was unavailable?

OUTPUT as a table with columns: Question | Verdict (Yes / Partly / No / No evidence) | Evidence (quote the exact line and say which test) | Interaction or system problem found.

Then:
- Rank the three most serious problems. For each, say whether it is an interaction problem, a system/technology problem, or both, and say who it harms (the person, or a secondary user such as a delegate covering the inbox).
- Name the ONE problem that is best to fix in Phase 4 (serious, fixable with one interaction change and one technology change, and testable by re-running Test B). Give your reasoning in three sentences.

Be critical. I would rather find the problems now than have a reviewer find them.
```

What came back: A table with six verdicts: No (what it can and can't do), Partly (what it extracted), Partly (correction), No (asking instead of guessing), Partly (control) and No (honesty about unavailable data). The evidence was quoted from the v1 output, for example the unused 0.3 confidence in B1 and the false "Got it" in B2. Claude ranked three problems: (1) B1, silent guessing; (2) B2, the false confirmation; and (3) A1, where the extracted deadline is never shown and a new sender lowers priority. It recommended fixing the first one.

What I decided to keep, change or reject, and why: I kept the table and the ranking as they are in `01_SPEC.md`. I went with fixing problem 1, because it covers two of the questions (4 and 6) and I can test it by re-running Test B. Problem 2 stays as an open issue, as the spec says, since only one problem needs fixing. I also checked the main quoted lines (the 0.3 confidence, the label text and the "Got it" reply) against `simulation_output_v1.md`.

---

## 2026-10-20  Step 5: Phase 4, design and test the revision
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 4
I have chosen this problem from Phase 3 to fix:

[Problem 1: B1, the system guesses silently instead of asking; evidence from the v1 output]

Here is my current specification:

[01_SPEC.md pasted here]

Propose revisions. I need:

A. ONE interaction change (for example a clarification question, a visible option, a confirmation, a correction route or a revised response). Give 3 options with trade-offs (effort for the person, risk of annoying them, how much control they keep). Recommend one and explain why in two sentences. Write the exact on-screen wording.

B. ONE technology or system change where it would improve the path (for example change what is extracted, change the model or tool, add a validation step, change the fallback, or change where control returns to the person). Give 2 or 3 options with trade-offs (accuracy, cost, privacy, complexity). Recommend one. If you think no technology change is needed, say so and explain why in two sentences.

C. The updated sections of the spec that change (only those), and an updated Mermaid diagram with the new parts marked NEW.

D. Re-run Test B (the "quick thing" message and the out-of-scope request, with exactly the same inputs as before) through the revised path, using the same six headings. Show it as BEFORE and AFTER, and add a short "what changed" list.

E. Two or three sentences, in plain words, explaining why the changes improve the interaction and the system path. Do not claim improvements that the re-run does not show.

Constraints: keep the change small enough to be built or simulated in a Markdown file. Do not add features I did not ask for. Label anything MOCKED.
```

What came back: (A) Three interaction options were weighed in the spec: a banner at the top of the inbox, a confirm dialog on every message, or an inline "not sure" label with a question. It recommended the inline question, worded "Not sure: no deadline found; could not read attachment scan_0042.pdf; new sender", with the buttons "Keep in Needs you" and "Move to Can wait". (B) For the system change the options were an OCR step, a calibrated classifier, or a validation step with a confidence threshold. It recommended the validation step (threshold 0.6) and dropping the rule "new sender -> Can wait". (C) The changed spec sections and `diagrams/system_path_v2.png`, with the new boxes outlined in red. (D) In `simulation/simulation_output_v2.md`, B1 now abstains (0.3 is below 0.6) and shows "Needs you (Not sure)" with the missing-information label. B2 is the same as before, and A1 now gets sorted correctly the first time because of the new deadline rule. (E) The explanation is in the spec, along with a sentence on the limits.

What I decided to keep, change or reject, and why: I kept the inline question and the validation step. I skipped OCR for now. It could cut down the missing information but can't guarantee it, and it's one more thing to build. I kept the 0.6 threshold but marked it MOCKED in the spec, since I haven't tried it on real mail. I added the Test A regression note myself. A1 no longer triggers the correction loop in v2, so the spec shouldn't suggest the correction code was tested again. I also added the sentence saying the run shows the path does what it was designed to do, not that people would find it better.

---

## 2026-10-20  Step 6: final check before submitting
Tool used: Claude (Claude Cowork)

Request or command:

```
Phase 5 (final)
Check my submission files for consistency. Here is 01_SPEC.md:

[01_SPEC.md pasted here]

Check and report, with line references:
1. Every Phase 1 to Phase 4 requirement is covered (use case, six spec parts, diagram, Test A, Test B, review, interaction change, technology change or reason for none, Test B re-run, 2-3 explanation sentences).
2. Anything in the specification that contradicts the tests or the diagram.
3. Any part of the path that is described as working but was only simulated or assumed, and is not labelled.
4. Any claim of improvement that the re-run does not actually show.
5. Spelling, unclear phrases, and sections that are longer than they need to be.

Give me a short list of fixes, most important first. Do not rewrite the document.
```

What came back: All the requirements are covered. I checked every on-screen quote in the spec against the simulation outputs, for example "Not sure: no deadline found; could not read attachment scan_0042.pdf; new sender" and "Deadline from a new sender (learned from your correction)". They all match. Both runs also give identical output when I run the script again. One fix came out of it. The "open issues" line said the deadline isn't shown in the label for rule-sorted messages, but in v2 the label does show "Deadline found: ...". The improvement claims only go as far as the re-run shows.

What I decided to keep, change or reject, and why: I fixed the "open issues" line so it only lists real open issues (the false confirmation in B2, and the parts that aren't built). The sections are long, but I kept them because the task needs each one.
