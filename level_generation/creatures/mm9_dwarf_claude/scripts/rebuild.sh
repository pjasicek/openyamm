#!/usr/bin/env bash
# After the paint: reweight -> finish -> export -> clips -> fingers -> corrections -> helpers -> skirt legs -> skirt -> axe hide -> arm bumps -> head clear -> axe lift -> prepare -> LODs -> shadow fix -> ramps -> floor -> winding [-> install] -> viewer. Project folder: scripts/rebuild.sh [--install]
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
G="$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python"; n=mm9_dwarf; N=Dwarf; IN=${IN:-rew_v1.blend}
if [[ -z "${SKIP_EXPORT:-}" ]]; then
F='^(REWEIGHT|SKIRT|ERR)' scripts/run.sh reweight.py "$here/work/uv_v1.blend" "$here/work/rew_v1.blend"
F='^(FINISH|ERR)' W=170 scripts/run.sh finish_dwarf.py "$here/work/$IN" "$here/work/final_v1.blend" "$here/work/hand_poses.json"
F='^(EXPORTED)' scripts/run.sh export_dwarf.py "$here/work/final_v1.blend" "$here/work/dwarf_body.glb" | cut -c1-120
fi
Q() { "$@" 2>&1 | grep -v "Unexpected value\|RuntimeWarning" ; }
Q "$G" scripts/clips_mm9.py work/dwarf_body.glb work/dwarf_clips0.glb scripts/roles_dwarf.json work/clips.json | tail -1 | cut -c1-120
Q "$G" scripts/finger_keys.py work/dwarf_clips0.glb work/dwarf_clips1.glb work/hand_poses.json | tail -1
cp work/dwarf_clips1.glb work/dwarf_clips1d.glb
if [[ -f scripts/corrections.sh ]]; then source scripts/corrections.sh; fi
Q "$G" scripts/half_keys.py work/dwarf_clips1d.glb work/dwarf_clips2.glb | tail -1
Q "$G" scripts/skirt_leg_keys.py work/dwarf_clips2.glb work/dwarf_clips2l.glb | tail -1
Q "$G" scripts/skirt_keys.py work/dwarf_clips2l.glb work/dwarf_clips3.glb work/skirt_report.json | tail -1
Q "$G" scripts/axe_hide.py work/dwarf_clips3.glb work/dwarf_clips4.glb | tail -1
if [[ -s scripts/arm_jobs.txt ]]; then
  Q "$G" scripts/arm_bump.py work/dwarf_clips4.glb work/dwarf_clips5.glb $(cat scripts/arm_jobs.txt) | grep -E "BUMP|Traceback|Error" | cut -c1-170
else cp work/dwarf_clips4.glb work/dwarf_clips5.glb; fi
Q "$G" scripts/head_clear.py work/dwarf_clips5.glb work/dwarf_clips6.glb | grep -E "max_f': 0\.[1-9]|HEAD|Traceback|Error" | cut -c1-170
Q "$G" scripts/axe_lift.py work/dwarf_clips6.glb work/dwarf_final_clips.glb Fidget AttackMelee3 | grep -E "AXE|Traceback|Error" | cut -c1-170
Q "$G" "$repo/tools/prepare_actor_glb.py" work/dwarf_final_clips.glb export/${n}_runtime_lod0.glb | tail -1 | cut -c1-160
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${n}_runtime_lod0.glb" "$here/export/${n}_lods.glb" --mesh-node $N --max-influences 4 2>&1 | grep -E "LOD triangles|Error" | cut -c1-200
Q "$G" scripts/shrink_shadow_lods.py export/${n}_lods.glb export/${n}_lods_shadowfix.glb $N | tail -1 | cut -c1-160
if [[ -f textures/dwarf_ramps.json ]]; then
Q "$G" ../claude_shared/region_variants.py export/${n}_lods_shadowfix.glb export/${n}_skins.glb textures/dwarf_ramps.json \
  --extra DwarfTorso openyamm_specular=0 --extra DwarfLimbs openyamm_specular=0 --extra DwarfHead openyamm_specular=0 --extra DwarfTorso pbr.metallicFactor=0 --extra DwarfLimbs pbr.metallicFactor=0 --extra DwarfHead pbr.metallicFactor=0 \
  --extra DwarfWeapon openyamm_specular=0.3 --extra DwarfWeapon pbr.metallicFactor=0.35 | tail -1 | cut -c1-160
else cp export/${n}_lods_shadowfix.glb export/${n}_skins.glb; fi
Q "$G" ../claude_shared/floor/floor_fix.py export/${n}_skins.glb export/${n}.glb $(cat scripts/floor_ops.txt) --ground-death Death Dead | tail -2 | cut -c1-200
Q "$G" scripts/fix_winding.py export/${n}.glb work/wound.glb | tail -1 | cut -c1-120; mv work/wound.glb export/${n}.glb
rm -f export/${n}_lods.geometry.glb
Q "$G" "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${n}.glb | tail -1
if [[ "${1:-}" == "--install" ]]; then python3 "$repo/tools/install_model.py" export/${n}.glb --world mm9; fi
ls -la export/${n}.glb
mkdir -p review/viewer
Q "$G" scripts/viewer_tiers.py | grep -E "Error|Traceback" || true
python3 scripts/make_viewer_manifest.py ${REV:-r1} "dwarf_a=Dwarven Guard=review/viewer/dwarf_a.glb" "dwarf_b=Dwarven Soldier=review/viewer/dwarf_b.glb" "dwarf_c=Dwarven Commander=review/viewer/dwarf_c.glb" | cut -c1-80
