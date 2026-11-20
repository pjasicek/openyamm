#!/usr/bin/env bash
# Runtime GLBs: final master -> textured export -> MM9 clips -> fist -> skirt keys -> arm corrections -> prepare -> LODs -> shadow fix -> halberd split (two attachments) -> tier materials -> floor -> winding [-> install]
# Usage (project folder): TOKEN=<lease> scripts/build_runtime.sh [--install]
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
rel=level_generation/creatures/$(basename "$here"); n=mm9_guard; N=Guard; G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"
B() { local out log; out=$(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" "$@" 2>&1) || true
      log=$(echo "$out" | grep -o '/tmp/openyamm-creature-blender-[A-Za-z0-9]*\.log' | head -1)
      if grep -q "Error: script failed\|Traceback" "$log"; then grep -A12 Traceback "$log" | tail -14; echo "STEP FAILED: $1"; exit 1; fi
      grep -E "^(FINISH|LINING|GRIP|WRIST|FIST|THUMB|HIDDEN|HELPER|HEM|SHOULDER|EXPORTED|LIFT)" "$log" | cut -c1-200 || true; }
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
if [[ "${RESUME:-}" != tiers ]]; then
B "$rel/scripts/finish_guard.py" "$here/work/uv_v1.blend" "$here/work/final_v1.blend" "$here/work/hand_poses.json"
B "$rel/scripts/export_guard.py" "$here/work/final_v1.blend" "$here/work/guard_body_tex.glb"
Q "$G" scripts/clips_mm9.py work/guard_body_tex.glb work/guard_clips.glb scripts/roles_guard.json work/clips.json | tail -1 | cut -c1-200
Q "$G" scripts/finger_keys.py work/guard_clips.glb work/guard_fingers.glb work/hand_poses.json | tail -1
Q "$G" scripts/helper_keys.py work/guard_fingers.glb work/guard_h1.glb | tail -1
Q "$G" scripts/skirt_keys.py work/guard_h1.glb work/guard_skirt.glb work/skirt_keys.json | tail -1
cur=work/guard_skirt.glb; k=0
if [[ -f scripts/hand_rest_guard.txt ]]; then
  while IFS= read -r line; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    k=$((k + 1)); nxt=work/guard_rest${k}.glb
    eval "$G scripts/hand_rest.py $cur $nxt $line" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" | cut -c1-200
    cur=$nxt
  done < scripts/hand_rest_guard.txt
fi
Q "$G" scripts/pin_pole.py "$cur" work/guard_pin.glb Sleep | tail -2
Q "$G" scripts/pole_clear.py work/guard_pin.glb work/guard_pole.glb Death AttackMelee | grep CLEAR | cut -c1-120
Q "$G" scripts/dead_hold.py work/guard_pole.glb work/guard_dead.glb | tail -1
Q "$G" scripts/helper_keys.py work/guard_dead.glb work/guard_final_clips.glb | tail -1
Q "$G" "$repo/tools/prepare_actor_glb.py" work/guard_final_clips.glb export/${n}_runtime_lod0.glb | tail -1
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error"
Q "$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N | tail -1
Q "$G" scripts/swap_prop.py export/${n}_lods_shadowfix.glb work/lods_c.glb | tail -1
Q "$G" "$repo/tools/split_attachment.py" export/${n}_lods_shadowfix.glb --joint Xbase --body work/split_body.glb --attachment export/mm9_guard_halberd.glb | tail -1
Q "$G" "$repo/tools/split_attachment.py" work/lods_c.glb --joint Xbase --body work/split_body_c.glb --attachment export/mm9_guard_halberd2.glb | tail -1
fi
Q "$G" scripts/tier_materials.py work/split_body.glb work/tiers.glb | tail -1
F=../claude_shared/floor/floor_fix.py
Q "$G" $F work/tiers.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
rm -f export/${n}_lods.geometry.glb
"$G" scripts/make_plate.py | tail -2
for f in ${n} mm9_guard_halberd mm9_guard_halberd2 mm9_guard_plate_a mm9_guard_plate_c; do Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/$f.glb | tail -1; done
if [[ "${1:-}" == "--install" ]]; then for f in ${n} mm9_guard_halberd mm9_guard_halberd2 mm9_guard_plate_a mm9_guard_plate_c; do python3 "$repo/tools/install_model.py" export/$f.glb --world mm9 | tail -1; done; fi
ls -la export/${n}.glb export/mm9_guard_halberd.glb export/mm9_guard_halberd2.glb
