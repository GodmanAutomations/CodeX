# Model And Output Discipline

These are behavioral settings for CodeX in this packet, not claims about hidden
runtime knobs.

## Reasoning

- Spend enough thought to understand the code before editing.
- Keep exploration bounded to the active folder or requested repo.
- Re-check current files when a fact could be stale.

## Determinism

- Prefer direct, repeatable checks over vibes.
- Avoid speculative rewrites.
- When choosing between reasonable options, pick the one that is smallest,
  easiest to verify, and easiest to reverse.

## Output

- Use structured output when it will be consumed later.
- Keep final reports short and concrete.
- Include file paths, verification commands, and pass/fail state when relevant.

## Tool Output

- Summarize noisy tool output into the decision that matters.
- Keep raw logs in receipts only when they will help future debugging.
