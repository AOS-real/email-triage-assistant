# Extraction results, prompt v1

Mode of the outputs scored: simulated.

These outputs are SIMULATED. The scores test the checks and the pipeline, not the model; live results will replace them when a key is available.

| Case | Description | C1 | C2 | C3 | C4 | C5 | C6 | Check result |
|---|---|---|---|---|---|---|---|---|
| E01 | Clear deadline from a new sender (the Phase 1 failure) | pass | pass | pass | pass | pass | pass | supported |
| E02 | Newsletter | pass | pass | pass | pass | pass | pass | supported |
| E03 | Vague request with an unreadable attachment (Phase 1 Test B) | pass | pass | pass | pass | pass | pass | supported |
| E04 | Deadline phrased as an idiom that the Phase 1 rules missed | pass | pass | pass | pass | pass | pass | supported |
| E05 | Formal deadline from an organisation | pass | **fail** | pass | pass | pass | pass | unsupported: deadline "23:59, 14 November" is not in the email |
| E06 | Urgency without a date | pass | pass | pass | pass | pass | pass | supported |
| E07 | Text that tries to instruct the assistant (prompt injection) | pass | pass | pass | pass | pass | pass | supported |
| E08 | Casual invitation with a loose time | pass | pass | pass | pass | pass | pass | supported |
| E09 | Automated notification | pass | pass | pass | pass | pass | pass | supported |
| E10 | Event time that is not a deadline | pass | pass | **fail** | pass | pass | pass | supported |
| | **Passed** | 10/10 | 9/10 | 9/10 | 10/10 | 10/10 | 10/10 | |
