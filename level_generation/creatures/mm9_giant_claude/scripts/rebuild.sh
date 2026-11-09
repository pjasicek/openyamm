#!/usr/bin/env bash
# export -> clips (MM9, finger keys, helpers) -> prepare -> LODs -> shadow fix -> ramps -> tier heads -> floor -> winding [-> install] -> viewer.
# Usage (project folder): REV=rN scripts/rebuild.sh [--install]. BLEND (default fist_v2.blend). SKIP_EXPORT / SKIP_CLIPS reuse work files.
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_giant; N=Giant; BLEND=${BLEND:-fist_v2.blend}
[[ -n "${SKIP_EXPORT:-}" ]] || F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_giant.py "$here/work/$BLEND" "$here/work/gi_body.glb"
if [[ -z "${SKIP_CLIPS:-}" ]]; then
"$G" scripts/clips_mm9.py work/gi_body.glb work/gi_clips0.glb scripts/roles_giant.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
"$G" scripts/finger_keys_giant.py work/gi_clips0.glb work/gi_clips1a.glb work/hand_poses.json 2>&1 | grep -E 'FINGERKEYS|Error|Traceback'
"$G" scripts/grip_lock.py work/gi_clips1a.glb work/gi_clips1.glb 2>&1 | grep -E 'GRIPLOCK|Error|Traceback' | cut -c1-200
"$G" scripts/half_keys.py work/gi_clips0.glb work/gi_ref_clips.glb 2>&1 | tail -1      # jitter reference: MM9's clips with the same helpers
if [[ -f scripts/arm_fix.sh ]]; then bash scripts/arm_fix.sh work/gi_clips1.glb work/gi_clips2.glb; else cp work/gi_clips1.glb work/gi_clips2.glb; fi
"$G" scripts/left_ik.py work/gi_clips2.glb work/gi_clips2ik.glb 2>&1 | grep -E 'LEFTIK|Error|Traceback' | cut -c1-400      # two-handed grip: the left fist on the shaft
"$G" scripts/left_grip.py work/gi_clips2ik.glb work/gi_clips3.glb 2>&1 | grep -E 'Error|Traceback'      # left fingers and thumb clear of the shaft outside the grip
"$G" scripts/arm_bump.py work/gi_clips3.glb work/gi_clips3b.glb Fidget:L:0.45:0:9:shaftbody Aware:L:0.3:0:9:shaft AttackMelee3:L:0.3:0:9:shaft AttackRanged:L:0.45:0:9:shaft Hit:L:0.3:0:9:shaft Hit2:L:0.3:0:9:shaft Death:L:0.3:0:9:shaft Death2:L:0.3:0:9:shaft AttackMelee:L:0.3:0.3:0.5 AttackMelee:R:0.45:0.4:0.9:mallet 2>&1 | grep -E 'BUMP|Error|Traceback' | cut -c1-200      # after the grip (third pass): the left hand off the shaft outside its grip, the fists apart at the top of the swing, the mallet out of the body
LG_CLIPS=Fidget "$G" scripts/left_grip.py work/gi_clips3b.glb work/gi_clips3bb.glb 2>&1 | grep -E 'Error|Traceback'; mv work/gi_clips3bb.glb work/gi_clips3b.glb      # r23: Fidget's shaftbody bump moves the open left hand after left_grip cleared its fingers: clear them again
"$G" scripts/corpse_mallet.py work/gi_clips3b.glb work/gi_clips3c.glb 2>&1 | grep CORPSE      # the corpse's mallet out of its thigh
"$G" scripts/half_keys.py work/gi_clips3c.glb work/gi_final_clips.glb 2>&1 | tail -1
fi
"$G" "$repo/tools/prepare_actor_glb.py" work/gi_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/gi_ramps.json \
  --extra Giant openyamm_specular=0 --extra Giant pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" scripts/tier_head.py export/${n}_skins0.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
if [[ -f export/mm9_giant_lods.geometry.glb ]]; then rm export/mm9_giant_lods.geometry.glb; fi
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
python3 ../claude_shared/bone_length_audit.py export/${n}.glb | tail -3 | cut -c1-140
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 | tail -1 | cut -c1-160; fi
PYTHONPATH=scripts "$G" scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "gi_a=Plain Giant (red braids, leather, wooden mallet)=review/viewer/gi_a.glb" "gi_b=Forest Giant (dark hair, bare chest, steel mallet)=review/viewer/gi_b.glb" | cut -c1-80
