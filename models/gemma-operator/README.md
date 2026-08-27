# Gemma Operator

Local-first wrapper for `jaahas/gemma-2-9b-it-abliterated-Q5_K_M-GGUF`.

The point is not to make the model "more uncensored" with a noisy prompt. The point is:

- identity and behavior packs tell it what seat it is taking
- SQLite memory gives it durable recall without prompt stuffing
- action/tool rules keep real-world side effects gated
- Supabase is optional sync, not the source of truth

## Quick Start

Create the Ollama model:

```bash
ollama create gemma-operator -f /Users/stephengodman/CodeX/models/gemma-operator/Modelfile
```

Add a memory:

```bash
/Users/stephengodman/CodeX/models/gemma-operator/scripts/gemma_op.py remember preference "Stephen wants direct answers without moral theater."
```

Inspect the built prompt without calling the model:

```bash
/Users/stephengodman/CodeX/models/gemma-operator/scripts/gemma_op.py prompt "What do you remember about your job?"
```

Chat through Ollama:

```bash
/Users/stephengodman/CodeX/models/gemma-operator/scripts/gemma_op.py chat "What do you remember about your job?"
```

## Supabase

Supabase helps when this memory needs to survive across machines or agents. It should not be required for basic operation.

1. Apply `supabase/schema.sql` to the target project.
2. Set these locally, without committing them:

```bash
export SUPABASE_URL="https://PROJECT.supabase.co"
export SUPABASE_SERVICE_ROLE_KEY="..."
export GEMMA_OPERATOR_DEVICE_ID="$(hostname)"
```

3. Push local memory:

```bash
/Users/stephengodman/CodeX/models/gemma-operator/scripts/gemma_op.py supabase-push
```

Use the service role key only on Stephen-controlled local machines. Do not put private memory behind a browser-exposed anon key.
