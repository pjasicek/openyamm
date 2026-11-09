#!/usr/bin/env bash
# Retextured 45 % peasant -> export/mm6_pfem_retex.glb and the viewer tiers (review/viewer/mm6_pfem_*_r45t.glb).
# Texture inputs: compose_r45.py, tier_ramps_r45.py, compose_head_set.py, compose_head_r45.py (see README).
set -euo pipefail
P="$(cd "$(dirname "$0")/.." && pwd)"; R="$(cd "$P/../../.." && pwd)"; cd "$P"
python3 - <<'PY'
from PIL import Image
for n in ['pfem_normal','pfem_metal_rough']:
    Image.open(f'textures_r45/{n}.png').resize((1024,1024),Image.LANCZOS).save(f'textures_r45/{n}_1k.png',optimize=True)
PY
blender --background work/r45_master.blend --python scripts/export_glb_r45.py 2>&1 | grep -c EXPORTED >/dev/null
python3 "$R/tools/prepare_actor_glb.py" export/mm6_pfem_lod0.glb export/mm6_pfem_runtime_lod0.glb >/dev/null
blender --background --factory-startup --python-exit-code 1 --python "$R/tools/build_actor_lods.py" -- \
  export/mm6_pfem_runtime_lod0.glb export/mm6_pfem_lods.glb --mesh-node Peasant 2>&1 | grep "LOD triangles"
python3 scripts/shrink_shadow_lods.py export/mm6_pfem_lods.glb export/mm6_pfem_lods_shadowfix.glb >/dev/null
python3 ../claude_shared/region_variants.py export/mm6_pfem_lods_shadowfix.glb export/mm6_pfem_retex.glb \
  textures_r45/pfem_ramps.json --extra Peasant openyamm_specular=0 --extra Peasant pbr.metallicFactor=0 | tail -1
python3 "$R/tools/merge_head_material.py" export/mm6_pfem_retex.glb export/mm6_pfem_retex.glb | tail -1
python3 scripts/viewer_variants.py export/mm6_pfem_retex.glb r45t | tail -1
python3 - <<'PY'
import json, hashlib
m = json.load(open('review/viewer/manifest.json'))
for x in m['models']:
    if x['id'].endswith('_r45t'):
        f = x['url'].split('?')[0]; h = hashlib.sha256(open('review/viewer/' + f, 'rb').read()).hexdigest()
        x.update(url=f'{f}?v={h[:12]}', sha256=h)
json.dump(m, open('review/viewer/manifest.json', 'w'), indent=1)
PY
