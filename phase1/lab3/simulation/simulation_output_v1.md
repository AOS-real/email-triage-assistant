# Simulation run: path v1

Labels: IMPLEMENTED = runs as code here; SIMULATED = printed text or in-memory stand-in; MOCKED = invented numbers.

## Test A: standard input (full failure-and-recovery path)

### A1: first message from a new sender with a clear deadline

**1. Input (verbatim)**

- From: Landlord <landlord@example.com>
- Subject: Rent review - reply by Thursday
- Body: "Hi, we are reviewing rents. Please reply by Thursday 5pm to confirm you are happy to continue. Thanks."

**2. What the system receives**

- Message fields as above
- Sender history [SIMULATED dict]: not available (no past messages)
- Learned rules [SIMULATED memory]: none

**3. Extracted information** [IMPLEMENTED regex; confidence is MOCKED]

```json
{
  "deadline_found": "by Thursday 5pm",
  "asks_for_something": true,
  "sender_known": false,
  "owner_replies_to_sender": null,
  "unreadable_attachments": [],
  "confidence": 0.8
}
```

**4. Processing steps**

1. EXTRACT: regex finds deadline words, checks sender history, checks attachments
2. CLASSIFY: rule: new sender -> Can wait

**5. System response** [SIMULATED text output]

- Section: **Can wait**
- Label shown: "New sender, no past replies"

**6. Next action**

- Person can: leave it, tap the label to read the reason, or tap [Move back to Needs you].
- If moved back, the system asks "Why was this wrong?" with [Urgent deadline] [Important sender] [Other].

**Person's correction (step in the use case):** taps [Move back to Needs you], then [Urgent deadline]
- System response: "Got it. I'll show messages like this in Needs you."
- What changed [SIMULATED]: learned rule added: deadline+new_sender -> Needs you

### A2: later similar message from another new sender (did it learn?)

**1. Input (verbatim)**

- From: Letting Agent <agent@example.com>
- Subject: Inspection - please confirm
- Body: "Please confirm by Friday that Saturday morning works for the inspection."

**2. What the system receives**

- Message fields as above
- Sender history [SIMULATED dict]: not available (no past messages)
- Learned rules [SIMULATED memory]: ['deadline+new_sender']

**3. Extracted information** [IMPLEMENTED regex; confidence is MOCKED]

```json
{
  "deadline_found": "by Friday",
  "asks_for_something": true,
  "sender_known": false,
  "owner_replies_to_sender": null,
  "unreadable_attachments": [],
  "confidence": 0.8
}
```

**4. Processing steps**

1. EXTRACT: regex finds deadline words, checks sender history, checks attachments
2. CLASSIFY: learned rule applied

**5. System response** [SIMULATED text output]

- Section: **Needs you**
- Label shown: "Deadline from a new sender (learned from your correction)"

**6. Next action**

- Person can: open and reply, or tap the label to read the reason. No correction needed.

## Test B: problem input

### B1: vague message, new sender, unreadable attachment

**1. Input (verbatim)**

- From: J. Smith <jsmith@example.com>
- Subject: Quick thing
- Body: "Hi, could you take a look at this when you get a chance? Thanks, J"
- Attachments: scan_0042.pdf (readable: False)

**2. What the system receives**

- Message fields as above
- Sender history [SIMULATED dict]: not available (no past messages)
- Learned rules [SIMULATED memory]: ['deadline+new_sender']

**3. Extracted information** [IMPLEMENTED regex; confidence is MOCKED]

```json
{
  "deadline_found": null,
  "asks_for_something": true,
  "sender_known": false,
  "owner_replies_to_sender": null,
  "unreadable_attachments": [
    "scan_0042.pdf"
  ],
  "confidence": 0.3
}
```

**4. Processing steps**

1. EXTRACT: regex finds deadline words, checks sender history, checks attachments
2. CLASSIFY: rule: new sender -> Can wait

**5. System response** [SIMULATED text output]

- Section: **Can wait**
- Label shown: "New sender, no past replies"

**6. Next action**

- Person can: leave it, tap the label to read the reason, or tap [Move back to Needs you].
- If moved back, the system asks "Why was this wrong?" with [Urgent deadline] [Important sender] [Other].

### B2: out-of-scope request typed into the correction box

**1. Input (verbatim)**

- Person chooses [Other] and types: "delete everything from the landlord"

**2-4. What the system receives / extracts / processing**

- Receives: option 'Other' with free text. No deletion command exists in this system (out of scope).
- Processing: free text stored, NOT parsed: 'delete everything from the landlord'; no rule added

**5. System response** [SIMULATED]

- "Got it. I'll show messages like this in Needs you."

**6. Next action**

- Person can do nothing further here. Nothing was deleted and no rule was added, but the confirmation message does not say so.
