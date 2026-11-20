#!/usr/bin/env bash
# MM9 Flying Icky runtime GLB (from mm9_dfly_claude / mm9_lobber_claude): prepare -> LODs -> shadow fix (wing leaves
# kept) -> material extras (one skin: no tier ramps) -> floor pass (flier hover, corpse grounding) -> winding check.
# Usage: scripts/build_runtime.sh [--install]. build_export.py and compose.py run before this; see README.md.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
repo="$(cd -- "$here/../../.." && pwd)"
cd "$here"
name=mm9_icky
python3 "$repo/tools/prepare_actor_glb.py" export/${name}_lod0.glb export/${name}_runtime_lod0.glb
/snap/bin/blender --background --factory-startup --disable-autoexec --threads 4 --python-exit-code 1 \
  --python "$repo/tools/build_actor_lods.py" -- "$here/export/${name}_runtime_lod0.glb" \
  "$here/export/${name}_lods.glb" --mesh-node Icky 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/${name}_lods.glb export/${name}_lods_shadowfix.glb Icky Icky_Wing
python3 scripts/material_extras.py export/${name}_lods_shadowfix.glb export/${name}_skins.glb Icky \
  openyamm_specular=0 pbr.metallicFactor=0
# Floor (claude_shared/floor/README.md, flier rule): the lowest point over the living clips meets the floor; the
# death eases the lift out and the corpse is grounded. HOVER = -(lowest living point), from scripts/clip_heights.py.
HOVER="${HOVER:-$(python3 scripts/clip_heights.py export/${name}_skins.glb | python3 -c '
import sys
low = min(float(l.split()[4]) for l in sys.stdin if l.split()[0] not in ("Death", "Dead"))
print(f"{-low:.6f}")')}"
echo "hover $HOVER"
F=../claude_shared/floor/floor_fix.py
python3 $F export/${name}_skins.glb export/${name}_hover.glb --hover "$HOVER" Death Dead
python3 $F export/${name}_hover.glb export/${name}.glb --ground-death Death Dead
rm -f export/${name}_lods.geometry.glb
python3 "$repo/level_generation/decorations/mm8_3d/animated/scripts/check_winding.py" export/${name}.glb | tail -1
python3 scripts/clip_heights.py export/${name}.glb
if [[ "${1:-}" == "--install" ]]; then
  python3 "$repo/tools/install_model.py" export/${name}.glb --world mm9
fi
ls -la export/${name}.glb
