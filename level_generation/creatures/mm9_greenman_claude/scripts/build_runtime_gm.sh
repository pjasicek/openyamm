#!/usr/bin/env bash
# Runtime GLB for mm9_greenman (Sigmund's chain on GREENMAN.abc's own 56-joint Bip01 skeleton: own clips stand, walk,
# fidget1, fidget2 + retargeted PeasantMale run, hattack1, wince1, die1): rigged master -> textured export -> MM9 clips
# (+ finger aliases) -> staff held in the R hand (staff_follow.py) -> [arm_clear] -> hand rest -> prepare -> LODs ->
# shadow fix -> material extras -> floor fix -> true handedness (mirror_glb.py) -> winding check [-> install --world mm9].
# Every Blender step memory-capped (12G, no swap).
# Usage (from the repo root): TOKEN=<lease> [BLEND=work/....blend] level_generation/creatures/mm9_greenman_claude/scripts/build_runtime_gm.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=../claude_shared/gltf_venv/bin/python
export PYTHONPATH=/usr/lib/python3/dist-packages
CAP=(systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0)
rel="level_generation/creatures/$(basename "$here")"
n=gm; N=GreenMan
B() { local out log; out=$(cd "$repo" && "${CAP[@]}" tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
[[ -n "${SKIP_EXPORT:-}" ]] || B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/legs_v2.blend}" "$here/work/${n}_body_tex.glb" "$N" gm_tp gm gm_tp
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips0.glb scripts/roles_gm.json work/clips_v1.json 2>/dev/null | cut -c1-240
"$V" -W ignore scripts/staff_follow.py work/mm9_${n}_clips0.glb work/mm9_${n}_clips.glb ${STAFF_OPTS:---offset 0.047,-0.020,0.019} 2>/dev/null | tail -2
cur=work/mm9_${n}_clips.glb
# a constant small left-shoulder abduction on the standing clips (arm_const.py, Sigmund's/Kira's: one rotation at every
# key, no jitter): MM9's left hand hangs at the hip, our leaf kilt is fuller there (the right hand holds the staff)
if [[ -s scripts/arm_const_gm.txt ]]; then "$V" -W ignore scripts/arm_const.py $cur work/mm9_${n}_const.glb $(cat scripts/arm_const_gm.txt) | tail -1; cur=work/mm9_${n}_const.glb; fi
if [[ -n "${ARMCLIPS:-}" ]]; then
  "$V" -W ignore scripts/arm_clear.py $cur work/mm9_${n}_clear.glb --side L=' L ' ${ARMSIDES:-} \
    --clips "$ARMCLIPS" --outer-only --max-deg ${ARMCAP:-20} 2>&1 | grep -E "ARMCLEAR|Traceback|Error" | cut -c1-200 || true
  "$V" -W ignore scripts/staff_follow.py work/mm9_${n}_clear.glb work/mm9_${n}_clear_s.glb ${STAFF_OPTS:---offset 0.047,-0.020,0.019} 2>/dev/null | tail -1
  cur=work/mm9_${n}_clear_s.glb
fi
k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_${n}.txt
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
"${CAP[@]}" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
# one skin (row 266 only): no region variants, no tier heads
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
# the retargeted die1 hovered 0.33 m mid-fall and sank 0.51 m under the floor at the impact (the leg-ratio root scale):
# ground every key smoothly through the scene root (moves the staff bone too); jitter gate for Death against this file
python3 -W ignore scripts/death_ground.py export/mm9_${n}_extras.glb export/mm9_${n}_extras_d.glb Death "Scene Root" ${DEATH_SIGMA:-0.8} 0.008 | tail -1
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras_d.glb work/mm9_${n}_floor.glb $(cat scripts/floor_ops_gm.txt) | tail -3
python3 scripts/drop_lod_slivers.py work/mm9_${n}_floor.glb work/mm9_${n}_floor2.glb | tail -1
# true handedness: convert_abc_model.py keeps LithTech's left-handed numbers, so the unmirrored build is the actor in a mirror
"$V" scripts/mirror_glb.py work/mm9_${n}_floor2.glb work/mm9_${n}_mirror.glb | tail -1
# thin leaf shells closed by the export's hole fill have ~0 volume and an arbitrary sign: turn them outward
python3 scripts/fix_winding.py work/mm9_${n}_mirror.glb export/mm9_${n}.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9 --name mm9_greenman.glb
fi
ls -la export/mm9_${n}.glb
