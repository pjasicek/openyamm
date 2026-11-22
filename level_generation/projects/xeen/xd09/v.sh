#!/bin/bash
# regenerate, fmt, validate (Xeen world: build-xeen's oymap reads the world's rows from assets_dev)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../.." && pwd)"; O=$R/openyamm-studio/build-xeen/oymap; L=$R/devdocs/xeen/briefs/xd09/L4; X=$R/output/studio_cal/xd09
cd $R && python3 level_generation/projects/xeen/xd09/gen.py >/dev/null && for l in L1 L2 L3 L4; do $O fmt $R/devdocs/xeen/briefs/xd09/$l >/dev/null; done; $O validate $L --assets $R/assets_dev 2>&1 | tail -15
