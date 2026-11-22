#!/bin/bash
# XD-25: regenerate L4, fmt, validate against assets_dev (agent:xeen-a7-xd25)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd25/L4; X=$R/output/studio_cal/xd25
cd $R && python3 level_generation/projects/xeen/xd25/gen.py && $O fmt $L >/dev/null; $O validate $L --assets $R/assets_dev 2>&1
