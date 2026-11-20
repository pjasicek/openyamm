#!/usr/bin/env bash
# Runtime GLB for mm9_krohn (the Sigmund/Markel MM9 humanoid route on KROHN.abc's own 64-joint Bip01 skeleton, its own clips +
# retargeted PeasantMale roles, glaive and sword joined as a third material): rigged master -> textured export -> MM9 clips
# (+ finger aliases, cutscene origin offsets) -> arm corrections -> hand rest -> grip keys -> prepare -> LODs -> shadow fix ->
# material extras -> floor fix -> LOD slivers -> true handedness (mirror_glb.py) -> winding [-> install --world mm9].
# Every Blender step memory-capped (12G, no swap).
# Usage (from the repo root): TOKEN=<lease> [BLEND=work/....blend] level_generation/creatures/mm9_krohn_claude/scripts/build_runtime_kr.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=../claude_shared/gltf_venv/bin/python
CAP=(systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0)
rel="level_generation/creatures/$(basename "$here")"
n=kr; N=Krohn
PY() { PYTHONPATH=/usr/lib/python3/dist-packages "${CAP[@]}" "$V" -W ignore "$@"; }
B() { local out log; out=$(cd "$repo" && "${CAP[@]}" tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if [[ -z "$log" ]] || grep -q "Error: script failed\|Traceback" "$log"; then echo "$out" | tail -3; [[ -n "$log" ]] && grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX|PROPS|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
[[ -n "${SKIP_EXPORT:-}" ]] || B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/grip_props_cape.blend}" "$here/work/${n}_body_tex.glb" "$N" kr_tp krohn kr_tp
PY scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_krohn.json work/clips_v1.json 2>/dev/null | cut -c1-240
cur=work/mm9_${n}_clips.glb
# a constant small shoulder abduction on chosen clips (arm_const.py: one rotation at every key, no jitter)
if [[ -s scripts/arm_const_kr.txt ]]; then PY scripts/arm_const.py $cur work/mm9_${n}_clipsc.glb $(grep -v '^#' scripts/arm_const_kr.txt) | tail -1; cur=work/mm9_${n}_clipsc.glb; fi
if [[ -s scripts/arm_clear_kr.txt ]]; then
  PY scripts/arm_clear.py $cur work/mm9_${n}_clear.glb --side L=' L ' --side R=' R ' $(grep -v '^#' scripts/arm_clear_kr.txt) 2>&1 | grep -E "ARMCLEAR|Traceback|Error" | cut -c1-200 || true
  cur=work/mm9_${n}_clear.glb
fi
k=0
if [[ -s scripts/hand_rest_${n}.txt ]]; then
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_${n}.txt
fi
# right fist round the glaive shaft and the relaxed left hand (grip_keys.py, work/hand_poses.json from grip_solve.py)
if [[ -s work/hand_poses.json ]]; then PY scripts/grip_keys.py $cur work/mm9_${n}_grip.glb work/hand_poses.json | tail -1; cur=work/mm9_${n}_grip.glb; fi
# the glaive out of the body: a smoothed rotation about the fist where the shaft still enters the skin (spear_clear.py; caps per
# line in scripts/spear_clear_kr.txt: "<cap deg> <clip> [clip...]")
k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); cap=${line%% *}; clips=${line#* }
  DEPTH_MAX=${DEPTH_MAX:-0.15} CAP_DEG=$cap PY scripts/spear_clear.py $cur work/mm9_${n}_spear$k.glb $clips 2>&1 | grep -E "CLEAR|Traceback|Error" | cut -c1-160
  cur=work/mm9_${n}_spear$k.glb
done < <(cat scripts/spear_clear_kr.txt 2>/dev/null)
# the long hair hangs from the back, not the head, in the retargeted PeasantMale clips (it swung through the sword)
PY scripts/hair_follow.py $cur work/mm9_${n}_hair1.glb 0.9 Running AttackMelee Hit | tail -1
# Death: only the side strand that crossed the sword turns, over its contact window (a whole-hair follow added shoulder-skin
# jitter); then the glaive takes one smooth windowed turn about the fist where it still passes the shoulder/hair (AttackMelee)
# or the thigh (cutscene clips): spear_window.py, hair_window.py (orchestrator pass 2026-11-04)
PY scripts/hair_window.py work/mm9_${n}_hair1.glb work/mm9_${n}_hair.glb Death Xhairpiv01 | tail -1
SW_FPS=48 PY scripts/spear_window.py work/mm9_${n}_hair.glb work/mm9_${n}_sw1.glb AttackMelee | tail -1
SW_FPS=24 PY scripts/spear_window.py work/mm9_${n}_sw1.glb work/mm9_${n}_sw2.glb Krohn01 Krohn03 Krohn04 | tail -3
SW_FPS=8 PY scripts/spear_window.py work/mm9_${n}_sw2.glb work/mm9_${n}_sw.glb Krohn05 | tail -1; cur=work/mm9_${n}_sw.glb
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
"${CAP[@]}" /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
# one skin (row 255 only): no region variants, no tier heads
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb work/mm9_${n}_floor.glb $(grep -v '^#' scripts/floor_ops.txt) --ground-death Death Dead | tail -3
# Walking: one smooth low-passed root-height curve, centred on the floor (walk_floor.py; per-key grounding jittered, the
# floor_fix smoothing's running maximum lifted every foot 3.8 units)
PY scripts/walk_floor.py work/mm9_${n}_floor.glb work/mm9_${n}_floorw.glb Walking 0.1 | tail -1
python3 scripts/drop_lod_slivers.py work/mm9_${n}_floorw.glb work/mm9_${n}_floor2.glb | tail -1
# true handedness: convert_abc_model.py keeps LithTech's left-handed numbers, so the unmirrored build is the actor in a mirror
PY scripts/mirror_glb.py work/mm9_${n}_floor2.glb export/mm9_${n}.glb | tail -1
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9 --name mm9_krohn.glb
fi
ls -la export/mm9_${n}.glb
