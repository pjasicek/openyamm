#!/bin/bash
# build and install into the Xeen world (assets_dev/worlds/xeen/maps; only the map's files), then audit and solve
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd06/L4; X=$R/output/studio_cal/xd06
cd $R; $O fmt $L >/dev/null
$O build $L --assets $R/assets_dev --out $X/build 2>&1 | grep -v "placeholder not built" | tail -5
$O install $L --build $X/build --root $R/assets_dev | tail -4
M=$R/assets_dev/worlds/xeen/maps/xeen_xd06.blv
$O audit $M --world xeen --assets $R/assets_dev --reach --solve > $X/audit_world.txt 2>&1; sed -n 3p $X/audit_world.txt
$O solve $M --world xeen --assets $R/assets_dev > $X/solve_world.txt 2>&1; grep "never reached\|exits:" $X/solve_world.txt
