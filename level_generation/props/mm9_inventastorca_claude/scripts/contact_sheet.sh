#!/usr/bin/env bash
# The contact sheet of every Inventa Storca prop (review renders from scripts/review.py: LOD0 front, three-quarter, side,
# behind-above, below, then LOD1/LOD2 three-quarter) -> review/props_sheet.png, with the isle project's sheet.py.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
cd "$HERE"
rows=()
for p in $(ls work/*_meta.json | sed 's#work/##; s#_meta.json##'); do
    tris=$(python3 -c "import json; print('/'.join(map(str, json.load(open('work/${p}_meta.json'))['triangles'])))")
    r="mm9_deco_$p|$tris tris:"
    for v in front threequarter side back below; do r+="review/$p/lod0_$v.png,"; done
    for i in 1 2; do
        if [ -f "review/$p/lod${i}_threequarter.png" ]; then r+="review/$p/lod${i}_threequarter.png,"; else r+=","; fi
    done
    rows+=("${r%,}")
done
python3 ../mm9_isleofashes_claude/scripts/sheet.py review/props_sheet.png "${rows[@]}" --cell 150
