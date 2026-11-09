#!/usr/bin/env bash
# See-through sweep 2026-11-02 (render only, nothing written outside this folder): mm9_peasantdm2_claude's
# scripts/see_through_gate.py on the installed GLBs of the bodies that went through the same cuff/boot steps.
# Usage (any folder): run_sweep.sh [body ...]   (body = the GLB's name after mm9_)
set -u
repo="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../../../.." && pwd)"
out="$repo/level_generation/creatures/claude_shared/mm9_overview/holes_sweep_20261102"
gate="$repo/level_generation/creatures/mm9_peasantdm2_claude/scripts/see_through_gate.py"
bodies=("$@"); [[ ${#bodies[@]} -gt 0 ]] || bodies=(peasantm7 peasantm1 pm1d peasantm2 phom1 bjarni sven markel tryggva peasantdm1)
for b in "${bodies[@]}"; do
  mkdir -p "$out/$b"
  glb="$repo/assets_source/worlds/mm9/models/mm9_$b.glb"
  sha256sum "$glb" > "$out/$b/input.sha256"
  /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
    --python "$gate" -- "$glb" "$out/$b/see_through.json" step=4 px_mm=4 shots=2 extra= 2>&1 \
    | grep -a -E "SEE_THROUGH|Error|Traceback" > "$out/$b/run.log"
  echo "SWEEP $b done"
done
