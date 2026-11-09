#!/bin/bash
# rebuild + viewer. TOKEN=.. REV=.. scripts/rv.sh [--install]
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_ghoul_claude
scripts/rebuild.sh "$@" 2>&1 | grep -E "FAILED|Traceback|Error|WINDING|FLAP|BUMP|DEPTH|PLUG|LINING|Dead:|nstalled|checked|LIFT|Thigh|Calf|LOD triangles|inverted|mm9_ghoul.glb" | cut -c1-200
PYTHONPATH=scripts ../claude_shared/gltf_venv/bin/python scripts/viewer_tiers.py 2>&1 | grep -E "Error|Traceback"
python3 scripts/make_viewer_manifest.py ${REV:-r1_ghoul_20261031} "ghoul_a=Ghast (olive)=review/viewer/ghoul_a.glb" "ghoul_b=Ghoul (slate)=review/viewer/ghoul_b.glb" "ghoul_c=Revenant (ash)=review/viewer/ghoul_c.glb" | cut -c1-60
