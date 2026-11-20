#!/bin/bash
# PF7 rebuild from the paid paints (project folder): head fixes -> finish -> tiers -> finish -> tweak -> rig -> runtime -> viewer.
# Usage: scripts/rebuild.sh <viewer rev> [--install]   (run under the memory cap: systemd-run --user --scope -p MemoryMax=12G ...)
set -e
G=../claude_shared/gltf_venv/bin/python; export PYTHONPATH=/usr/lib/python3/dist-packages
[ -f scripts/tweak.env ] && { set -a; . scripts/tweak.env; set +a; }
for t in a b; do
  [ -f textures/pf_head_${t}_raw.png ] || continue
  $G -W ignore scripts/sym_paint.py work/uv.npz 1 textures/pf_head_${t}_raw.png textures/pf_head_${t}_sym.png > /dev/null 2>&1
  python3 scripts/head_fix_pf2.py $t textures/pf_head_${t}_sym.png textures/pf_head_${t}_fix.png
  if [ -f scripts/face_pf2.sh ]; then scripts/face_pf2.sh $t; fi
done
python3 scripts/finish_pf.py > /dev/null
python3 scripts/tiers_pf2.py | tail -1
python3 scripts/finish_pf.py > /dev/null
if [ -f scripts/tweak_pf2.py ]; then python3 scripts/tweak_pf2.py work/asm_frozen.npz work/uv_tex.npz work/uv_tex2.npz; else cp work/uv_tex.npz work/uv_tex2.npz; fi
if [ -f scripts/line_rims_pf2.sh ]; then scripts/line_rims_pf2.sh; M=work/uv_lined.npz; else M=work/uv_tex2.npz; fi
scripts/rig.sh $M 2>&1 | grep -E "Error|Trace|HALF" || true
scripts/build_runtime.sh $2 2>&1 | grep -E "WINDING|Error|Trace|nstall|LOD" || true
scripts/viewer_update.sh $1 | tail -1
echo REBUILT $1
