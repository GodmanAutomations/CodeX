# CodeX Failure Memory

Failure memory stores the mistakes that make CodeX sharper.

Database:
`/Users/stephengodman/Candice-Code/failures/codex-failures.sqlite3`

Helper:
`/Users/stephengodman/Candice-Code/failures/codex_failure.py`

## Purpose

Record practical failures, symptoms, causes, fixes, and prevention rules.

Use this for:

- tool wiring failures
- identity contamination
- smoke-test bugs
- eval false positives or false negatives
- launch/service hangs
- any failure likely to repeat

Do not use this for:

- blame
- private raw transcripts
- secrets
- huge logs
- vague vibes without a prevention rule

## Commands

```bash
/Users/stephengodman/Candice-Code/bin/codex-failure status
/Users/stephengodman/Candice-Code/bin/codex-failure list
/Users/stephengodman/Candice-Code/bin/codex-failure search gemini
/Users/stephengodman/Candice-Code/bin/codex-failure add --key example --symptom "What broke" --cause "Why" --fix "What fixed it" --prevention "How to avoid it"
```
