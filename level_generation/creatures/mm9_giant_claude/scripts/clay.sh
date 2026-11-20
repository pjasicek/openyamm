#!/bin/bash
# clay.sh <blend> <out png> <objects> [ortho] [center] [views]: clay tiles joined into one sheet (tiles deleted by name).
cd /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_giant_claude
t=$(/snap/bin/blender --background --factory-startup --python scripts/clay_blend.py -- "$@" 2>&1 | grep -E "^TILES|Error|Traceback")
echo "$t" | grep -v TILES
python3 -c "
import sys
from PIL import Image
fs=sys.argv[2].split(','); ims=[Image.open(f).convert('RGB') for f in fs]
s=Image.new('RGB',(700*len(ims),700))
for i,im in enumerate(ims): s.paste(im,(700*i,0))
s.save(sys.argv[1])
import os
for f in fs: os.remove(f)
" "$2" "$(echo "$t" | grep TILES | cut -c7-)"
