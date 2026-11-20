#!/bin/bash
# regenerate, format, validate, build; prints the frontier
cd /home/pjasicek/github/OpenYAMM/output/studio_cal/mm6_cd2/tools
python3 gen.py || exit 1
python3 gen_objects.py || exit 1
cp ../objects_auto.yml ../../../../devdocs/map_studio/briefs/mm6_cd2/L4/objects.yml
cp ../wiring_auto.yml ../../../../devdocs/map_studio/briefs/mm6_cd2/L4/wiring.yml
cd /home/pjasicek/github/OpenYAMM; L=devdocs/map_studio/briefs/mm6_cd2/L4; O=$PWD/openyamm-studio/build/oymap; A=$PWD/assets_dev; D=output/studio_cal/mm6_cd2
$O fmt $L >/dev/null; $O validate $L --assets $A 2>&1 | cut -c1-300 | head -${1:-25}
$O build $L --assets $A 2>&1 | tail -3 | cut -c1-300
$O install $L --mount $D/mount --assets $A 2>&1 | tail -1
