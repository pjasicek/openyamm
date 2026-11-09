#!/bin/bash
# Hanndl gates on v2/export/mm9_hanndl.glb (project folder): arm and hand, jitter vs MM9's clips, sleeve poke, see-through.
cd "$(dirname "$0")/.."
G=../claude_shared/gltf_venv/bin/python; O=v2/review/gates; mkdir -p $O/see_through
PYTHONPATH= $G v2/scripts/arm_hand_gate.py v2/export/mm9_hanndl.glb $O/arm.json --side "L= L " --side "R= R " --outer-only --exact > $O/arm.txt 2>&1
PYTHONPATH= $G v2/scripts/jitter_gate.py v2/export/mm9_hanndl.glb v2/work/mm9_hanndl_clips.glb $O/jitter.json --side "L= L " --side "R= R " > $O/jitter.txt 2>&1
PYTHONPATH= $G scripts/sleeve_poke_gate.py v2/export/mm9_hanndl.glb $O/sleeve_poke.json > $O/sleeve_poke.txt 2>&1
/snap/bin/blender --background --factory-startup --threads 4 --python scripts/see_through_gate.py -- $PWD/v2/export/mm9_hanndl.glb $PWD/$O/see_through/see_through.json step=4 > $O/see_through/log.txt 2>&1
echo GATES_DONE
