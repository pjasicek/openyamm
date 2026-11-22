#!/bin/bash
# regenerate, fmt, validate (Xeen world: build-xeen's oymap against assets_dev; since merge point 3 it reads the world's rows)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd21/L4; X=$R/output/studio_cal/xd21
cd $R && python3 level_generation/projects/xeen/xd21/gen.py >/dev/null && $O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev 2>&1
