#!/bin/bash
# XD-26: regenerate L4, fmt, validate against assets_dev (agent:xeen-a7-xd26)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd26/L4; X=$R/output/studio_cal/xd26
cd $R && python3 level_generation/projects/xeen/xd26/gen.py && $O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev 2>&1
