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
- docs/indoor_oe_collision_physics_plan.md
- docs/indoor_outdoor_shared_gameplay_extraction_plan.md

Use docs/indoor_oe_collision_physics_plan.md as the authoritative plan for the current slice.
Use docs/indoor_outdoor_shared_gameplay_extraction_plan.md only as architectural ownership background.
Do not execute the detailed plan linearly.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent slice, or a tightly related micro-batch if required to keep the build passing.

Current priority:
- implement OE-like indoor BLV collision/physics structurally;
- replace simplified destination-position indoor collision with swept nearest-hit iterative collision;
- keep BLV sectors, portals, moving mechanisms, floor/ceiling, and collision application in indoor world code;
- keep shared actor AI as behavior owner and feed it movement/contact facts only;
- remove the temporary reduced indoor actor wall-navigation radius as the final solution;
- remove or gate temporary noisy indoor collision diagnostics before completion.

Do not copy OpenEnroth code. Use the local OpenEnroth checkout only as behavioral/structural reference.
Do not move BLV collision into shared gameplay.
Do not introduce callback bags or adapters that hide ownership.
Prefer doctest/unit tests for pure collision primitives and deterministic resolver behavior.
Use headless tests for integrated BLV behavior only when unit tests would be artificial or too coupled to runtime setup.
Run the documented build/tests.
Fix regressions you introduce.
Update TASK_QUEUE.md and PROGRESS.md with concrete evidence.
Update ACCEPTANCE.md when criteria are satisfied.

Completion requires root ACCEPTANCE.md and docs/indoor_oe_collision_physics_plan.md done definitions to be satisfied.
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
