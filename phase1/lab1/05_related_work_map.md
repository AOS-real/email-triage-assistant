# Related-work map and gap sentence

## Themes (two or three; name each in four words)

### Theme A — Explanations and over-reliance effects
- Vasconcelos et al. (2023), doi 10.1145/3579605: shows that over-reliance falls when an explanation makes checking the AI cheaper, and that people decide whether to engage with an explanation by weighing its cost against its benefit (five studies, 731 participants).
- Bansal et al. (2021), doi 10.1145/3411764.3445717: shows that explanations did not raise team accuracy and instead made people more likely to accept the AI's recommendation, whether or not it was correct.

### Theme B — Other cues shaping reliance
- Kim et al. (2025), doi 10.1145/3706598.3714020: shows that in an LLM question-answering task (N=308), explanations increased reliance on correct and incorrect answers, while sources and inconsistencies reduced reliance on incorrect ones.
- Kim et al. (2024), doi 10.1145/3630106.3658941: shows that first-person uncertainty wording ("I'm not sure, but...") lowered agreement with an LLM and improved accuracy (N=404, medical questions).

### Theme C — Reviews of automation bias
- Romeo & Conti (2025), doi 10.1007/s00146-025-02422-7: a review of 35 studies finding that explainable AI often raises perceived acceptability without improving accuracy or reducing bias, and pointing to user engagement and verification as the better lever.

## Gap sentence

These sources establish that explanations can raise or lower reliance depending on how costly they make checking (A), that other cues such as sources, inconsistencies and uncertainty wording also change reliance (B), and that explanations often fail to reduce automation bias (C), but none shows whether making the signals behind an email-triage assistant's sorting decisions visible leads people to check and correct wrongly sorted messages; that is the gap this project addresses.

### Three tests
- every phrase in the first half carries a theme letter: yes (A, B, C).
- the second half is a question a study could answer within the eleven-week module: yes, as a small user study. For example, compare an inbox sorted with and without a "why this was sorted" signal, and count how often participants open and correct messages the assistant got wrong. (My suggestion for the design; adjust it to your module.)
- it is a gap in the literature, not a gap in my reading: only partly tested. The five sources above are all in decision-making or question-answering tasks, not email. Two quick web searches for email triage plus explanation, reliance or checking returned vendor blog posts and email-triage papers on how people triage (Microsoft Research, "Email Triage: Challenges and Opportunities"; a Waterloo seminar on email triage and deferral) that I did not read, and none looked like a study of explanations and checking in email triage. That is not proof of absence. Before you state "none shows" in a report, run one more search (for example, "email" AND "explanation" AND "reliance" in Google Scholar) and screen the first results.

Other verified source not used here: Buçinca et al. (2021), doi 10.1145/3449287, on cognitive forcing functions, which would fit Theme A.
