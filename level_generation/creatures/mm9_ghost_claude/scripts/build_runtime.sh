#!/usr/bin/env bash
# Runtime GLB: textured export -> MM9 clips -> dissolve death -> prepare -> LODs -> shadow fix -> tiers -> floor -> mirror -> blend order [-> install --world mm9].
# Usage (repo root): TOKEN=<lease> level_generation/creatures/mm9_ghost_claude/scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
V="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
: "${TOKEN:?set TOKEN}"
rel=level_generation/creatures/mm9_ghost_claude
cd "$repo"
B() { local out log; out=$(tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|SLOTS" "$log" | cut -c1-160 || true; }
B $rel/scripts/build_export.py "$here/${MASTER:-work/uv_v1.blend}" "$here/work/ghost_body_tex.glb"
cd "$here"
"$V" -W ignore scripts/clips_mm9.py work/ghost_body_tex.glb work/mm9_ghost_clips.glb scripts/roles_ghost.json work/clips.json | cut -c1-200
cur=work/mm9_ghost_clips.glb
if [[ -f scripts/hand_rest_ghost.txt ]]; then
  k=0
  "$V" -W ignore scripts/gate_alias.py "$cur" work/alias_in.glb
  cur=work/alias_in.glb
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/mm9_ghost_rest${k}.glb
    eval "$V -W ignore scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_ghost.txt
  "$V" -W ignore scripts/gate_alias.py "$cur" work/mm9_ghost_rested.glb --reverse
  cur=work/mm9_ghost_rested.glb
fi
"$V" -W ignore scripts/ghost_death.py "$cur" export/mm9_ghost_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_ghost_lod0.glb export/mm9_ghost_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_ghost_runtime_lod0.glb" \
  "$here/export/mm9_ghost_lods.glb" --mesh-node Ghost --max-influences 4 2>&1 | grep "LOD triangles"
"$V" -W ignore scripts/shrink_shadow_lods.py export/mm9_ghost_lods.glb export/mm9_ghost_lods_shadowfix.glb Ghost
"$V" -W ignore scripts/ghost_variants.py export/mm9_ghost_lods_shadowfix.glb export/mm9_ghost_skins.glb
"$V" -W ignore ../claude_shared/emission.py export/mm9_ghost_skins.glb export/mm9_ghost_glow.glb --material GhostHead --mask textures/ghost_eye_mask.png \
  --color ghost_a=0,0,0 --color ghost_b=0.2,1.0,0.3 --color ghost_c=0.2,0.55,1.0 --strength 1.2 --pulse 0.12,2.3 | tail -1 | cut -c1-160
"$V" -W ignore ../claude_shared/floor/floor_fix.py export/mm9_ghost_glow.glb export/mm9_ghost_floored.glb $(set -f; cat scripts/floor_ops.txt) | tail -4 | cut -c1-200
"$V" -W ignore scripts/mirror_glb.py export/mm9_ghost_floored.glb export/mm9_ghost_mirrored.glb
"$V" -W ignore scripts/finish_blend.py export/mm9_ghost_mirrored.glb export/mm9_ghost.glb | tail -5 | cut -c1-160
rm -f export/mm9_ghost_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_ghost.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_ghost.glb --world mm9
fi
ls -la export/mm9_ghost.glb
