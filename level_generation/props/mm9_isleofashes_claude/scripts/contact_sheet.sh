#!/usr/bin/env bash
# The contact sheet of every converted prop (review renders from scripts/review.py: LOD0 front, three-quarter,
# side, behind-above, below, then LOD1/LOD2 three-quarter) -> ../../projects/mm9r_isleofashes/review/props_sheet.png
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
rows=()
for p in book coatrack cookpot cot dresser logsburning podium roundtable shipwreck skull statstone stonedebris02 \
         stonedebris03 stool vikingship well; do
    tris=$(python3 -c "import json; print('/'.join(map(str, json.load(open('work/${p}_meta.json'))['triangles'])))")
    r="mm9_deco_$p|$tris tris:"
    for v in front threequarter side back below; do r+="review/$p/lod0_$v.png,"; done
    for i in 1 2; do
        if [ -f "review/$p/lod${i}_threequarter.png" ] && [ "review/$p/lod${i}_threequarter.png" -nt "work/${p}_meta.json" ]; then
            r+="review/$p/lod${i}_threequarter.png,"
        else
            r+=","
        fi
    done
    rows+=("${r%,}")
done
python3 scripts/sheet.py ../../projects/mm9r_isleofashes/review/props_sheet.png "${rows[@]}" --cell 150
