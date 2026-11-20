#!/bin/bash
# graded maps -> final images (project folder)
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
rm -f textures/thrall_torso_a_preseam.png textures/thrall_torso_b_preseam.png textures/thrall_torso_c_preseam.png
$G scripts/soft_tex.py 2>&1 | tail -1
$G scripts/finish_tex.py
PYTHONPATH=scripts $G scripts/pale_fill.py 2>&1 | grep -E 'PALE|PELT|Trace|Error' | cut -c1-120
PYTHONPATH=scripts $G scripts/tier_ramps.py 2>&1 | grep -E 'done|Trace|Error' | cut -c1-200
PYTHONPATH=scripts $G scripts/seam_fix.py 2>&1 | grep -E 'SEAM|Trace|Error' | cut -c1-160
