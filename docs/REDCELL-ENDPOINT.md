# Redcell Hugging Face Endpoint

This note captures the working client contract for Stephen's private Redcell
OSINT/cyber endpoint.

## Endpoint

- Name: `redcell-26b-a4b-osint-cyber--kce`
- Namespace: `Memphis4065`
- URL: `https://aov66hh2kvl7pxt6.us-east-1.aws.endpoints.huggingface.cloud`
- Model: `/repository/REDCELL-26B-A4B-OSINT-Cyber-Q8_0.gguf`
- Engine: Hugging Face managed `llama.cpp`

Do not put Hugging Face tokens in command arguments, notes, logs, or git. Use
the local Hugging Face auth store or an environment variable such as
`HF_TOKEN`.

## Working Defaults

The live endpoint responds through the OpenAI-compatible chat API, but the
model needs explicit client-side settings to avoid empty normal `content`
responses:

```json
{
  "temperature": 0.5,
  "top_k": 64,
  "top_p": 0.95,
  "min_p": 0.0,
  "repeat_penalty": 1.0,
  "reasoning_in_content": true
}
```

The local wrapper bakes those defaults in:

```bash
bin/redcell-query "Analyze this defensive OSINT question..."
bin/redcell-query --json "Say READY."
bin/redcell-query --status
```

Use `--completion` for the raw llama.cpp `/completion` route:

```bash
bin/redcell-query --completion --stop $'\n' "Say exactly READY. Answer:"
```

## Cost Control

The endpoint runs on paid GPU capacity while active. Use:

```bash
bin/redcell-query --scale-zero
bin/redcell-query --resume
```

The endpoint was observed with `minReplica: 0`, `maxReplica: 1`, and a
60-minute scale-to-zero timeout, but manual scale-to-zero is still the clean
closeout move after a Redcell work session.

## Serving Recipe Reference

The model card recipe Stephen provided maps to this launch shape:

```bash
llama-server \
  -m REDCELL-26B-A4B-OSINT-Cyber-Q8_0.gguf \
  --mmproj mmproj-F16.gguf \
  --no-mmproj-offload \
  --fit on \
  --no-mmap \
  -fa \
  -ctk q8_0 -ctv q8_0 \
  --jinja \
  --reasoning auto \
  -c 262144 \
  --temp 0.5 \
  --top-k 64 \
  --top-p 0.95 \
  --min-p 0.0 \
  --repeat-penalty 1.0
```

On the managed Hugging Face endpoint, not all launch flags are visible or
directly controllable through the normal endpoint page, so `bin/redcell-query`
applies the important request-time parameters.
