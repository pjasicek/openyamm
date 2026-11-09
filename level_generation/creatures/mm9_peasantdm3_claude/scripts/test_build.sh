#!/usr/bin/env bash
# Geometry/rig test build with placeholder (DM1) textures: export -> clips -> hand rest -> mirror. Project folder.
# Usage: BLEND=work/x.blend scripts/test_build.sh <out name>
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"; repo="$(cd -- "$here/../../.." && pwd)"; cd "$here"
V=../claude_shared/gltf_venv/bin/python; rel="level_generation/creatures/$(basename "$here")"; out=$1
(cd "$repo" && bash $rel/scripts/bl.sh "EXPORTED|HEADFIX|Error|Trace" $rel/scripts/build_export_v2.py "$here/$BLEND" "$here/work/${out}_tex.glb" PeasantDM3 ${BODYP:-test} ${HEADC:-test} ${HEADP:-test}) | cut -c1-200
"$V" scripts/clips_mm9.py work/${out}_tex.glb work/${out}_clips.glb scripts/roles_pdm3.json work/${out}_clips.json 2>/dev/null | tail -2 | cut -c1-200
cur=work/${out}_clips.glb; k=0
while IFS= read -r line; do
  [[ -z "$line" || "$line" == \#* ]] && continue
  k=$((k + 1)); nxt=work/${out}_rest${k}.glb
  eval "python3 scripts/hand_rest.py $cur $nxt $line" | grep HANDREST | cut -c1-240
  cur=$nxt
done < scripts/hand_rest_pdm3.txt
$V scripts/mirror_glb.py $cur work/${out}.glb | tail -1
ls -la work/${out}.glb
