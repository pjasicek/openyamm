#!/bin/bash
# Regenerate the shell and the objects from the scratch generators (first pass only), fmt, validate.
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../../.." && pwd)"
L=$R/devdocs/xeen/briefs/xd03/L4
T=$R/output/studio_cal/xd03/tools
cd $T && python3 gen_rooms.py $L && python3 gen_objects.py $L && cd $R && openyamm-studio/build/oymap fmt $L >/dev/null && openyamm-studio/build/oymap validate $L --assets assets_dev
