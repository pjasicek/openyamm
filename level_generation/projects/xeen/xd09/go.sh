#!/bin/bash
# build, audit and solve the build, install into the Xeen world (only the map's files), then audit the installed map
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd09/L4; X=$R/output/studio_cal/xd09
cd $R; $O fmt $L >/dev/null
$O build $L --assets $R/assets_dev --out $X/build > $X/build.txt 2>&1; grep -v "placeholder not built" $X/build.txt | tail -8
B=$X/build/xeen_xd09.blv; ls $X/build/*.blv >/dev/null 2>&1 && B=$(ls $X/build/*.blv | head -1)
$O audit $B --world xeen --assets $R/assets_dev --reach --solve > $X/audit.txt 2>&1; head -5 $X/audit.txt
$O install $L --build $X/build --root $R/assets_dev | tail -4
M=$R/assets_dev/worlds/xeen/maps/xeen_xd09.blv
$O audit $M --world xeen --assets $R/assets_dev --reach --solve > $X/audit_world.txt 2>&1; head -5 $X/audit_world.txt
$O solve $M --world xeen --assets $R/assets_dev > $X/solve_world.txt 2>&1; grep -i "never reached\|exits" $X/solve_world.txt
