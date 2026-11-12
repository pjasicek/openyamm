#!/usr/bin/env bash
# PartUV study: sequential Blender measurement queue (the creature wrapper serialises on the project lock).
# Usage: partuv_measure_queue.sh <lease token> <job file>; each job line: measure <in> <object> <out glb> [apply args...]
#        or export <in> <object> <out npz> [args...]. Lines run in order; texture_quality.py runs after each measure.
set -u
T=$1; JOBS=$2
REPO=/home/pjasicek/github/OpenYAMM
S=level_generation/creatures/uv_research_20261111/scripts
cd $REPO
while read -r kind src obj out rest; do
  [ -z "$kind" ] && continue
  case $kind in
    measure)
      tools/run_creature_blender.sh --token $T $S/partuv_apply_uv.py $src $obj $out - $rest > ${out%.glb}.wrap 2>&1 || { echo "FAIL $out"; continue; }
      python3 level_generation/creatures/claude_shared/texture_quality.py $out --by-bone --heatmap ${out%.glb} --json ${out%.glb}.json | head -n 1 ;;
    upload)
      tools/run_creature_blender.sh --token $T $S/partuv_apply_uv.py $src $obj $out $rest > ${out%.glb}.wrap 2>&1 || echo "FAIL $out"; echo "UPLOAD $rest" ;;
    export)
      tools/run_creature_blender.sh --token $T $S/partuv_export_mesh.py $src $obj $out $rest > ${out%.npz}.wrap 2>&1 || echo "FAIL $out"; echo "EXPORT $out" ;;
  esac
done < $JOBS
echo QUEUE_DONE
