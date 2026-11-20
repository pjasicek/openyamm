#!/usr/bin/env bash
# export -> clips -> helpers -> prepare -> LODs -> shadow fix -> ramps -> Yeti head -> floor -> winding [-> install]. Usage (project folder): REV=rN scripts/rebuild.sh [--install]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_bigfoot; N=Bigfoot; BLEND=${BLEND:-uv_v1.blend}
[[ -n "${SKIP_EXPORT:-}" ]] || F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_bf.py "$here/work/$BLEND" "$here/work/bf_body.glb"
# clips (run 2): MM9 clips with the soft offset line -> constant arm abduction -> helpers -> hands cleared on keys (hand_clear_keys.py, ~40 min) -> helpers again.
# SKIP_CLIPS=1 keeps work/bf_final_clips.glb (it carries the body of work/bf_body.glb: only for texture-only rebuilds)
if [[ -z "${SKIP_CLIPS:-}" ]]; then
# collapse follow-up (r8): neck and armpit weights, head pivot 8 cm forward, head twist soft cap 50/75 deg
THROAT=0.08,0.18 FLANK=0.40,1.95,0.08,0.25,0.16 ONLY=Head HEAD_PARENTS=Spine3 RINGS=0 ITER=0 "$G" scripts/neck_shoulder_weights.py work/bf_body.glb work/bf_body_w.glb 2>&1 | grep -E 'WEIGHTS|Error|Traceback'
"$G" scripts/head_pivot.py work/bf_body_w.glb work/bf_body_wp.glb 0 0 0.08 2>&1 | grep -E 'PIVOT|Error|Traceback'
"$G" scripts/clips_mm9.py work/bf_body_wp.glb work/bf_clips0a.glb scripts/roles_bf.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
"$G" scripts/head_twist_cap.py work/bf_clips0a.glb work/bf_clips0.glb 50 75 2>&1 | grep -E 'WalkFidget|Hit2|Error|Traceback'
"$G" scripts/arm_out.py work/bf_clips0.glb work/bf_clips1.glb ${ARM:-12} 2>&1 | tail -1
"$G" scripts/half_keys.py work/bf_clips1.glb work/bf_clips2.glb 2>&1 | tail -1
"$G" scripts/half_keys.py work/bf_clips0.glb work/bf_ref_clips.glb 2>&1 | tail -1      # the jitter gate's reference: MM9's clips with the same helpers
"$G" scripts/hand_clear_keys.py work/bf_clips2.glb work/bf_clips3.glb work/hand_clear.json 2>&1 | grep -E 'CLEAR|NOFIX|DONE|Error|Traceback' | cut -c1-200
"$G" scripts/half_keys.py work/bf_clips3.glb work/bf_final_clips.glb 2>&1 | tail -1
fi
"$G" "$repo/tools/prepare_actor_glb.py" work/bf_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins0.glb textures/bf_ramps.json \
  --extra Bigfoot openyamm_specular=0 --extra Bigfoot pbr.metallicFactor=0 2>&1 | tail -1 | cut -c1-160
"$G" scripts/tier_head_c.py export/${n}_skins0.glb export/${n}_skins.glb 2>&1 | tail -1
"$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
python3 ../claude_shared/bone_length_audit.py export/${n}.glb | tail -3 | cut -c1-140
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 | tail -1 | cut -c1-160; fi
PYTHONPATH=scripts "$G" scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "bf_a=Bigfoot (brown)=review/viewer/bf_a.glb" "bf_b=Sasquatch (dark, silver saddle)=review/viewer/bf_b.glb" "bf_c=Yeti (white)=review/viewer/bf_c.glb" | cut -c1-80
