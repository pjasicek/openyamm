#!/usr/bin/env bash
# Clay sheet of one clip frame: scripts/pose_sheet.sh <blend> <clip> <frame> <out.png> [centre x,y,z] [size] [views...]
set -e
cd "$(dirname "$0")/.."
B=$1; C=$2; F=$3; O=$4; CEN=${5:-0,-0.2,0.95}; SZ=${6:-2.0}; shift 6 2>/dev/null || shift $#
V=${@:-front three_quarter left -35:10}
T=$(mktemp -d /tmp/claude-1000/-home-pjasicek-github-OpenYAMM/ff001cf4-6927-455b-b1bb-249fd16968d3/scratchpad/hkr/ps.XXXX)
ACTION=$C FRAME=$F RES=${RES:-600} scripts/step.sh render_focus.py "$PWD/$B" "$T/v" "$CEN" "$SZ" $V
python3 - "$T" "$O" $V <<'PY'
import sys, glob
from PIL import Image
t, o, vs = sys.argv[1], sys.argv[2], sys.argv[3:]
ims = [Image.open(f"{t}/v_{v.replace(':', '_')}.png").convert('RGB') for v in vs]
w, h = ims[0].size; s = Image.new('RGB', (w * len(ims), h))
for i, im in enumerate(ims): s.paste(im, (i * w, 0))
s.save(o)
PY
