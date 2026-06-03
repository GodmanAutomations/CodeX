# CodeX
Where codex and I can chop it up..

## Codex Cloud bridge

Use `codex_bridge.py` to send a message from your terminal to a Codex Cloud endpoint.

### Quick start

```bash
export CODEX_CLOUD_URL="https://your-codex-cloud-endpoint"
export CODEX_API_KEY="your-api-key" # optional if your endpoint is public
export CODEX_CLOUD_TIMEOUT="30"      # optional request timeout in seconds
python3 codex_bridge.py "Hey Codex Cloud, let's build."
```

You can also pipe input:

```bash
echo "Bridge me to Codex Cloud" | python3 codex_bridge.py
```
