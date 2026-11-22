#!/bin/bash
# Regenerate rooms, objects and wiring from the scratch generators (first pass only), fmt, validate.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
L=$R/devdocs/xeen/briefs/xd04/L4
T=$R/output/studio_cal/xd04/tools
cd $R && python3 $T/gen_rooms.py $R/devdocs/xeen/briefs/xd04/L3/rooms.yml $L && python3 $T/gen_objects.py $L && python3 $T/gen_wiring.py $L && openyamm-studio/build/oymap fmt $L >/dev/null && openyamm-studio/build/oymap validate $L --assets assets_dev
