#!/usr/bin/env bash
# Runtime GLB for mm9_peasantm3 (PeasantM7/PeasantDM2 chain on the PeasantMale skeleton): rigged master -> textured export ->
# MM9 clips (+ finger aliases) -> finger_pose.py (relaxed hands) -> hand rest (scripts/hand_rest_pm3.txt) -> prepare -> LODs ->
# shadow fix -> tiers (body: region mask + ramps; head: tier B image) -> material extras -> floor fix -> mirror -> winding
# [-> install --world mm9]. Usage: TOKEN=<lease> [BLEND=work/<master>.blend] [SKIP_TIER_HEAD=1] scripts/build_runtime_pm3.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=../claude_shared/gltf_venv/bin/python
rel="level_generation/creatures/$(basename "$here")"
n=pm3; N=PeasantM3
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX|LOD triangles" "$log" | cut -c1-200 || true; }
mkdir -p export work
[[ -n "${SKIP_EXPORT:-}" ]] || B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/neck_v5.blend}" "$here/work/${n}_body_tex.glb" "$N" pm3_tp pm3 pm3_tp
"$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb scripts/roles_pm3.json work/clips_v1.json 2>/dev/null | cut -c1-240
# relaxed fingers that follow MM9's mitten curl (Kira's finger_pose.py; VARIANTS_BRIEF hands lesson)
"$V" scripts/finger_pose.py work/mm9_${n}_clips.glb work/mm9_${n}_fingers.glb 2>/dev/null | tail -1 | cut -c1-200
cur=work/mm9_${n}_fingers.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_${n}.txt
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$N" --max-influences 4 2>&1 | grep "LOD triangles"
DROP_LINING_LODS=3 python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$N"
"$V" ../claude_shared/region_variants.py export/mm9_${n}_lods_shadowfix.glb work/mm9_${n}_rv.glb textures/pm3_ramps.json 2>/dev/null | tail -1 | cut -c1-200
if [[ -n "${SKIP_TIER_HEAD:-}" ]]; then echo "TIER HEAD SKIPPED (test build only)"; cp work/mm9_${n}_rv.glb work/mm9_${n}_tiers.glb
else "$V" scripts/tier_head.py work/mm9_${n}_rv.glb work/mm9_${n}_tiers.glb PeasantM3Head pm3_b=pm3b_tp 2>/dev/null; fi
python3 scripts/set_material_extras.py work/mm9_${n}_tiers.glb export/mm9_${n}_extras.glb openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_extras.glb work/mm9_${n}_floor.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -3
# true handedness (mirror_glb.py, as mm9_peasantdm2d_claude on the same skeleton): convert_abc_model.py keeps LithTech's
# left-handed numbers, so the unmirrored build (work/mm9_pm3_floor.glb) is the game's actor in a mirror
$V scripts/mirror_glb.py work/mm9_${n}_floor.glb export/mm9_${n}.glb | tail -1
rm -f export/mm9_pm3_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9
fi
ls -la export/mm9_${n}.glb
