#!/bin/bash
# Lane A8 lights audit (merge point 14): after a map's install, bake it and run its playtests 4 of 4 from assets_dev.
# Run as: flock output/studio_cal/a8_s5/lights/post.lock a8_lights_post.sh <key>   (one bake and one game at a time)
R="$(cd "$(dirname "$(readlink -f "$0")")/../../../../.." && pwd)"; C=$R/output/studio_cal; k=$1; cd $R
P=tools/lighting/baked_indoors/profiles/xeen_$k.yml
[ -f $P ] || sed "s/xeen_xd08.blv/xeen_$k.blv/" tools/lighting/baked_indoors/profiles/xeen_xd08.yml > $P
# wait for another A8 bake (blender with a8_bake in its arguments), by its exact pid
while true; do
  B=$(ps -eo pid=,comm=,args= | awk '$2 == "blender" && /a8_bake/ {print $1}' | head -1)
  [ -z "$B" ] && break
  echo "waiting for A8 bake pid $B"; while kill -0 $B 2>/dev/null; do sleep 10; done
done
if [ "${NOBAKE:-0}" != 1 ]; then
echo "== bake $k $(date +%T)"
$R/level_generation/projects/xeen/common/bake/a8_bake.sh $k $R/assets_dev 2>&1 | grep -E "installed|Error|error|Traceback" | tail -5
fi
python3 tools/lighting/stale_bakes.py --check 2>&1 | grep -E "xeen_(xd06|xd09|xd10|xd11|xd12|xd21|xd27|dd01|dd02|dd03|dd04|dd09|dd10a|dd10b|dd18|dd05|dd12|dd14|dd19|dd20|dd15|dd17|dd08|dd10c|dd21|dd25|dd22|dd26|fd01)" || echo "stale: none of the lane's maps"
echo "== tests $k $(date +%T)"
export ASSETS=$R/assets_dev
case $k in
  xd06|xd21) $R/level_generation/projects/xeen/$k/world_four.sh ;;
  xd09) $R/level_generation/projects/xeen/$k/four.sh 4 ;;
  xd12|xd27) $R/level_generation/projects/xeen/$k/xfour.sh ;;
  *) $R/level_generation/projects/xeen/$k/four.sh ;;
esac
echo "== done $k $(date +%T)"
