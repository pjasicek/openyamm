#!/bin/bash
# The 2026-10-31 rebuild of one MM9 dungeon after the converter's invisible-bottoms / Firethrough fix
# (DUNGEON_PLAYBOOK.md "Package change: invisible brush bottoms and the Firethrough helper"): convert.py from the current
# converter, its scenarios, stair probes; its now stale baked lighting is copied to work/lighting_stale_20261031/ and
# removed from the review root (user decision 2026-10-31: classic lighting until the end-of-integration lighting pass).
# Usage: rebuild_map.sh <stem> [probe]      log: level_generation/projects/mm9r_common/rebuild_1031/<stem>.log
stem=$1
cd /home/pjasicek/github/OpenYAMM || exit 1
P=level_generation/projects/mm9r_$stem
L=level_generation/projects/mm9r_common/rebuild_1031/$stem.log
A="$PWD/output/mm9_rework/assets_dev"
{
echo "== $stem rebuild start $(date '+%Y-%m-%d %H:%M:%S')"
python3 $P/convert.py > $P/work/convert_1031.log 2>&1; rc=$?
echo "convert exit $rc end $(date '+%H:%M:%S')"
grep -m1 '^wrote' $P/work/convert_1031.log
python3 -c "import json;print('invisible bottoms dropped', len(json.load(open('$P/work/invisible_bottoms.json'))))"
if [ $rc -ne 0 ]; then tail -20 $P/work/convert_1031.log; echo "FAILED convert"; exit 1; fi
if [ -f $P/make_scenarios.py ]; then python3 $P/make_scenarios.py > $P/work/make_scenarios_1031.log 2>&1; echo "make_scenarios exit $?"; fi
for s in $P/scenario_*.yml; do
  case $s in *stair_probes*) continue;; esac
  ./build/game/openyamm --asset-root "$A" --headless-run-scenario $s --scenario-no-color > $P/work/scn_1031_$(basename $s .yml).log 2>&1
  echo "scenario $(basename $s) exit $? $(grep -c 'ASSERT fail' $P/work/scn_1031_$(basename $s .yml).log) failed asserts; $(grep -m1 -o 'Scenario [a-z]*' $P/work/scn_1031_$(basename $s .yml).log)"
done
if [ "$2" = probe ]; then python3 level_generation/projects/mm9r_common/stair_probes.py $stem > $P/work/stair_probes_1031.log 2>&1; echo "stair probes exit $?"; cat $P/work/stair_probes_1031.log; fi
python3 level_generation/projects/mm9r_common/rebuild_1031/remove_stale_lighting.py $stem
echo "== $stem done $(date '+%H:%M:%S')"
} > $L 2>&1
