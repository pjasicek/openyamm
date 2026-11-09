#!/usr/bin/env bash
# Quality pass reduction of one summer tree and its leafy twins (autumn, fruit): leaf cards thinned (thin_cards.py),
# bark collapsed (copies of the mm6_reduce_pilot scripts: deco_dump, deco_ladder pick, deco_build, deco_swap_glb),
# LOD0 bottom pinned (pin_bounds.py). Twins drop the same cards and take the summer's reduced bark.
# Output work/reduce/mm7_deco_<id>.glb, work/<id>/model.json. Usage: reduce_family.sh <summer> <fraction> [twin ...]
#   a twin written fruit:<id> keeps its Fruit material (tree38).
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"; cd "$here/scripts"
venv=${MESH_VENV:-/tmp/claude-1000/-home-pjasicek-github-OpenYAMM/53a68caf-2dc9-4fcd-9e2a-654e43d315c9/scratchpad/meshvenv/bin/python}
s="$1"; f="$2"; shift 2
R=../work/reduce
python3 thin_cards.py "$s" "$f"
/snap/bin/blender -b -P deco_dump.py -- "$s=$R/${s}_thin.glb" 2>&1 | grep -E "DUMP|Error|Traceback"
"$venv" deco_ladder.py "$s"
pick=$(python3 -c "import json; print(json.load(open('$R/ladder_$s.json'))['pick'] or '')")
[[ -n "$pick" ]] || { echo "no passing step for $s"; exit 1; }
/snap/bin/blender -b -P deco_build.py -- "$s:$pick:$R/${s}_thin.glb" 2>&1 | grep -E "BUILT|Error|Traceback"
python3 deco_swap_glb.py "$R/${s}_thin.glb" "$R/${s}_lod0.glb" "$R/mm7_deco_$s.glb"
python3 pin_bounds.py "$s"
for t in "$@"; do
  keep=()
  if [[ "$t" == fruit:* ]]; then t="${t#fruit:}"; keep=(Fruit); fi
  python3 thin_cards.py "$t" --like "$s"
  python3 deco_swap_glb.py "$R/${t}_thin.glb" "$R/${s}_lod0.glb" "$R/mm7_deco_$t.glb" "${keep[@]}"
  python3 pin_bounds.py "$t"
done
for id in "$s" "$@"; do python3 ../../../mm8_3d/animated/scripts/check_winding.py "$R/mm7_deco_${id#fruit:}.glb" | grep WINDING; done
