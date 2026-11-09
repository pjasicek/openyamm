#!/usr/bin/env python3
"""Material fixes after the Blender export, in place: Glow* and Thrust* materials unlit (KHR_materials_unlit),
Thrust* alpha BLEND and double-sided. Usage: fix_materials.py in.glb out.glb"""
import sys
from glb_io import read_glb, write_glb
doc, b = read_glb(sys.argv[1])
used = set(doc.get('extensionsUsed', []))
for m in doc['materials']:
    if m['name'].startswith(('Glow', 'Thrust')):
        m.setdefault('extensions', {})['KHR_materials_unlit'] = {}; used.add('KHR_materials_unlit')
        m.pop('normalTexture', None)
    if m['name'].startswith('Thrust'):
        m['alphaMode'] = 'BLEND'; m['doubleSided'] = True
doc['extensionsUsed'] = sorted(used)
write_glb(sys.argv[2], doc, b)
print('FIXED', [(m['name'], m.get('alphaMode', 'OPAQUE'), 'unlit' if 'extensions' in m else '') for m in doc['materials']])
