#!/usr/bin/env bash
# Runtime GLB (2026-10-30 rework: five-finger MPFB hands, 1K head+hands set): head_v1.blend -> textured export ->
# MM9 clips (+ finger aliases) -> arm clearance -> prepare -> LODs -> shadow fix -> material extras ->
# floor fix -> winding check [-> install --world mm9].
# Usage (from the project folder): PYGLTF_PYTHON=<python with pygltflib> TOKEN=<lease> [BLEND=<rigged master, default
#        v2/work/head_v1.blend>] [BODYTEX=<body texture prefix in textures/, default <prefix>; texture pass:
#        <prefix>_tp>] [HEADTEX=<head set prefix in v2/textures/, default <prefix>>]
#        v2/scripts/build_runtime_v2.sh <prefix> <MeshName> <roles json> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
n="$1"; N="$2"; R="$3"; V="${PYGLTF_PYTHON:?set PYGLTF_PYTHON}"; : "${TOKEN:?set TOKEN}"
rel="level_generation/creatures/$(basename "$here")"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|LOD triangles" "$log" | cut -c1-200 || true; }
B "$rel/v2/scripts/build_export_v2.py" "$here/${BLEND:-v2/work/head_v1.blend}" "$here/v2/work/${n}_body_tex.glb" "$N" "${BODYTEX:-$n}" "$n" "${HEADTEX:-$n}"
if [[ -n "${CLIPS_FROM:-}" ]]; then
  # Hanndl linings (2026-11-02): the lining faces would change what arm_clear.py/hand_rest.py see inside the body, so the
  # clips of the accepted build (its lod0, before prepare/floor) are grafted onto this export unchanged
  CL=$("$V" -c "import json,sys; r=json.load(open(sys.argv[1])); print(' '.join('--clip '+k for k in list(r['roles'])+['Dead']))" "$R")
  "$V" ../claude_shared/graft_clips.py v2/work/${n}_body_tex.glb "$CLIPS_FROM" v2/export/mm9_${n}_lod0.glb $CL | tail -1
else
"$V" v2/scripts/clips_mm9.py v2/work/${n}_body_tex.glb v2/work/mm9_${n}_clips.glb "$R" v2/work/clips_v2.json
# arm and hand gate: hands/fingers out of the body. With v2/scripts/hand_rest_<prefix>.txt (one hand_rest.py argument
# set per line, after the in/out paths): the smooth hand-rest push replaces the per-key arm_clear.py turns (Forad v3:
# arm_clear lifted MM9's hand-on-heart to the face and jittered). Otherwise the least upper-arm turn (arm_clear.py).
# Hanndl (2026-11-02): ARMCLEAR_CLIPS limits the accepted arm_clear.py passes (Annud's base clips) to those clips; then
# v2/scripts/hand_rest_<prefix>.txt (if any) runs hand_rest.py lines on the remaining clips.
if [[ -n "${ARMCLEAR_CLIPS:-}" ]]; then
python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clips.glb v2/work/mm9_${n}_clear1.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.012 --max-deg 40 --clips "$ARMCLEAR_CLIPS" | cut -c1-200
python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clear1.glb v2/work/mm9_${n}_clear2.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.015 --max-deg 40 --clips "$ARMCLEAR_CLIPS" | cut -c1-200
cur=v2/work/mm9_${n}_clear2.glb; k=0
if [[ -f v2/scripts/hand_rest_${n}.txt ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=v2/work/mm9_${n}_rest${k}.glb
    eval "python3 v2/scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < v2/scripts/hand_rest_${n}.txt
fi
if [[ -f v2/scripts/abduct_${n}.txt ]]; then
  "$V" scripts/arm_abduct.py "$cur" v2/work/mm9_${n}_abduct.glb $(grep -v '^#' v2/scripts/abduct_${n}.txt) | cut -c1-200
  cur=v2/work/mm9_${n}_abduct.glb
fi
cp "$cur" v2/export/mm9_${n}_lod0.glb
else
if [[ -f v2/scripts/hand_rest_${n}.txt ]]; then
  cur=v2/work/mm9_${n}_clips.glb; k=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=v2/work/mm9_${n}_rest${k}.glb
    eval "python3 v2/scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < v2/scripts/hand_rest_${n}.txt
  cp "$cur" v2/export/mm9_${n}_lod0.glb
else
python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clips.glb v2/work/mm9_${n}_clear1.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.012 --max-deg 40 | cut -c1-200
python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clear1.glb v2/export/mm9_${n}_lod0.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.015 --max-deg 40 | cut -c1-200
fi
fi
fi
python3 "$repo/tools/prepare_actor_glb.py" v2/export/mm9_${n}_lod0.glb v2/export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/v2/export/mm9_${n}_runtime_lod0.glb" \
  "$here/v2/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 v2/scripts/shrink_shadow_lods.py v2/export/mm9_${n}_lods.glb v2/export/mm9_${n}_lods_shadowfix.glb "$N"
python3 v2/scripts/set_material_extras.py v2/export/mm9_${n}_lods_shadowfix.glb v2/export/mm9_${n}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
# no merge_head_material.py: the body base colour is 2K and its normal/ORM 1K, so no single atlas layout fits
# both (the tool refuses); two primitives = two draws per actor
python3 ../claude_shared/floor/floor_fix.py v2/export/mm9_${n}_extras.glb v2/export/mm9_${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead
rm -f v2/export/mm9_${n}_lods.geometry.glb
# Hanndl linings (2026-11-02): decimation closes a small piece of the collar lining + neck cap into an inverted part in
# LOD1/LOD2 (72 / 12 triangles, ~0 volume); pm1d's fix_winding.py turns such parts outward
[[ -f scripts/fix_winding.py ]] && python3 scripts/fix_winding.py v2/export/mm9_${n}.glb v2/work/mm9_${n}_wind.glb | tail -1 && mv v2/work/mm9_${n}_wind.glb v2/export/mm9_${n}.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" v2/export/mm9_${n}.glb | tail -1
if [[ "${4:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" v2/export/mm9_${n}.glb --world mm9
fi
ls -la v2/export/mm9_${n}.glb
