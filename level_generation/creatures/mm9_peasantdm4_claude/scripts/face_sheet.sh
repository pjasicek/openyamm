#!/usr/bin/env bash
# Face pre-screen sheet (VARIANTS_BRIEF face rules; user 2026-11-02: a receding chin seen only in profile, "two mouths"):
# MM9 (bind pose of the converted PEASANTDM4A model; LithTech handedness, so its profiles are mirrored) and ours (export,
# Standing frame 0 and Talk) at the same cameras on Bip01 Head: front, 3/4, right and left true profiles, low 3/4 from
# below the chin, party view 22 deg above (front and 3/4), each with a 128 px simulation of the party views.
# Usage (repo root): scripts/face_sheet.sh <rev> [glb]
set -euo pipefail
P=level_generation/creatures/mm9_peasantdm4_claude
R=$1; G=${2:-$P/export/mm9_pdm4.glb}
V="front|0|0 q34|35|0 profR|90|0 profL|-90|0 low34|30|-28 party|0|22 party34|35|22"
# targets: the face centre (eyes 0.44 m above MM9's origin in its centred frame; ours lifted 0.603 m, floor 0)
specs() { for v in $V; do IFS='|' read n az el <<< "$v"; echo "$1_$n|$2|$3|$4|$az|$el|$5"; done; }
mapfile -t S1 < <(specs mm9 bind 0 "0,-0.02,0.415" 0.36); mapfile -t S2 < <(specs ours Standing 0 "0,-0.02,1.02" 0.40)
mapfile -t S3 < <(specs talk Talk 60 "Bip01 Head" 0.46)
$P/scripts/blr.sh $P/scripts/closeup.py $PWD/$P/source/mm9/pdm4a.glb $PWD/$P/review/faces/$R a "${S1[@]}"
$P/scripts/blr.sh $P/scripts/closeup.py $PWD/$G $PWD/$P/review/faces/$R a "${S2[@]}" "${S3[@]}"
python3 - "$P/review/faces/$R" "$P/review/sheet_face_$R.png" <<'PY'
import sys
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]
views = ['front', 'q34', 'profR', 'profL', 'low34', 'party', 'party34']
rows = [('MM9 bind', 'mm9'), ('ours Standing', 'ours'), ('ours Talk 2.0 s', 'talk')]
W = 360; sheet = Image.new('RGB', (W * (len(views) + 2), W * len(rows)), (30, 30, 30)); dr = ImageDraw.Draw(sheet)
for r, (lab, p) in enumerate(rows):
    for c, v in enumerate(views):
        im = Image.open(f'{d}/{p}_{v}.png').convert('RGB')
        sheet.paste(im.resize((W, W)), (c * W, r * W)); dr.text((c * W + 4, r * W + 4), f'{lab} {v}', fill=(255, 255, 0))
    for k, v in enumerate(['party', 'party34']):     # 128 px simulation: the head about 40 px tall, as from party distance
        im = Image.open(f'{d}/{p}_{v}.png').convert('RGB')
        sim = im.resize((128, 128), Image.LANCZOS).resize((W, W), Image.NEAREST)
        x = (len(views) + k) * W; sheet.paste(sim, (x, r * W)); dr.text((x + 4, r * W + 4), f'{v} @128px', fill=(255, 255, 0))
sheet.save(out); print('FACESHEET', out, sheet.size)
PY
