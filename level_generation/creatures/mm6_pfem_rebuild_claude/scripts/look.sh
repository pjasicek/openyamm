#!/usr/bin/env bash
# look.sh <blend> <out png> [attr] [action:frame|-] [zoom x,y,z,size]: workbench tiles (front, right side, back, 3/4) joined into one strip
set -uo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
"$here/B.sh" look.py "$@" | grep -E "^LOOK" || exit 1
python3 -c "
import sys; from PIL import Image
o=sys.argv[1]; t=[Image.open(o+'.%d.png'%k) for k in range(4)]
im=Image.new('RGB',(sum(x.width for x in t),t[0].height)); x=0
for a in t: im.paste(a.convert('RGB'),(x,0)); x+=a.width
im.save(o)
import os; [os.remove(o+'.%d.png'%k) for k in range(4)]" "$2"
