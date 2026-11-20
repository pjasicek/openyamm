#!/usr/bin/env bash
# Runtime GLB of PeasantM7d: PeasantM7's build_runtime_v2.sh chain (the approved PeasantM7 steps, same scripts copied from
# ../mm9_peasantm7_claude/scripts/) on this project's master with the elf ears.
#   export -> clips_mm9.py (roles_pm7d.json) -> hand_rest.py (hand_rest_pm7d.txt) -> prepare -> LODs -> shadow fix ->
#   extras -> region_variants.py (body ramps) -> tier_head.py (tier C's own head colour + normal) -> floor_fix.py ->
#   mirror_glb.py -> winding [-> install].
# Usage (project folder): TOKEN=<lease> [BLEND=work/linings_v1.blend] [NAME=PeasantM7d] [N=pm7d] [BODYTEX=pm7d_tp]
#   [HEADTEX=pm7d_tp] [RAMPS=textures/pm7d_ramps.json] [ROLES=scripts/roles_pm7d.json] [TIERHEAD="pm7d_c=pm7dc_tp" or ""]
#   [FLOOR=scripts/floor_ops_pm7d.txt] [REST=scripts/hand_rest_pm7d.txt] scripts/build_runtime_pm7d.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
: "${TOKEN:?set TOKEN}"
V=$here/../claude_shared/gltf_venv/bin/python
n=${N:-pm7d}; NM=${NAME:-PeasantM7d}
rel="level_generation/creatures/$(basename "$here")"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "EXPORTED|LIFT|HEADFIX" "$log" | cut -c1-300 || true; }
B "$rel/scripts/build_export_v2.py" "$here/${BLEND:-work/linings_v1.blend}" "$here/work/${n}_body_tex.glb" "$NM" "${BODYTEX:-pm7d_tp}" pm7d "${HEADTEX:-pm7d_tp}"
PYTHONPATH=/usr/lib/python3/dist-packages "$V" scripts/clips_mm9.py work/${n}_body_tex.glb work/mm9_${n}_clips.glb "${ROLES:-scripts/roles_pm7d.json}" work/clips_${n}.json | tail -2
cur=work/mm9_${n}_clips.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/mm9_${n}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | cut -c1-200
  cur=$nxt
done < "${REST:-scripts/hand_rest_pm7d.txt}"
cp "$cur" export/mm9_${n}_lod0.glb
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_${n}_lod0.glb export/mm9_${n}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_${n}_runtime_lod0.glb" \
  "$here/export/mm9_${n}_lods.glb" --mesh-node "$NM" --max-influences 4 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_${n}_lods.glb export/mm9_${n}_lods_shadowfix.glb "$NM"
python3 scripts/set_material_extras.py export/mm9_${n}_lods_shadowfix.glb export/mm9_${n}_extras.glb \
  openyamm_specular=0 pbr.metallicFactor=0
python3 ../claude_shared/region_variants.py export/mm9_${n}_extras.glb work/mm9_${n}_variants.glb "${RAMPS:-textures/pm7d_ramps.json}" \
  --extra "$NM" openyamm_specular=0 --extra "$NM" pbr.metallicFactor=0 | tail -1 | cut -c1-200
TH=${TIERHEAD-pm7d_c=pm7dc_tp}
if [[ -n "$TH" ]]; then
  "$V" scripts/tier_head.py work/mm9_${n}_variants.glb export/mm9_${n}_variants.glb "${NM}Head" $TH
else
  cp work/mm9_${n}_variants.glb export/mm9_${n}_variants.glb
fi
python3 ../claude_shared/floor/floor_fix.py export/mm9_${n}_variants.glb work/mm9_${n}_unmirrored.glb $(cat "${FLOOR:-scripts/floor_ops_pm7d.txt}") --ground-death Death Dead | tail -1
if [[ -e export/mm9_${n}_lods.geometry.glb ]]; then mv -f export/mm9_${n}_lods.geometry.glb work/; fi
python3 scripts/mirror_glb.py work/mm9_${n}_unmirrored.glb export/mm9_${n}.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_${n}.glb --world mm9 --name mm9_peasantm7d.glb
fi
ls -la export/mm9_${n}.glb
