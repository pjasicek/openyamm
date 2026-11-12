#!/usr/bin/env bash
# uv blend -> body GLB -> MM9 clips -> material -> prepare -> LODs -> shadow tuck -> tier variants -> far LODs (lod
# repair steps) -> floor -> winding -> export/mm8_lizardman_peasant.glb [--install]. TOKEN=<lease> scripts/build_runtime.sh
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"
rel=level_generation/creatures/$(basename "$here"); n=mm8_lizardman_peasant
PY=$repo/level_generation/creatures/claude_shared/gltf_venv/bin/python
LR=$repo/level_generation/creatures/lod_repair_claude/scripts; MLPY=$here/../mm6_ttn_rebuild_claude/work/lodrep_venv/bin/python
L=$repo/level_generation/creatures/claude_shared
export PYTHONPATH=$(python3 -c "import yaml,os;print(os.path.dirname(os.path.dirname(yaml.__file__)))")
cd "$here"; mkdir -p export
(cd "$repo" && tools/run_creature_blender.sh --token "$TOKEN" $rel/scripts/export_body.py "$here/${BLEND:-work/uv_v1.blend}" "$here/work/body_uv.glb" >/dev/null)
$PY scripts/clips_mm9.py work/body_uv.glb work/raw_clips.glb scripts/roles_lizp.json work/clips.json 2>&1 | grep CLIPS
$PY scripts/attach_material.py work/raw_clips.glb work/mat.glb 2>&1 | grep MATERIAL
$PY "$repo/tools/prepare_actor_glb.py" work/mat.glb export/${n}_runtime_lod0.glb 2>&1 | tail -1
(cd "$repo" && python3 tools/creature_workspace.py run --project "$here" --token "$TOKEN" -- \
  /snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python tools/build_actor_lods.py -- "$here/export/${n}_runtime_lod0.glb" "$here/work/lods.glb" --mesh-node Lizardman_Body --max-influences 4 2>&1 | grep -E "LOD triangles|Error")
rm -f work/lods.geometry.glb
$PY scripts/shrink_shadow_lods.py work/lods.glb work/lods_s.glb Lizardman_Body 2>&1 | tail -1 | cut -c1-200
$PY $L/region_variants.py work/lods_s.glb work/skins.glb textures/liz_ramps.json 2>&1 | tail -1 | cut -c1-200
mkdir -p work/lodrep
$MLPY $LR/build_lods.py work/skins.glb Lizardman_Body work/lodrep/built.glb 2:0.25,3:0.125 | tail -1
$MLPY $LR/unwrap_lods.py work/lodrep/built.glb Lizardman_Body work/lodrep/bake 2:512,3:256 | tail -1
$MLPY $LR/transfer_textures.py work/lodrep/built.glb Lizardman_Body work/lodrep/bake | tail -1
$MLPY $LR/apply_bake.py work/lodrep/built.glb Lizardman_Body work/lodrep/bake work/far.glb 2,3 | tail -1
$PY scripts/hand_rest.py work/far.glb work/far_hr.glb --clip Fidget --side "L= L " --side "R= R " --surface-joints Spine,Pelvis,Thigh --sigma-time 0.24 --hold-time 0.12 --max-push 0.05 --sigma-dir 0.3 2>&1 | grep HANDREST | cut -c1-200
$PY $L/floor/floor_fix.py work/far_hr.glb export/$n.glb $(cat scripts/floor_ops.txt) 2>&1 | tail -2 | cut -c1-200
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/$n.glb | tail -1
if [[ " $* " == *" --install "* ]]; then (cd "$repo" && python3 tools/install_model.py "$here/export/$n.glb" --world mm8); fi
