#!/usr/bin/env bash
# peasantm1d (2026-11-01, from mm9_honkmale_claude): tiers on body + head by region_variants, mirror last.
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
"$V" v2/scripts/clips_mm9.py v2/work/${n}_body_tex.glb v2/work/mm9_${n}_clips.glb "$R" v2/work/clips_v2.json
# arm and hand gate: hands/fingers out of the body. With v2/scripts/hand_rest_<prefix>.txt (one hand_rest.py argument
# set per line, after the in/out paths): the smooth hand-rest push replaces the per-key arm_clear.py turns (Forad v3:
# arm_clear lifted MM9's hand-on-heart to the face and jittered). Otherwise the least upper-arm turn (arm_clear.py).
if [[ -f v2/scripts/hand_rest_${n}.txt ]]; then
  cur=v2/work/mm9_${n}_clips.glb; k=0
  if [[ -f v2/scripts/arm_offset_${n}.txt ]]; then
    python3 v2/scripts/arm_offset.py "$cur" v2/work/mm9_${n}_armout.glb $(cat v2/scripts/arm_offset_${n}.txt); cur=v2/work/mm9_${n}_armout.glb
  fi
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=v2/work/mm9_${n}_rest${k}.glb
    eval "python3 v2/scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
    cur=$nxt
  done < v2/scripts/hand_rest_${n}.txt
  cp "$cur" v2/export/mm9_${n}_lod0.glb
else
# peasanthom1 (2026-11-01): optional v2/scripts/arm_clear_<prefix>.txt = extra arm_clear.py arguments for both passes
# (a wider --sigma: Fidget's scratching hand in the other sleeve jittered with the default 1.5 keys)
AC=""; [[ -f v2/scripts/arm_clear_${n}.txt ]] && AC=$(grep -v '^#' v2/scripts/arm_clear_${n}.txt | tr '\n' ' ')
eval "python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clips.glb v2/work/mm9_${n}_clear1.glb --side 'L= L ' --side 'R= R ' \
  --iter 8 --margin 0.012 --max-deg 40 $AC" | cut -c1-200
eval "python3 v2/scripts/arm_clear.py v2/work/mm9_${n}_clear1.glb v2/export/mm9_${n}_lod0.glb --side 'L= L ' --side 'R= R ' \
  --iter 8 --margin 0.015 --max-deg 40 $AC" | cut -c1-200
# peasanthom1: optional v2/scripts/smooth_correction_<prefix>.txt = smooth_correction.py arguments: the arm_clear turn
# re-applied to the raw clip as a held, low-passed rotation (jitter gate)
if [[ -f v2/scripts/smooth_correction_${n}.txt ]]; then
  eval "$PYGLTF_PYTHON v2/scripts/smooth_correction.py v2/work/mm9_${n}_clips.glb v2/export/mm9_${n}_lod0.glb v2/work/mm9_${n}_smooth.glb $(grep -v '^#' v2/scripts/smooth_correction_${n}.txt | tr '\n' ' ')" 2>&1 | grep SMOOTHCORR
  mv v2/work/mm9_${n}_smooth.glb v2/export/mm9_${n}_lod0.glb
fi
fi
python3 "$repo/tools/prepare_actor_glb.py" v2/export/mm9_${n}_lod0.glb v2/export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/v2/export/mm9_${n}_runtime_lod0.glb" \
  "$here/v2/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 v2/scripts/shrink_shadow_lods.py v2/export/mm9_${n}_lods.glb v2/export/mm9_${n}_lods_shadowfix.glb "$N"
# region mask + tier ramps on the body AND on the head set (hair), one material per tier sharing every image
python3 ../claude_shared/region_variants.py v2/export/mm9_${n}_lods_shadowfix.glb v2/export/mm9_${n}_extras.glb textures/${n}_ramps.json \
  --extra "$N" openyamm_specular=0 --extra "$N" pbr.metallicFactor=0
# the hand on the forearm's line, MM9's wrist (one constant Hand rotation in every clip; Honk third pass), opt-in
if [[ -f v2/scripts/wrist_fix_${n}.txt ]]; then
  python3 v2/scripts/wrist_fix.py v2/export/mm9_${n}_extras.glb v2/work/mm9_${n}_wrist.glb $(cat v2/scripts/wrist_fix_${n}.txt) | cut -c1-120
  mv v2/work/mm9_${n}_wrist.glb v2/export/mm9_${n}_extras.glb
fi
python3 ../claude_shared/floor/floor_fix.py v2/export/mm9_${n}_extras.glb v2/work/mm9_${n}_floor1.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead
cp v2/work/mm9_${n}_floor1.glb v2/export/mm9_${n}.glb
if [[ -f v2/scripts/clip_relax_${n}.txt ]]; then
  python3 v2/scripts/clip_relax.py v2/export/mm9_${n}.glb v2/work/mm9_${n}_relax.glb $(cat v2/scripts/clip_relax_${n}.txt) && mv v2/work/mm9_${n}_relax.glb v2/export/mm9_${n}.glb
fi
# MM9 GLBs are the mirror image of the game's actor (LithTech left-handed numbers read as glTF; checked on PEASANTM1D:
# L Hand at x -0.62 with the toes toward +z): last geometry step. v2/work/mm9_<n>_floor1.glb is the unmirrored build.
python3 v2/scripts/mirror_glb.py v2/export/mm9_${n}.glb v2/work/mm9_${n}_mirrored.glb && mv v2/work/mm9_${n}_mirrored.glb v2/export/mm9_${n}.glb
# decimation remnants: a 6-triangle zero-volume boot-strap piece in LOD1 counts as inverted (Nobleman's fix_winding.py)
python3 scripts/fix_winding.py v2/export/mm9_${n}.glb v2/work/mm9_${n}_wind.glb | tail -1 && mv v2/work/mm9_${n}_wind.glb v2/export/mm9_${n}.glb
rm -f v2/export/mm9_${n}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" v2/export/mm9_${n}.glb | tail -1
if [[ "${4:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" v2/export/mm9_${n}.glb --world mm9
fi
ls -la v2/export/mm9_${n}.glb
