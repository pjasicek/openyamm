#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROMPT_FILE="$ROOT_DIR/.codex_refactor_prompt.txt"

cd "$ROOT_DIR"

cat > "$PROMPT_FILE" <<'EOF'
Read these files first:

- AGENTS.md
- PLAN.md
- ACCEPTANCE.md
- TASK_QUEUE.md
- PROGRESS.md
- implementation_plan.md

Use implementation_plan.md as the authoritative source for the current overnight missing-features/bugfixes loop.
Do not execute it linearly.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent implementation slice, or a tightly related micro-batch if required to keep the build passing.

Current priority order:
- stabilize active indoor combat hit reactions;
- stabilize indoor corpse/world-item interaction parity;
- fix indoor event/status/dialogue activation gaps;
- implement shared wand attack behavior;
- implement Recharge Item and inventory item mixing;
- implement Lloyd's Beacon;
- implement remaining spell gaps: Summon Wisp, Prismatic Light, Soul Drinker, and indoor-only spell gates;
- implement monster relation overrides and unique actor guaranteed drops;
- implement save screenshot preview and dungeon transition dialogue;
- implement indoor save/load parity.

Architecture constraints:
- keep shared gameplay shared by default;
- do not duplicate outdoor gameplay paths into indoor;
- do not add callback bags or forwarding adapters that only hide ownership;
- keep indoor/outdoor-specific code limited to world facts, collision, picking, LOS, floor resolution, geometry,
  map/event/mechanism/decor lookup, world collision, and decal placement;
- keep implementations simple, readable, and testable.

Do not copy OpenEnroth or mm_mapview2 code.
Use the local OpenEnroth checkout only as behavioral/structural reference when needed.
Fix regressions you introduce.
Remove temporary diagnostics before finishing the slice.
Update TASK_QUEUE.md and PROGRESS.md with concrete evidence.
Update ACCEPTANCE.md only when criteria are satisfied.

Validation:
- run cmake --build build --target openyamm_unit_tests -j25 when unit/shared code changes;
- run ctest --test-dir build --output-on-failure when unit/shared code changes;
- run cmake --build build --target openyamm -j25 after meaningful runtime/rendering slices;
- add or update doctest coverage for pure gameplay logic when feasible;
- add or update focused headless coverage for map/runtime behavior when unit tests are not enough;
- record manual smoke notes in PROGRESS.md for behavior that cannot be validated automatically.

Completion requires root ACCEPTANCE.md done definition to be satisfied.
Stop only after finishing the current slice, recording evidence, and leaving the repo in a buildable state.
If scope is unclear, consult only the relevant sections of the control files and continue.
EOF

while true; do
  echo "=== Running Codex overnight bugfix loop ==="
  codex exec "$(cat "$PROMPT_FILE")" || true

  if grep -q '^## Done definition satisfied: YES$' PROGRESS.md; then
    echo "Loop complete."
    break
  fi

  if grep -q '^- Hard blocker: YES$' PROGRESS.md; then
    echo "Hard blocker recorded. Stopping."
    break
  fi
done
