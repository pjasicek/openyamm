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
- docs/headless_to_doctest_migration_inventory.md

Use docs/headless_to_doctest_migration_inventory.md as the authoritative source for the current refactor loop.
Do not execute it linearly.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent migration slice, or a tightly related micro-batch if required to keep the build passing.

Current priority:
- move as many slow headless diagnostics as possible into fast doctest unit tests;
- prefer remaining doctest-direct cases first;
- for doctest-with-adaptation, extract only the smallest reusable seams that unlock multiple tests;
- keep true world/application integration cases headless unless explicitly reclassified;
- if condensing headless execution, preserve per-case identity and clear failure reporting.

Do not copy OpenEnroth code. Use the local OpenEnroth checkout only as behavioral/structural reference when needed.
Do not weaken assertion scope silently during migration.
Do not create broad fake application layers just for tests.
Prefer openyamm_unit_tests / doctest validation for migrated slices.
Run openyamm and targeted headless validation only when the migrated batch still touches headless code or integrated behavior.
Fix regressions you introduce.
Update TASK_QUEUE.md and PROGRESS.md with concrete evidence.
Update ACCEPTANCE.md when criteria are satisfied.

Completion requires root ACCEPTANCE.md done definition to be satisfied.
Stop only after finishing the current slice, recording evidence, and leaving the repo in a buildable state.
If scope is unclear, consult only the relevant sections of the inventory and control files, then continue.
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
