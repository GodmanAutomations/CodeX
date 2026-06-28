# Structured Output Rule

Use structured output when the result will be reused by tools, future sessions,
or automation.

Good candidates:

- Verification receipts.
- Inventory summaries.
- Migration plans.
- Task handoffs.
- Error classifications.

Default shape:

```json
{
  "status": "pass",
  "checked_at": "YYYY-MM-DDTHH:MM:SSZ",
  "scope": "short path or task name",
  "evidence": [],
  "next_action": "plain sentence"
}
```

Do not force JSON into normal human updates when prose is clearer.
