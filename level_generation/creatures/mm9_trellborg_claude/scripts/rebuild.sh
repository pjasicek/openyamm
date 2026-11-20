#!/usr/bin/env bash
# After the paints: club -> export -> clips -> wrist keys -> helpers -> arm bumps -> prepare -> LODs -> shadow fix -> head ramps -> tier materials -> floor -> winding [-> install] -> viewer. Project folder: REV=rN scripts/rebuild.sh [--install]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_trellborg; N=Trellborg; IN=${IN:-fist_v1.blend}
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(REWEIGHT|ERR)' scripts/run.sh reweight.py "$here/work/uv_v1.blend" "$here/work/rew_v1.blend"
F='^(TAPER|WELD|Traceback|Error)' W=150 scripts/run.sh fist.py "$here/work/rew_v1.blend" "$here/work/fist_v1.blend"
Q "$G" scripts/make_club.py | tail -1
F='^(CLUB|ERR)' scripts/run.sh add_club.py "$here/work/$IN" "$here/work/final_v1.blend" | tail -1
F='^(CUFF|Traceback|Error)' W=160 scripts/run.sh add_cuffs.py "$here/work/final_v1.blend" "$here/work/final_c.blend"
F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_trell.py "$here/work/final_c.blend" "$here/work/trell_body.glb" | tail -1 | cut -c1-120
fi
Q "$G" scripts/clips_mm9.py work/trell_body.glb work/trell_clips0.glb scripts/roles_trell.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/club_keys.py work/trell_clips0.glb work/trell_clips0c.glb work/grip.json | tail -1 | cut -c1-200
Q "$G" scripts/half_keys.py work/trell_clips0c.glb work/trell_clips1.glb | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/trell_clips1.glb work/trell_final_clips.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/trell_clips1.glb work/trell_final_clips.glb; fi
Q "$G" "$repo/tools/prepare_actor_glb.py" work/trell_final_clips.glb export/${n}_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
Q "$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N | tail -1 | cut -c1-160
Q "$G" scripts/tier_materials.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb | tail -1 | cut -c1-160
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
python3 ../claude_shared/bone_length_audit.py export/${n}.glb | tail -1 | cut -c1-140
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
if [[ -n "${VIEWER_OK:-}" ]]; then V=viewer; else V=viewer_test; fi; export VIEWER=$V
Q "$G" scripts/viewer_tiers.py | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "trell_a=Trellborg=review/$V/trell_a.glb" "trell_b=Kin Trellborg=review/$V/trell_b.glb" "trell_c=Ancient Trellborg=review/$V/trell_c.glb" | cut -c1-80
