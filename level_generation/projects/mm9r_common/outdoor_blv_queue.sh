#!/bin/bash
# Builds outdoor-BLV region projects one after another into the shared review root (they share its tables, so never in
# parallel): outdoor_blv_queue.sh thronheim drangheim ...  Logs: <project>/work/convert.log; summary on stdout.
cd "$(dirname "$0")/../../.."
for stem in "$@"; do
  p=level_generation/projects/mm9r_${stem}_blv
  mkdir -p $p/work
  start=$(date +%s)
  python3 $p/convert.py > $p/work/convert.log 2>&1
  code=$?
  echo "$stem exit=$code $(( $(date +%s) - start ))s: $(grep -o 'sectors=[0-9]* vertices=[0-9]* faces=[0-9]* doors=[0-9]*' $p/work/convert.log | tail -1) | $(tail -1 $p/work/convert.log | cut -c1-160)"
done
echo QUEUE_DONE
