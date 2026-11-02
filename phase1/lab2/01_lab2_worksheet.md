# Lab 2 worksheet

Use this file for the written notes in all five phases. The Canvas page gives the instructions. This is the only Markdown file you need to complete. You do not need to write paragraphs.

## What to do

Work through the five phases on the Canvas page:

1. Write one inference about what the system senses, infers and does.
2. Draw the interaction flow as a loop from the person's goal to system feedback.
3. Draw the normal interaction as a storyboard with as many moments as you need.
4. Show what happens when the inference is wrong and how the person recovers.
5. Choose one design check and draw an improvement into the storyboard.

Submit this worksheet with the three images you make for phases 2, 3 and 4.

## 1. Your interaction

Problem from Lab 1:

People who want to check and question why an AI email-triage assistant made a recommendation cannot do so, because the system sorts their email but hides the signals behind each decision.

What should the system sense, infer and do?

- Senses: sender (and whether the person has replied to them before), subject line and message text, deadline words and dates, and what the person has done with similar messages (opened, replied, moved, ignored).
- Infers (one thing): "this message can wait" (low priority).
- Does: moves the message to a "Can wait" section of the inbox, and shows a short "why" next to it (for example, "Newsletter sender, you have never replied").
- Channel: a visual label in the inbox list. Tapping the label opens the full "why" and a button to move the message back.

When could that inference be wrong?

- A new sender writes with something urgent (for example, a landlord or a university), so there is no history to go on.
- A real person writes in a newsletter-like or very short style, so it looks like low-value mail.
- The person's situation has changed (for example, they are job hunting), so past behaviour no longer predicts what matters.
- A deadline is written in an unusual way ("by end of play Thursday") and the system misses it.
- A forwarded or long thread hides the one new line that matters.

## 2. Your flow

Draw one image that joins these five parts into one interaction loop. Use one labelled box for each part and connect the boxes with arrows. After the feedback, connect the arrow back to the person's goal:

1. Person's goal
2. What the system senses
3. What the system infers
4. What the system does and through which channel
5. What feedback the person receives

## 3. Your normal-interaction storyboard

A storyboard is a sequence of frames. Each frame shows one moment in the interaction, including what the person does, what the system does and what the person sees next. It can be hand-drawn or made in slides, Figma or another tool. Use as many frames as you need to make the interaction clear. It does not need polished artwork.

Make sure the storyboard shows the person's goal, the important actions, the system's action, the feedback and any next step or recovery.

Notes on my storyboard (six frames):

1. Goal: the person opens a busy inbox with little time and wants to get through it without missing anything important.
2. System acts: the assistant has sorted the new mail into "Needs you" and "Can wait". Each message in "Can wait" has a short "why" label.
3. Person sees: the "Can wait" section is collapsed with a count, so the person deals with "Needs you" first.
4. Person checks: the person taps a "why" label on one message and sees the full reason ("Newsletter sender, you have never replied") and a "Move back" button.
5. Person agrees: the reason makes sense, so the person closes it and leaves the message where it is.
6. Next step: the person moves on to the next message. If the reason were wrong, "Move back" is the recovery (shown in Phase 4).


## 4. Your failure-and-recovery storyboard

Draw a second storyboard for this phase. This is the failure-and-recovery storyboard, not the Phase 2 flow. Use as many frames as you need to show the wrong inference, how the person notices, the recovery and what the system should learn. Include:

- What wrong inference does it make?
- How does the person notice?
- How do they recover?
- What should the system learn?

Notes on my failure-and-recovery storyboard:

- Wrong inference: a message from a new sender (a landlord) with a deadline ("reply by Thursday") is sorted into "Can wait". The label says "New sender, no past replies", which treats a lack of history as low priority.
- How the person notices: the person opens the collapsed "Can wait" section, sees the deadline in the message preview and taps the "why" label. The reason ("New sender, no past replies") does not match what the message says.
- Recovery action: the person taps "Move back to Needs you". The system then asks one question: "Why was this wrong?" with the options "Urgent deadline", "Important sender" and "Other". The person taps "Urgent deadline" and replies to the message.
- What the system should learn: a deadline in a message from a new sender should raise priority, not lower it. The system says "Got it, I'll show messages like this in Needs you" and applies it to the next similar message.

## 5. Check the storyboard with a secondary user

Look at your Phase 3 storyboard from the perspective of a secondary user, someone else who would use the system. Choose one question below, pick one frame and revise it so the interaction is clearer for that person:

- Is it apparent what the system can do?
- Is it apparent how well the system can do it?
- Is it apparent why the system acted?
- Can the person correct it?
- Can the person see the consequences of an action?

Show the revised frame in your storyboard. In the worksheet, write:

- Which question did you choose?
- Which frame did you change?
- What was unclear?
- What did you change and why?

Notes for Phase 5 (secondary-user storyboard, shown as a separate image):

- Secondary user: a colleague who covers the owner's inbox for a week (a delegate). They did not set up the assistant and do not know the owner's habits.
- Question I chose: "Is it apparent why the system acted?"
- What was unclear: in the Phase 3 storyboard (frames 2 and 4) the reason chips and panel say things like "You never reply". For the delegate, "you" is the owner, so it is unclear who never replies. The delegate also cannot tell what signals the assistant looked at, or what it did not find.
- What I changed: (1) the reason names who it refers to ("Owner has never replied to this sender"). (2) The reason panel lists the signals checked: sender history, subject and text, deadline words, and shows what it did not find ("No deadline words found"). (3) Each reason has a plain-language confidence line ("Fairly sure this can wait"). (4) The delegate sees "Why this section?" text under the "Can wait" heading, so the reason is visible without tapping each chip. (5) The "Move back" button is kept.
- Why: a delegate has no history to fill in the gaps, so the reason has to say who, what was checked and how sure the assistant is. That lets them decide whether to trust the sorting or move a message back without asking the owner.

## Save

Submit this worksheet, one flow image, one normal-interaction storyboard image and one failure-and-recovery storyboard image (plus the secondary-user storyboard image from Phase 5, as the Canvas page asks). Use placeholders instead of real names, faces or private messages.
