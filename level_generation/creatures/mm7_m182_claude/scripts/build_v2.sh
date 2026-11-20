#!/bin/bash
# v2 rebuild after the native fits (work/v2/fit/*.json from scripts/fit_native.py, run separately: slow).
# Usage: scripts/build_v2.sh [from-step]   steps: sym wing rig uv anim bake tex export
set -e
cd "$(dirname "$0")/.."
B="blender -b --python"
q() { grep -E "$1" || true; }
step=${1:-sym}
case $step in sym)
  python3 scripts/sym_v2.py | q SYM_V2
  $B scripts/mirror_half.py -- work/static_v4.blend work/v2/rest_co_v5a.npy work/v2/static_v5a.blend work/v2/mirror_report.json 2>&1 | q MIRROR
  $B scripts/dump_mesh.py -- work/v2/static_v5a.blend work/v2/static_v5a.npz 2>&1 | q DUMP
  python3 scripts/shoulder_envelope.py work/v2/static_v5a.npz work/v2/shoulder_env.npz
  $B scripts/clean_shoulder.py -- work/v2/static_v5a.blend work/v2/shoulder_env.npz work/v2/static_v5b.blend work/v2/shoulder_report.json 2>&1 | q SHOULDER
  ;& wing)
  python3 scripts/build_wing.py work/v2/shoulder_env.npz
  python3 scripts/wing_texture.py work/v2/wing_left.npz work/v2/wings_proc
  $B scripts/assemble_wing.py -- work/v2/static_v5b.blend work/v2/wing_left.npz work/v2/static_v5.blend 2>&1 | q ASSEMBLED
  ;& rig)
  $B scripts/reduce_v2.py -- work/v2/static_v5.blend 6 work/v2/static_v6.blend 2>&1 | q REDUCE
  $B scripts/rig_v2.py -- work/v2/static_v6.blend work/v2/rig_v3.blend 2>&1 | q "RIG|Error"
  $B scripts/rig_v2.py -- work/v2/static_v5.blend work/v2/rig_v2.blend 2>&1 | q "RIG|Error"
  $B scripts/dump_mesh.py -- work/v2/rig_v2.blend work/v2/rig_v2.npz 2>&1 | q DUMP
  ;& uv)
  $B scripts/uv_v2.py -- work/v2/rig_v3.blend work/v2/uv_rig.blend 2>&1 | q "UV_V2|Error"
  ;& anim)
  python3 scripts/clip_tables.py | q TABLES
  $B scripts/animate_v2.py -- work/v2/uv_rig.blend work/v2/anim_v2.blend 2>&1 | q "ANIMATED|Error"
  $B scripts/animation_gate.py -- work/v2/anim_v2.blend animation_gate.json 2>&1 | q "Error|Assert" 
  ;& bake)
  $B scripts/bake_v2.py -- work/v2/uv_rig.blend work/v2/bake_source.blend work/v2/bake 2>&1 | q "BAKED|Error"
  $B scripts/uv_raster_v2.py -- work/v2/uv_rig.blend work/v2 2>&1 | q "RASTER|Error"
  ;& tex)
  python3 scripts/compose_v2.py | cut -c1-300
  ;& export)
  $B scripts/export_v2.py 2>&1 | q "EXPORT|Error"
  python3 scripts/build_runtime.py prepare | q "bytes|kept|flipped"
  $B scripts/build_lods.py 2>&1 | q "LOD triangles|Error"
  python3 scripts/build_runtime.py finish | tail -1
  mkdir -p work/build; mv export/mm7_m182_prepared.glb export/mm7_m182_lods.glb export/mm7_m182_lods.geometry.glb export/mm7_m182_lods_shadow.glb work/build/
  python3 ../../decorations/mm8_3d/animated/scripts/check_winding.py export/mm7_m182.glb | tail -1
  python3 scripts/viewer.py
  ;;
esac
