#!/bin/bash
# Run scripts/st_probe.py jobs from probe_queue.py (stdin lines "probe <label> <glb> <clip> <f30> <view>") under the Blender lock.
# Usage (project folder): python3 scripts/probe_queue.py ... | scripts/run_probes.sh  -> work/probe/<label>_<clip>_<f30>_<view>.json
cd "$(dirname "$0")/.."; P=$PWD; R=/home/pjasicek/github/OpenYAMM; T=$(cat LEASE_TOKEN.txt); rel=${P#$R/}
while read -r _ lab glb clip f view _rest; do
  out=$P/work/probe/${lab}_${clip}_${f}_${view}.json
  [[ -f $out ]] && continue
  (cd $R && flock /home/pjasicek/github/OpenYAMM/level_generation/creatures/mm9_tryggva_reduce_claude/work/blender.lock \
    systemd-run --user --scope -q -p MemoryMax=12G -p MemorySwapMax=0 tools/run_creature_blender.sh --token $T \
    $rel/scripts/st_probe.py $P/$glb $out clip=$clip f30=$f view=$view > ${out%.json}.log 2>&1)
  echo PROBED $lab $clip $f $view $(python3 -c "import json; print(json.load(open('$out'))['holes'])" 2>/dev/null)
done
echo PROBES_DONE
