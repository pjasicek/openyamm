#!/usr/bin/env python3
"""Runtime material settings of the fish GLB: both materials specular 0 / metallic 0 (CLAUDE_CREATURE_TEXTURES.md);
the fin material renamed FishFin, alphaMode MASK at 0.5 (MM9 FISH.dtx is drawn with its alpha: MONSTERS.txt
Transparent 1; Blender exports the clip material as BLEND) and no edge darkening (flat leaves have no silhouette).
Usage: set_extras.py in.glb out.glb [--opaque-fins]   (opaque before build_actor_lods.py, which merges shadow
geometry only from opaque materials; MASK after strip_shadow_fins.py)"""
import json, struct, sys
from pathlib import Path
src, dst = sys.argv[1:3]
opaque = '--opaque-fins' in sys.argv
raw = Path(src).read_bytes()
n = struct.unpack_from('<I', raw, 12)[0]
doc = json.loads(raw[20:20 + n]); rest = raw[20 + n:]
for mat in doc['materials']:
    mat.setdefault('pbrMetallicRoughness', {})['metallicFactor'] = 0
    mat.setdefault('extras', {})['openyamm_specular'] = 0
    if mat['name'].startswith('FishFin'):
        mat['name'] = 'FishFin'
        mat['pbrMetallicRoughness']['roughnessFactor'] = 0.92   # flat leaves: no sheen when one faces the light
        if opaque:
            mat['alphaMode'] = 'OPAQUE'; mat.pop('alphaCutoff', None)
        else:
            mat['alphaMode'] = 'MASK'; mat['alphaCutoff'] = 0.5
        mat['extras']['openyamm_edge_darkening'] = 0
js = json.dumps(doc, separators=(',', ':')).encode(); js += b' ' * (-len(js) % 4)
out = bytearray(raw[:12]) + struct.pack('<II', len(js), 0x4E4F534A) + js + rest
struct.pack_into('<I', out, 8, len(out))
Path(dst).write_bytes(out)
print('EXTRAS', [(m['name'], m.get('alphaMode', 'OPAQUE')) for m in doc['materials']])
