#!/usr/bin/env bash
# MM9 dragonfly runtime GLB: export -> prepare -> LODs -> shadow fix -> A/B/C skins (region ramps) -> floor pass
# (flier hover, corpse grounding) -> winding check. Usage: TOK=<lease token> scripts/build_runtime.sh [--install]
# The export step (build_export.py) and compose run before this; see README.md "Rebuild".
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
python3 "$repo/tools/prepare_actor_glb.py" export/mm9_dfly_lod0.glb export/mm9_dfly_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/mm9_dfly_runtime_lod0.glb" \
  "$here/export/mm9_dfly_lods.glb" --mesh-node Dfly 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm9_dfly_lods.glb export/mm9_dfly_lods_shadowfix.glb
python3 ../claude_shared/region_variants.py export/mm9_dfly_lods_shadowfix.glb export/mm9_dfly_skins.glb \
  textures/dfly_ramps.json --extra Dfly openyamm_specular=0 --extra Dfly pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, flier rule): the lowest point over the living clips meets the floor; the
# death eases the lift out and the corpse is grounded. HOVER = -(lowest living point), from scripts/clip_heights.py.
HOVER="${HOVER:-$(python3 scripts/clip_heights.py export/mm9_dfly_skins.glb | python3 -c '
import sys
low = min(float(l.split()[4]) for l in sys.stdin if l.split()[0] not in ("Death", "Dead"))
print(f"{-low:.6f}")')}"
echo "hover $HOVER"
F=../claude_shared/floor/floor_fix.py
python3 $F export/mm9_dfly_skins.glb export/mm9_dfly_hover.glb --hover "$HOVER" Death Dead
python3 $F export/mm9_dfly_hover.glb export/mm9_dfly.glb --ground-death Death Dead
rm -f export/mm9_dfly_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/mm9_dfly.glb | tail -1
python3 scripts/clip_heights.py export/mm9_dfly.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/mm9_dfly.glb --world mm9
fi
ls -la export/mm9_dfly.glb
