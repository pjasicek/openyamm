#!/usr/bin/env python3
"""Review-viewer GLBs: each tier's materials made the primary in a copy of the delivered GLB. Writes review/viewer/dook_a.glb, _b, _c."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
GLB = HERE / 'export' / 'mm9_dookmilitia.glb'
for k, t in enumerate('abc'):
    doc, binary = RV.read_glb(GLB)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if k in mp['variants']: prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'): prim.pop('extensions', None)
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.3 if m_['name'].startswith('DookWeapon') else 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary))
    RV.write_glb(HERE / 'review' / 'viewer' / f'dook_{t}.glb', d2, b2)
print('VIEWER done')
