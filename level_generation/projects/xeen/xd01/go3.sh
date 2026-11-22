#!/bin/bash
# Third pass (textures): fmt, validate, build into build3/, install into mount3/ (headless playtests) and the scratch root.
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
set -e
R=$OYR
O=$R/openyamm-studio/build/oymap
L=$R/devdocs/xeen/briefs/xd01/L4
X=$R/output/studio_cal/xd01
cd $R
$O fmt $L >/dev/null
$O validate $L --assets assets_dev
$O build $L --assets assets_dev --out $X/build3 2>&1 | grep -v "is named" || true
$O install $L --build $X/build3 --mount $X/mount3 --assets assets_dev >/dev/null
$O install $L --build $X/build3 --root $X/root >/dev/null
echo installed
