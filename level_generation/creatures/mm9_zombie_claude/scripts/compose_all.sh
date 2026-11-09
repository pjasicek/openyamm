#!/bin/bash
# textures from the graded maps (project folder): soft_detail -> torso images -> ramps -> torso finish -> repacked body maps
G=$PWD/../claude_shared/gltf_venv/bin/python
PYTHONPATH=scripts $G scripts/soft_detail.py 2>&1 | grep -E 'NECK|SOFT|Traceback|Error'
PYTHONPATH=scripts $G scripts/torso_images.py 2>&1 | grep -E 'Traceback|Error'
PYTHONPATH=scripts $G scripts/tier_ramps.py 2>&1 | grep -E 'Traceback|Error|RAMPS|head '
PYTHONPATH=scripts $G scripts/torso_finish.py 2>&1 | grep -E 'Traceback|Error|TORSO'
PYTHONPATH=scripts $G scripts/head_match.py 2>&1 | grep -E 'px/m|pool|join|HEADMATCH|Traceback|Error'
PYTHONPATH=scripts $G scripts/repack_maps.py 2>&1 | grep -E 'atlas|scale|REPACK|Traceback|Error'
