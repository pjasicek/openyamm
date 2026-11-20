#!/usr/bin/env bash
# PeasantM2d runtime (PeasantM2's chain; project folder): finish (linings, cap) -> upper-tunic lining (collar_lining.py) -> export -> clips -> arm constant -> hand rest -> half joints -> skirt keys ->
# prepare -> LODs -> shadow fix -> tiers (head B images, body ramps) -> material extras -> floor -> winding -> [install] -> viewer GLBs.
# IN = the frozen-UV blend with the final weights (default work/uv_v2.blend). Usage: scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; N=PeasantM2d; IN=${IN:-mouth_v2.blend}
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(FINISH|LINING|CAP|ERR)|Traceback|Error' scripts/run.sh finish_pm2.py "$here/work/$IN" "$here/work/final_v1.blend"
F='^(COLLAR)|Traceback|Error' scripts/run.sh collar_lining.py "$here/work/final_v1.blend" "$here/work/final_v2.blend" | cut -c1-120
F='^(EXPORTED)|Traceback|Error' scripts/run.sh export_pm2.py "$here/work/final_v2.blend" "$here/work/pm2d_body.glb" | cut -c1-40
fi
Q "$G" scripts/clips_mm9.py work/pm2d_body.glb work/pm2d_clips0.glb scripts/roles_pm2.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/half_keys.py work/pm2d_clips0.glb work/pm2d_ref_h.glb | tail -1   # jitter reference: MM9 untouched + the same helper keys
Q "$G" scripts/arm_const.py work/pm2d_clips0.glb work/pm2d_clips1.glb $(cat scripts/arm_const.txt) | tail -2
cur=work/pm2d_clips1.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); eval "Q \"$G\" scripts/hand_rest.py $cur work/pm2d_rest$k.glb $line" | grep HANDREST | cut -c1-160; cur=work/pm2d_rest$k.glb
done < scripts/hand_rest_pm2.txt
if [[ -s scripts/armout_jobs.txt ]]; then Q "$G" scripts/arm_out.py $cur work/pm2d_out.glb $(cat scripts/armout_jobs.txt) | tail -2; cur=work/pm2d_out.glb; fi
Q "$G" scripts/half_keys.py $cur work/pm2d_clips2.glb | tail -1
Q "$G" scripts/skirt_keys.py work/pm2d_clips2.glb work/pm2d_final_clips.glb work/skirt_report.json | tail -1
Q "$G" "$repo/tools/prepare_actor_glb.py" work/pm2d_final_clips.glb export/mm9_peasantm2d_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_peasantm2d_runtime_lod0.glb" "$here/export/mm9_peasantm2d_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/mm9_peasantm2d_lods.glb export/mm9_peasantm2d_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" scripts/tiers_pm2.py export/mm9_peasantm2d_lods_shadowfix.glb export/mm9_peasantm2d_tiers.glb | tail -3
Q "$G" scripts/set_material_extras.py export/mm9_peasantm2d_tiers.glb export/mm9_peasantm2d_skins.glb openyamm_specular=0 pbr.metallicFactor=0 | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/mm9_peasantm2d_skins.glb export/mm9_peasantm2d.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/mm9_peasantm2d.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/mm9_peasantm2d.glb
if [[ -e export/mm9_peasantm2d_lods.geometry.glb ]]; then rm export/mm9_peasantm2d_lods.geometry.glb; fi
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_peasantm2d.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/mm9_peasantm2d.glb --world mm9; fi
ls -la export/mm9_peasantm2d.glb
