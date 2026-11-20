#!/usr/bin/env bash
# Texture chain of the retextured 45 % peasant (after uv_r45.py, knife_fix.py, bake_ao_r45.py and the Meshy returns).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; cd "$P"
blender -b -P scripts/dump_uv3d_r45.py 2>&1 | grep DUMPED
python3 scripts/compose_r45.py 2>&1 | grep '^{'
python3 scripts/tier_ramps_r45.py | cut -c1-140
python3 ../claude_shared/compose_head_set.py "$P" pfem work/r45_master.blend Peasant "$P/textures_r45/pfem_a_basecolor.png" \
  --textures textures_r45 --local 0 --contrast 1.0 --saturation 1.0 --fine 1.0 | tail -1
(cd scripts && python3 compose_head_r45.py 2>&1 | grep '^{')
# compose_head_r45.py moved the body skin halfway toward the head: refresh the runtime 1K body base colour
python3 -c "from PIL import Image; Image.open('textures_r45/pfem_a_basecolor.png').resize((1024, 1024), Image.LANCZOS).save('textures_r45/pfem_a_basecolor_1k.png', optimize=True)"
