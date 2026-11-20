#!/bin/bash
# arm and hand contacts cleared by one windowed bump per contact (arm_bump.py, ~30 min). Reuses <out> when it is newer than <in>. Args: <in glb> <out glb>
G=/home/pjasicek/github/OpenYAMM/level_generation/creatures/claude_shared/gltf_venv/bin/python
if [[ "$2" -nt "$1" && -z "${FORCE_ARM:-}" ]]; then echo "ARMFIX reused $2"; exit 0; fi
"$G" scripts/arm_bump.py "$1" "$2" Fidget2:R Taunt:R AttackMelee:R:0.6:0.42:0.85:mallet AttackMelee:R:0.42:0.6:1.0:both Death:L Death2:L:0.3 Death:R:0.3:0.95:1.15:mallet Death:R:0.3:2.35:2.9:mallet 2>&1 | grep -E 'BUMP|Error|Traceback' | cut -c1-200
