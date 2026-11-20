#!/bin/bash
# rebuild + viewer. TOKEN=.. REV=.. scripts/rv.sh [--install]
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_zombie_claude
scripts/rebuild.sh "$@" 2>&1 | grep -E "FAILED|Traceback|Error|WINDING|BUMP|DEPTH|SIGNS|ARMPIT|LOD triangles|PLUG|WELD|LINING|Dead:|nstalled|HANDREST" | cut -c1-200
PYTHONPATH=scripts ../claude_shared/gltf_venv/bin/python scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback"
python3 scripts/make_viewer_manifest.py ${REV:-r2_zombie_20261030} "zombie_a=Rotter (bare chest)=review/viewer/zombie_a.glb" "zombie_b=Dripper (vest)=review/viewer/zombie_b.glb" "zombie_c=Zombie (mail)=review/viewer/zombie_c.glb" | cut -c1-60
