#!/bin/bash
# Regenerate, build, install into the scratch root and audit (no game run). Usage: level_generation/projects/xeen/d7/cycle.sh
cd "$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"
X=output/studio_cal/d7; R=$X/root/assets_dev; OY=openyamm-studio/build-xeen/oymap
level_generation/projects/xeen/d7/v.sh $R 2>&1 | grep -v "no issues\|^==" | head -5
$OY build devdocs/xeen/briefs/d7/L4 --out $X/build --assets $R > $X/build.log 2>&1 || { cut -c1-300 $X/build.log | head; exit 1; }
grep -v "^built" $X/build.log | cut -c1-220; grep "^built" $X/build.log
[ -f level_generation/projects/xeen/d7/gen_playtests.py ] && systemd-run --user --scope -q -p MemoryMax=8G python3 level_generation/projects/xeen/d7/gen_playtests.py
$OY fmt devdocs/xeen/briefs/d7/L4 > /dev/null
$OY install devdocs/xeen/briefs/d7/L4 --root $R --build $X/build > $X/install_root.log 2>&1 || tail -3 $X/install_root.log
N=${N:-20} bash $X/a.sh
