# Reusable creature viewer checks

Use `python3 tools/run_creature_review.py` for local browser checks and captures. Its saved command-prefix
approval covers every creature project, so a new project or capture script does not need a separate Chrome
approval. Approval persistence belongs to the client; another machine may need to save the prefix once.

The existing repository HTTP server must be running (default port 8912; override with `--port`). The wrapper
constructs a loopback URL for the project's `review/viewer/`. It accepts these operations:

```sh
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m564_claude check
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m564_claude --token TOKEN playback
python3 tools/run_creature_review.py --project level_generation/creatures/mm8_m564_claude --token TOKEN shots \
  standing:Standing:0:quarter:body walk:Walking:0.5:left:body
```

`check` loads every tier and clip and checks browser errors. `playback` records every clip at normal and half speed
with timed screenshots. `shots` captures the requested clip/time/view/focus. Captures go to `review/playback/`
or `review/shots/`; an active project lease requires its token, and writes use the existing creature lock.
Use `--tier <model-id>` to start with another model from the viewer manifest.

Invoke the wrapper directly with ordinary arguments so the saved prefix matches. When the sandbox blocks Chrome,
use `require_escalated` with the existing `['python3', 'tools/run_creature_review.py']` approval. The wrapper runs
fixed review operations; ordinary texture, manifest and progress preparation remains in the filesystem sandbox.

Validation: `python3 -m unittest discover -s tools -p test_run_creature_review.py`.
