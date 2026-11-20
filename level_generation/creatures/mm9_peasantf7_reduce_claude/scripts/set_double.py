#!/usr/bin/env python3
"""doubleSided flags of the materials: `off` clears them (tools/build_actor_lods.py merges shadow geometry only across equal face
culling; the creature's chain built the LODs before double_head.py), `restore` copies them back by material name from the installed
GLB (before/mm9_peasantf7.glb). Usage: set_double.py <in.glb> <out.glb> off|restore"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
src, dst, mode = sys.argv[1:4]
doc, b = glbio.read_glb(Path(src))
ref = {m['name']: m.get('doubleSided', False) for m in glbio.read_glb(HERE / 'before' / 'mm9_peasantf7.glb')[0]['materials']}
for m in doc['materials']:
    if mode == 'off':
        m.pop('doubleSided', None)
    elif ref.get(m['name']):
        m['doubleSided'] = True
glbio.write_glb(Path(dst), doc, b)
print('DOUBLE', mode, [m['name'] for m in doc['materials'] if m.get('doubleSided')])
