#!/bin/bash
# build, full gate, then shots from this same build
REV=r9 scripts/rebuild.sh --install 2>&1 | grep -E 'WELD|WINDING|stretching|Traceback|^Error' | cut -c1-110
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
$G scripts/wrist_gate.py export/mm9_trellborg.glb 2>/dev/null | cut -c1-150 | tee review/gates/wrist.txt
scripts/wrist_sheet.sh | tail -1
echo R9_DONE
