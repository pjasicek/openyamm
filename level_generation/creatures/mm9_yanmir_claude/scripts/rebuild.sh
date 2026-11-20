#!/usr/bin/env bash
# export -> clips -> fist -> staff on the floor -> arm out -> helpers -> hands cleared on keys -> helpers -> prepare -> LODs -> shadow
# fix -> floor -> winding [-> install]. Usage (project folder): REV=rN scripts/rebuild.sh [--install]
# SKIP_CLIPS=1 keeps work/yan_final_clips.glb (texture-only rebuilds; it carries the body of work/yan_body.glb)
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_yanmir; N=Yanmir; BLEND=${BLEND:-parts_r5.blend}
[[ -n "${SKIP_EXPORT:-}" ]] || F='^(SHARDS|LIFT|EXPORTED)' scripts/run.sh export_yan.py "$here/work/$BLEND" "$here/work/yan_body.glb"
if [[ -z "${SKIP_CLIPS:-}" ]]; then
# collapse follow-up (r2): head pivot 6 cm back and 2 cm up (the nape folded when MM9 throws the head back), head twist soft cap 28/40 deg
"$G" scripts/head_pivot.py work/yan_body.glb work/yan_body_p.glb 0 0.02 -0.06 2>&1 | grep -E 'PIVOT|Error|Traceback'
"$G" scripts/clips_mm9.py work/yan_body_p.glb work/yan_clips0.glb scripts/roles_yan.json work/clips.json 2>&1 | grep -E 'Error|Traceback'
"$G" scripts/finger_keys_yan.py work/yan_clips0.glb work/yan_clips1.glb work/hand_poses.json | tail -1
"$G" scripts/staff_floor.py work/yan_clips1.glb work/yan_clips1t.glb Death Death2 Dead | cut -c1-120
"$G" scripts/head_twist_cap.py work/yan_clips1t.glb work/yan_clips1s.glb 28 40 | grep -E 'Fidget2|Error' 
"$G" scripts/half_keys.py work/yan_clips1s.glb work/yan_ref_clips.glb 2>&1 | tail -1      # the jitter gate's reference: MM9's clips (+ fist, staff) with the same helpers
SIDES=L "$G" scripts/arm_out.py work/yan_clips1s.glb work/yan_clips2.glb ${ARM:-6} 2>&1 | tail -1
"$G" scripts/half_keys.py work/yan_clips2.glb work/yan_clips3.glb 2>&1 | tail -1
"$G" scripts/hand_clear_keys.py work/yan_clips3.glb work/yan_clips4.glb work/hand_clear.json 2>&1 | grep -E 'CLEAR|NOFIX|DONE|Error|Traceback' | cut -c1-200
"$G" scripts/half_keys.py work/yan_clips4.glb work/yan_final_clips.glb 2>&1 | tail -1
fi
"$G" "$repo/tools/prepare_actor_glb.py" work/yan_final_clips.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 </dev/null | grep -E "LOD triangles|Error"
"$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N 2>&1 | tail -1 | cut -c1-160
"$G" ../claude_shared/floor/floor_fix.py export/${n}_lods_shadowfix.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead 2>&1 | tail -2 | cut -c1-200
"$G" scripts/fix_winding.py export/${n}.glb work/wound.glb 2>&1 | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
"$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
python3 ../claude_shared/bone_length_audit.py export/${n}.glb | tail -3 | cut -c1-140
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9 | tail -1 | cut -c1-160; fi
python3 scripts/make_viewer_manifest.py ${REV:-r1} "yanmir=Yanmir=export/${n}.glb" 2>&1 | cut -c1-80
