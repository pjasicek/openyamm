#!/usr/bin/env bash
# After the paints: export -> clips -> helpers -> arm bumps -> skirt -> prepare -> LODs -> shadow fix -> ramps -> tier parts -> floor -> winding [-> install]. Usage (project folder): scripts/rebuild.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_thrall; N=Thrall; BLEND=${BLEND:-uv_v3.blend}
[[ -n "${SKIP_EXPORT:-}" ]] || F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_thrall.py "$here/work/$BLEND" "$here/work/thrall_body.glb"
"$G" scripts/clips_mm9.py work/thrall_body.glb work/thrall_clips0.glb scripts/roles_thrall.json work/clips.json 2>&1 | grep -v Unexpected | cut -c1-120
"$G" scripts/half_keys.py work/thrall_clips0.glb work/thrall_clips1.glb 2>&1 | tail -1
"$G" scripts/skirt_keys.py work/thrall_clips1.glb work/thrall_clips2.glb work/skirt_report.json 2>&1 | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  "$G" scripts/arm_bump.py work/thrall_clips2.glb work/thrall_final_clips.glb $(cat scripts/arm_jobs.txt) 2>&1 | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/thrall_clips2.glb work/thrall_final_clips.glb; fi
"$G" "$repo/tools/prepare_actor_glb.py" work/thrall_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/thrall_ramps.json \
  --extra Thrall openyamm_specular=0 --extra Thrall pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" scripts/tier_variants.py export/${n}_skins0.glb export/${n}_skins.glb 2>&1 | grep -v Unexpected | tail -2 | cut -c1-200
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
PYTHONPATH=scripts "$G" scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "thrall_a=Field Thrall (tunic)=review/viewer/thrall_a.glb" "thrall_b=Thrall (half pelt)=review/viewer/thrall_b.glb" "thrall_c=Thrall Master (bare chest)=review/viewer/thrall_c.glb" | cut -c1-80
