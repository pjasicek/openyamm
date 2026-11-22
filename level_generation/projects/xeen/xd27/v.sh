#!/bin/bash
# regenerate L3 and L4, fmt, validate (the Xeen world's tables in assets_dev, read by build-xeen's oymap since A1's
# merge point 3; binary read-only)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; B=$R/devdocs/xeen/briefs/xd27; X=$R/output/studio_cal/xd27
cd $R && python3 level_generation/projects/xeen/xd27/make_l3.py >/dev/null && python3 level_generation/projects/xeen/xd27/gen.py --l3 >/dev/null && python3 level_generation/projects/xeen/xd27/gen.py >/dev/null || exit 1
$O fmt $B/L3 >/dev/null; $O fmt $B/L4 >/dev/null
echo "L3:"; $O validate $B/L3 --assets $R/assets_dev 2>&1 | grep -v "^note"
echo "L4:"; $O validate $B/L4 --assets $R/assets_dev 2>&1 | grep -v "^note"
