#!/usr/bin/env bash
# Runtime GLB: textured export -> MM9 clips -> prepare -> LODs -> tiers -> eye glow -> floor -> mirror -> blend order [-> install --world mm9].
# Usage (repo root): TOKEN=<lease> level_generation/creatures/mm9_banshee_claude/scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
V="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
: "${TOKEN:?set TOKEN}"
rel=level_generation/creatures/mm9_banshee_claude
cd "$repo"
B() { local out log; out=$(tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|SLOTS|NECK|RING" "$log" | cut -c1-160 || true; }
B $rel/scripts/rig_fix.py "$here/work/uv_v1.blend" "$here/work/uv_v2.blend"
B $rel/scripts/build_export.py "$here/work/uv_v2.blend" "$here/work/banshee_body_tex.glb"
cd "$here"
"$V" -W ignore scripts/clips_mm9.py work/banshee_body_tex.glb work/mm9_banshee_clips.glb scripts/roles_banshee.json work/clips.json 2>&1 | tail -1 | cut -c1-200
# her left hand out of the head in Fidget2: arm_clear solves it, arm_bump keeps one smooth rotation (per-key corrections jittered)
"$V" -W ignore scripts/gate_alias.py work/mm9_banshee_clips.glb work/alias_in.glb
"$V" -W ignore scripts/arm_clear.py work/alias_in.glb work/alias_clear.glb --side L=" L " --side R=" R " --clips Fidget2 --outer-only --tol 0.006 --margin 0.012 --max-deg 10 --sigma 6 --hand-names Hand,Index,Middle,Ring,Thumb --arm-names Clavicle,UpperArm,Forearm,Hand,Index,Middle,Ring,Thumb --root Xspine,XCENTER 2>&1 | tail -1 | cut -c1-160
"$V" -W ignore scripts/arm_bump.py work/alias_in.glb work/alias_clear.glb work/alias_bump.glb Fidget2 "Bip01 L UpperArm" 0.45 | tail -1
"$V" -W ignore scripts/gate_alias.py work/alias_bump.glb export/mm9_banshee_lod0.glb --reverse
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_banshee_lod0.glb export/mm9_banshee_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_banshee_runtime_lod0.glb" \
  "$here/export/mm9_banshee_lods.glb" --mesh-node Banshee --max-influences 4 2>&1 | grep "LOD triangles"
"$V" -W ignore scripts/shrink_shadow_lods.py export/mm9_banshee_lods.glb export/mm9_banshee_lods_shadowfix.glb Banshee
"$V" -W ignore scripts/banshee_variants.py export/mm9_banshee_lods_shadowfix.glb export/mm9_banshee_skins.glb
"$V" -W ignore ../claude_shared/emission.py export/mm9_banshee_skins.glb export/mm9_banshee_glow.glb --material BansheeHead --mask textures/banshee_eye_mask.png \
  --color banshee_a=0,0,0 --color banshee_b=0.9,0.28,0.08 --color banshee_c=0.15,1.0,0.3 --strength 1.3 --pulse 0.12,2.3 | tail -1 | cut -c1-160
"$V" -W ignore ../claude_shared/floor/floor_fix.py export/mm9_banshee_glow.glb export/mm9_banshee_floored.glb $(set -f; cat scripts/floor_ops.txt) | tail -4 | cut -c1-200
"$V" -W ignore scripts/mirror_glb.py export/mm9_banshee_floored.glb export/mm9_banshee_mirrored.glb
"$V" -W ignore scripts/finish_blend.py export/mm9_banshee_mirrored.glb export/mm9_banshee.glb | tail -5 | cut -c1-160
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_banshee.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_banshee.glb --world mm9
fi
ls -la export/mm9_banshee.glb
