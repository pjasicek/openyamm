#!/bin/bash
# Build XD-11's L4 from the generator, install it into assets_dev (the map's four files) and record.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd11/L4; X=$R/output/studio_cal/xd11
cd $R
python3 level_generation/projects/xeen/xd11/gen.py L4 || exit 1
$O fmt $L >/dev/null
$O validate $L --assets assets_dev | grep -v "^note: the asset root"
$O build $L --assets assets_dev --out $X/build 2>&1 | grep -v "Pandorian Box" | tail -8
$O install $L --build $X/build --root assets_dev >/dev/null || exit 1
$O record $L --author agent:xeen-a8-xd11 --label "${1:-generator run}" >/dev/null
