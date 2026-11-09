#!/usr/bin/env bash
# Runtime GLB (2026-10-30 rework: five-finger MPFB hands, 1K head+hands set): head_v1.blend -> textured export ->
# MM9 clips (+ finger aliases) -> arm clearance -> prepare -> LODs -> shadow fix -> material extras ->
# floor fix -> winding check [-> install --world mm9].
# Usage (from the project folder): PYGLTF_PYTHON=<python with pygltflib> TOKEN=<lease> [BLEND=<rigged master, default
#        work/head_v1.blend>] [BODYTEX=<body texture prefix in textures/, default <prefix>; texture pass:
#        <prefix>_tp>] [HEADTEX=<head set prefix in v2/textures/, default <prefix>>]
#        scripts/build_runtime_v2.sh <prefix> <MeshName> <roles json> [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
n="$1"; N="$2"; R="$3"; V="${PYGLTF_PYTHON:?set PYGLTF_PYTHON}"; : "${TOKEN:?set TOKEN}"
rel="level_generation/creatures/$(basename "$here")"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|LOD triangles" "$log" | cut -c1-200 || true; }
B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/head_v1.blend}" "$here/work/${n}_body_tex.glb" "$N" "${BODYTEX:-$n}" "$n" "${HEADTEX:-$n}"
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb "$R" work/clips_v2.json
# arm and hand gate: hands/fingers out of the body. With scripts/hand_rest_<prefix>.txt (one hand_rest.py argument
# set per line, after the in/out paths): the smooth hand-rest push replaces the per-key arm_clear.py turns (Forad v3:
# arm_clear lifted MM9's hand-on-heart to the face and jittered). Otherwise the least upper-arm turn (arm_clear.py).
if [[ -f scripts/hand_rest_${n}.txt ]]; then
  cur=work/mm9_${n}_clips.glb; k=0
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
    eval "python3 scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_${n}.txt
  cp "$cur" export/mm9_${n}_lod0.glb
  # mm9_markel: eased constant abductions (clap_spread.py, as mm9_sven) per scripts/spread_<prefix>.txt: "<env...> <clip> <deg>"
  if [[ -f scripts/spread_${n}.txt ]]; then
    while IFS= read -r line; do
      [[ -z "$line" || "$line" == \#* ]] && continue
      read -r -a pa <<< "$line"; m=${#pa[@]}
      env "${pa[@]:0:m-2}" python3 scripts/clap_spread.py export/mm9_${n}_lod0.glb export/mm9_${n}_lod0.glb "${pa[m-2]}" "${pa[m-1]}" | cut -c1-200
    done < scripts/spread_${n}.txt
  fi
else
python3 scripts/arm_clear.py work/mm9_${n}_clips.glb work/mm9_${n}_clear1.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.012 --max-deg 40 | cut -c1-200
python3 scripts/arm_clear.py work/mm9_${n}_clear1.glb export/mm9_${n}_lod0.glb --side "L= L " --side "R= R " \
  --iter 8 --margin 0.015 --max-deg 40 | cut -c1-200
fi
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
# no merge_head_material.py: the body base colour is 2K and its normal/ORM 1K, so no single atlas layout fits
# both (the tool refuses); two primitives = two draws per actor
# mm9_markel (as mm9_bjarni): one skin, no tiers (no region variants)
cp export/mm9_${n}_extras.glb export/mm9_${n}_variants.glb
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_variants.glb export/mm9_${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead
rm -f export/mm9_${n}_lods.geometry.glb
# MM9 GLBs are the mirror image of the game's actor (LithTech left-handed numbers read as glTF; mm9_imp/mm9_peasantm1d):
# mirror last, so MM9's R Hand is the anatomical right hand again (copied from mm9_peasantm1d_claude/v2/scripts/).
cp export/mm9_${n}.glb work/mm9_${n}_unmirrored.glb
python3 scripts/mirror_glb.py work/mm9_${n}_unmirrored.glb export/mm9_${n}.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${4:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9 --name mm9_markel.glb
fi
ls -la export/mm9_${n}.glb
