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
- docs/world_particle_fx_extraction_plan.md

Use docs/world_particle_fx_extraction_plan.md as the authoritative source for the current refactor loop.
Do not execute it linearly if a smaller coherent slice is safer.
Use TASK_QUEUE.md as the executable task list.

Execute the next unfinished task from TASK_QUEUE.md.
Work on one coherent extraction slice, or a tightly related micro-batch if required to keep the build passing.

Current priority:
- make particle FX 100% shared between indoor and outdoor;
- extract ParticleRenderer and particle render resources away from OutdoorGameView;
- move ParticleSystem ownership into shared WorldFxSystem;
- move projectile trail/impact particle spawning into shared WorldFxSystem;
- move party spell world particles into shared WorldFxSystem;
- wire indoor to the same shared update/render path;
- remove indoor fallback spell/projectile FX once shared rendering works.

Architecture constraints:
- keep the implementation coarse and human-readable;
- do not add callback bags or adapter layers that only hide ownership;
- do not add projectile-style micro-structs or Decision/Patch/EffectDecision plumbing;
- do not add indoor-only spell/projectile particle recipes;
- do not refactor projectile gameplay/collision unless strictly required for FX presentation wiring.

Do not copy OpenEnroth or mm_mapview2 code.
Use the local OpenEnroth checkout only as behavioral/structural reference when needed.
Preserve outdoor visuals while moving ownership.
Fix regressions you introduce.
Update TASK_QUEUE.md and PROGRESS.md with concrete evidence.
Update ACCEPTANCE.md when criteria are satisfied.

Validation:
- run cmake --build build --target openyamm_unit_tests -j25 when unit/shared code changes;
- run ctest --test-dir build --output-on-failure when unit/shared code changes;
- run cmake --build build --target openyamm -j25 after meaningful runtime/rendering slices;
- run timeout 300s build/game/openyamm --headless-run-regression-suite projectiles after projectile FX ownership
  changes;
- run timeout 300s build/game/openyamm --headless-run-regression-suite indoor after indoor FX wiring changes.

Completion requires root ACCEPTANCE.md done definition to be satisfied.
Stop only after finishing the current slice, recording evidence, and leaving the repo in a buildable state.
If scope is unclear, consult only the relevant sections of the control files and continue.
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
