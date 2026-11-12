#!/usr/bin/env bash
# Install the chosen step of each listed model from a repair run: export/<stem>.glb, winding check, install_model.py.
# Usage: install_batch.sh <run name> <list file>   -> work/<run>/install.log (one INSTALLED/FAILED line per model)
set -uo pipefail
here=$(cd "$(dirname "$0")" && pwd); project=$(dirname "$here"); root=$(cd "$project/../../.." && pwd)
run=$1; list=$2; log="$project/work/$run/install.log"; : > "$log"
while read -r stem; do
  [ -z "$stem" ] && continue
  read -r step world < <(python3 -I -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['chosen'], r['world'])" \
    "$project/work/$run/$stem/result.json")
  cp "$project/work/$run/$stem/$step.glb" "$project/export/$stem.glb"
  winding=$(python3 "$root/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" "$project/export/$stem.glb" | tail -1)
  case "$winding" in *": 0") ;; *) echo "FAILED $stem winding: $winding" >> "$log"; continue ;; esac
  if (cd "$root" && python3 tools/install_model.py "$project/export/$stem.glb" --world "$world") >> "$log.detail" 2>&1; then
    echo "INSTALLED $stem $world $step" >> "$log"
  else
    echo "FAILED $stem install" >> "$log"
  fi
done < "$list"
echo DONE >> "$log"
