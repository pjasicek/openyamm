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
- docs/projectile_service_moderate_refactor_plan.md
- docs/actor_ai_shared_refactor_plan.md

Use docs/projectile_service_moderate_refactor_plan.md as the authoritative plan for projectile work.
Use docs/actor_ai_shared_refactor_plan.md as the authoritative plan for actor AI work.
Use docs/indoor_outdoor_shared_gameplay_extraction_plan.md only as architectural ownership background.
Do not execute any plan linearly.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent slice, or a tightly related micro-batch if required to keep build passing.
Current priority is the projectile service moderate refactor first, then shared actor AI:
- add projectile coarse frame facts/result types
- add outdoor projectile frame fact collection
- implement updateProjectileFrame
- switch outdoor projectile loop to facts/result
- remove or privatize old projectile frame-decision layer
- then move to the actor AI task queue
Run the documented build/tests.
Fix regressions you introduce.
Update TASK_QUEUE.md, PROGRESS.md, and the relevant subsystem plan progress section with concrete evidence.
Do not mark completion just because a helper, adapter, or callback exists.
Completion requires the subsystem done definitions and root ACCEPTANCE.md to be satisfied.
Stop only after finishing the current slice, recording evidence, and leaving the repo in a buildable state.
If ownership or scope is unclear, consult only the relevant sections of the active subsystem plan and architectural
background, then continue.
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
