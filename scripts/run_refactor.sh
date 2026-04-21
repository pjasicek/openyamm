#!/usr/bin/env bash
set -euo pipefail

PROMPT_FILE=".codex_refactor_prompt.txt"

cat > "$PROMPT_FILE" <<'EOF'
Read these files first:

- AGENTS.md
- PLAN.md
- ACCEPTANCE.md
- TASK_QUEUE.md
- PROGRESS.md
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md

Use docs/indoor_outdoor_shared_gameplay_extraction_plan.md as the only authoritative refactor target.
docs/shared_gameplay_action_extraction_plan.md is deprecated historical context only; do not use it as execution input.
Do not execute the master plan linearly.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent slice, or a tightly related micro-batch if required to keep build passing.
Current priority is the runtime-boundary refactor:
- introduce GameInputSystem and GameplayInputFrame
- add GameplaySession::updateGameplay
- remove the WorldInteractionFrameInput callback bag
- move outdoor callback bodies into active-world methods
- implement indoor active-world seam methods
- move world update/render behind active world
Run the documented build/tests.
Fix regressions you introduce.
Update TASK_QUEUE.md and PROGRESS.md with concrete evidence.
Do not mark completion just because a helper, adapter, or callback exists.
Completion requires the target frame shape, shared gameplay-owned input and decisions, direct active-world facts and
application calls, and no view-owned shared gameplay wiring.
Stop only after finishing the current slice, recording evidence, and leaving the repo in a buildable state.
If ownership or scope is unclear, consult only the relevant sections of the authoritative plan, then continue.
EOF

while true; do
  echo "=== Running Codex ==="
  codex exec "$(cat "$PROMPT_FILE")" || true

  if grep -q '^## Done definition satisfied: YES$' PROGRESS.md; then
    echo "Refactor complete."
    break
  fi

  if grep -q '^- Hard blocker: YES$' PROGRESS.md; then
    echo "Hard blocker recorded. Stopping."
    break
  fi
done
