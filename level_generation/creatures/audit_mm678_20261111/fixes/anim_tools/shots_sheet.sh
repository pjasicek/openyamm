#!/usr/bin/env bash
# Viewer shots of the first tier before and after, as one sheet (top: installed before, bottom: anim fix).
#   shots_sheet.sh <project> <lease token> <sheet name> <clip:time:view:focus> ...   (from the repository root)
set -euo pipefail
P=$1; TK=$2; NAME=$3; shift 3
ids=$(python3 -c "import json;m=[x['id'] for x in json.load(open('$P/review/viewer/manifest.json'))['models']];a=[x for x in m if x.endswith('_after')][0];print(a.replace('_after','_before'),a)")
specs=(); i=0
for s in "$@"; do specs+=("s$i:$s"); i=$((i+1)); done
for M in $ids; do
    rm -rf "$P/review/shots"
    python3 tools/run_creature_review.py --project "$P" --token "$TK" --tier "$M" shots "${specs[@]}" | tail -1
    rm -rf "$P/review/shots_$M"; mkdir -p "$P/review/shots_$M"; mv "$P/review/shots/"*.png "$P/review/shots_$M/"
done
python3 - "$P/review" "$NAME" $i $ids <<'EOF'
import sys
from PIL import Image
root, name, n, ids = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4:]
rows = []
for m in ids:
    ims = [Image.open(f'{root}/shots_{m}/s{k}.png').convert('RGB') for k in range(n)]
    ims = [im.resize((im.width * 360 // im.height, 360)) for im in ims]
    r = Image.new('RGB', (sum(im.width for im in ims), 360))
    x = 0
    for im in ims:
        r.paste(im, (x, 0))
        x += im.width
    rows.append(r)
s = Image.new('RGB', (rows[0].width, 720))
s.paste(rows[0], (0, 0))
s.paste(rows[1], (0, 360))
s.save(f'{root}/{name}.png')
print(f'{root}/{name}.png')
EOF
