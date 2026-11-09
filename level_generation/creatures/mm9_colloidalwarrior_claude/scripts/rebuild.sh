#!/usr/bin/env bash
# export -> clips -> helpers [-> clip corrections] -> prepare -> LODs -> shadow fix -> ramps -> floor -> winding [-> install] -> viewer.
# Usage (project folder): REV=rN scripts/rebuild.sh [--install]. SKIP_EXPORT=1 keeps work/cw_body.glb, SKIP_CLIPS=1 keeps work/cw_final_clips.glb.
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_colloidalwarrior; N=Colloidal; BLEND=${BLEND:-uv_v1.blend}
[[ -n "${SKIP_EXPORT:-}" ]] || F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_cw.py "$here/work/$BLEND" "$here/work/cw_body.glb"
if [[ -z "${SKIP_CLIPS:-}" ]]; then
"$G" scripts/head_band.py work/cw_body.glb work/cw_body_w.glb 2>&1 | grep -E 'WEIGHTS|Error|Traceback'
# armpit: UpperArm mixes through its helper, smoothed (neck_shoulder_weights.py from mm9_bigfoot_claude); head pivot 14 cm toward the face
# (collapse trials: back 8 cm worse, forward 8/14/20 cm Fidget head 72/49/49, Hit2 57/89/134, Death2 156/116/82: 14 kept)
# second pass: armpit wall to Spine2/Spine3 (bigfoot's FLANK, AttackMelee R shoulder 70 -> 55), larger smoothing band
FLANK=0.62,1.60,0.14,0.40,0.30 FLANK_SPLIT=1.25,1.45 FLANK_BONES=Spine2,Spine3 ONLY='L UpperArm,R UpperArm' RINGS=5 ITER=16 \
  "$G" scripts/neck_shoulder_weights.py work/cw_body_w.glb work/cw_body_ws.glb 2>&1 | grep -E 'WEIGHTS|Error|Traceback' | cut -c1-160
"$G" scripts/head_pivot.py work/cw_body_ws.glb work/cw_body_wp.glb 0 0 0.14 2>&1 | grep -E 'PIVOT|Error|Traceback'
# second pass, MM9's slab (bulk.py), tried and NOT kept: arms x1.12 / x1.25 thicker sank the forearms into the belly (Walking, Backpedal,
# Death2; Walking R unclearable at 1.25); the head 7 cm lower into the shoulders raised Death2 head collapse 93 -> 119 and Standing
# shoulders 11/8 -> 16/9. HEAD=0 ARM=1.0 keeps the body as is.
ARM=1.0 HEAD=${HEADLOW:-0} "$G" scripts/bulk.py work/cw_body_wp.glb work/cw_body_wb.glb 2>&1 | grep -E 'BULK|Error|Traceback'
"$G" scripts/head_pivot.py work/cw_body_wb.glb work/cw_body_wbp.glb 0 -${HEADLOW:-0} 0 2>&1 | grep -E 'PIVOT|Error|Traceback'
"$G" scripts/clips_mm9.py work/cw_body_wbp.glb work/cw_clips0.glb scripts/roles_cw.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
# second pass: head rotation soft cap 35/50 deg (Death2 head 116 -> 93, Hit2 89 -> 41 face-frames at the worst frame)
"$G" scripts/head_cap.py work/cw_clips0.glb work/cw_clips0c.glb 35 50 2>&1 | grep -E 'Fidget |Hit2|Death2|Error|Traceback'
"$G" scripts/half_keys.py work/cw_clips0c.glb work/cw_ref_clips.glb 2>&1 | tail -1        # the jitter reference: MM9's clips (head capped) with the helpers
cp work/cw_ref_clips.glb work/cw_final_clips.glb
if [[ -x scripts/clip_fix.sh ]]; then scripts/clip_fix.sh; fi                               # clip corrections (hands, head), writes work/cw_final_clips.glb
fi
"$G" "$repo/tools/prepare_actor_glb.py" work/cw_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb textures/cw_ramps.json \
  --extra Colloidal pbr.metallicFactor=0 --extra Colloidal openyamm_specular=${SPEC:-0.4} 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
python3 ../claude_shared/bone_length_audit.py export/${n}.glb | tail -3 | cut -c1-140
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 | tail -1 | cut -c1-160; fi
PYTHONPATH=scripts "$G" scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "cw_a=Colloidal Soldier (tan mud)=review/viewer/cw_a.glb" "cw_b=Colloidal Warrior (green slime)=review/viewer/cw_b.glb" "cw_c=Colloidal Guardian (rust)=review/viewer/cw_c.glb" | cut -c1-80
