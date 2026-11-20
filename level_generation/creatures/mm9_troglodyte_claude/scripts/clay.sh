#!/bin/bash
# scripts/clay.sh <npz> <prefix> [size] [center] [ortho], from the project folder; contact sheet <prefix>_sheet.png
P=$PWD; cd /home/pjasicek/github/OpenYAMM; T=be3ecdfca5fa4ec5b09123d1327bc520
env -u PYTHONPATH tools/run_creature_blender.sh --token $T level_generation/creatures/mm9_troglodyte_claude/scripts/clay.py $P/$1 $P/$2 ${3:-700} ${4:-} ${5:-} >/dev/null
cd $P; python3 - "$2" <<'PY'
import sys,glob
from PIL import Image
fs=[f for f in sorted(glob.glob(sys.argv[1]+'_*.png')) if not f.endswith('sheet.png')]
if not fs: raise SystemExit('none')
w=Image.open(fs[0]).size[0]; s=Image.new('RGB',(w*len(fs),w))
for i,f in enumerate(fs): s.paste(Image.open(f).convert('RGB'),(i*w,0))
s.save(sys.argv[1]+'_sheet.png'); print(sys.argv[1]+'_sheet.png')
PY
