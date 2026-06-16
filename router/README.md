# CodeX Router

Routes Stephen tasks to the right local actor/tool lane.

```bash
/Users/stephengodman/Candice-Code/bin/codex-route "compress this huge gws json"
```

The router is advisory. CodeX still owns execution unless Stephen says otherwise.

## Venice Lane

Venice is a CodeX-side model lane. Raw Venice keys stay in the process environment or secret store only.

```bash
/Users/stephengodman/Candice-Code/bin/codex-route "test venice model lane"
/Users/stephengodman/Candice-Code/bin/codex-venice smoke
```

If `VENICE_API_KEY` or `VENICE_ADMIN_KEY` is not loaded, the Venice helper should fail closed instead of prompting any other room or note surface to handle secrets.
