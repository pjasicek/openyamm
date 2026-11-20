#!/usr/bin/env python3
"""Final runtime step for the single-material Treant (no tiers: descriptors 451-453 share palette 530, so no
KHR_materials_variants and no region ramps): set the same material extras the region_variants.py step sets on tiered
creatures. Usage: set_extras.py in.glb out.glb PREFIX KEY=VALUE [KEY=VALUE ...]  (values JSON; pbr.<k> sets
pbrMetallicRoughness.<k>). Uses claude_shared/region_variants.py read_glb/write_glb only."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as R
src, dst, prefix, *pairs = sys.argv[1:]
doc, binary = R.read_glb(src)
mats = [m for m in doc['materials'] if m.get('name', '').startswith(prefix)]
assert mats, f'no material starts with {prefix}'
for m in mats:
    for kv in pairs:
        k, v = kv.split('=', 1); v = json.loads(v)
        if k.startswith('pbr.'):
            m.setdefault('pbrMetallicRoughness', {})[k[4:]] = v
        else:
            m.setdefault('extras', {})[k] = v
R.write_glb(dst, doc, binary)
print(dst, 'materials', [m['name'] for m in doc['materials']], 'extras', pairs)
