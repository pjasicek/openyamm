#!/bin/bash
# regenerate, fmt, validate
OYR="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"   # the repository root
R=$OYR; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd05/L4
cd $R && python3 output/studio_cal/xd05/tools/gen.py >/dev/null && $O fmt $L >/dev/null && $O validate $L --assets assets_dev 2>&1
