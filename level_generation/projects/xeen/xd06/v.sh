#!/bin/bash
# regenerate, fmt, validate (Xeen world: build-xeen's oymap reads the world's rows from assets_dev since merge point 3)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd06/L4; X=$R/output/studio_cal/xd06
cd $R && python3 level_generation/projects/xeen/xd06/gen.py >/dev/null && $O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev 2>&1
