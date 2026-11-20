#!/usr/bin/env bash
# Titan hands rebuild (2026-11-11): installed GLB -> graft (Blender) -> bake -> compose -> splice (fingers, Cast fix)
# -> LODs (build_actor_lods.py) -> variants -> shadow tuck -> far-LOD repair steps (r25_12, the installed choice)
# -> export/mm6_ttn.glb [--install]. TOKEN=<lease> scripts/build_runtime.sh [--graft] [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
rel=level_generation/creatures/$(basename "$here")
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
MLPY=$here/work/lodrep_venv/bin/python
LR=$repo/level_generation/creatures/lod_repair_claude/scripts
B() { local out log; out=$(cd "$repo" && BLENDER_USER_EXTENSIONS=$HOME/.config/blender/5.2/extensions tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(GRAFT|BAKED|LOD triangles)" "$log" | cut -c1-200 || true; }
cd "$here"
if [[ " $* " == *" --graft "* ]]; then
  B $rel/scripts/graft_ttn.py $rel/scripts/graft_ttn.json
  B $rel/scripts/bake_hands_ttn.py work/graft_v1.blend middleage_caucasian_male/middleage_lightskinned_male_diffuse.png
  python3 scripts/compose_ttn.py
fi
$PY scripts/splice_ttn.py work/before_rebuild/mm6_ttn.glb work/graft_v1.glb work/splice_v1.glb 2>&1 | grep -v RuntimeWarning | cut -c1-120
(cd "$repo" && TOKEN=$TOKEN; python3 tools/creature_workspace.py run --project "$here" --token "$TOKEN" -- \
  /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python tools/build_actor_lods.py -- "$here/work/splice_v1.glb" "$here/work/lods_v1.glb" --mesh-node Titan 2>&1 | grep "LOD triangles")
rm -f work/lods_v1.geometry.glb
$PY scripts/copy_variants.py work/lods_v1.glb work/lods_v1v.glb 2>&1 | grep -v RuntimeWarning
$PY ../mm6_ttn1_claude/scripts/shrink_shadow_lods.py work/lods_v1v.glb work/lods_v1s.glb 2>&1 | grep -v RuntimeWarning | tail -2
rm -rf work/lodrep && mkdir -p work/lodrep
$MLPY $LR/build_lods.py work/lods_v1s.glb Titan work/lodrep/built.glb 2:0.25,3:0.125 | tail -2
$MLPY $LR/unwrap_lods.py work/lodrep/built.glb Titan work/lodrep/bake 2:512,3:256 | tail -2
$MLPY $LR/transfer_textures.py work/lodrep/built.glb Titan work/lodrep/bake | tail -2
$MLPY $LR/apply_bake.py work/lodrep/built.glb Titan work/lodrep/bake export/mm6_ttn.glb 2,3 | tail -2
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm6_ttn.glb | tail -2
if [[ " $* " == *" --install "* ]]; then
  (cd "$repo" && python3 tools/install_model.py "$here/export/mm6_ttn.glb" --world mm6)
fi
