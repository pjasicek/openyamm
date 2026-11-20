#!/bin/bash
# Runs every prepared head job that has no raw.png yet, four at a time.
cd /home/pjasicek/github/OpenYAMM || exit 1
ls -d level_generation/ui/hud_inventory/mm9_pc_dolls/pc*/ | while read d; do
  [ -f "$d/raw.png" ] || echo "${d}run.sh"
done | xargs -P 4 -I{} bash -c '{} > /dev/null 2>&1; echo "finished {} $([ -f $(dirname {})/raw.png ] && echo ok || echo FAILED)"'
