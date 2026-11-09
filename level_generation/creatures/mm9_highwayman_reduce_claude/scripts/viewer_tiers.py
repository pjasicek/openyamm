#!/usr/bin/env python3
"""Review-viewer GLBs (../mm9_highwayman_claude/scripts/viewer_tiers.py with the GLB and prefix as arguments): each tier's
materials made the primary in a copy. Usage: viewer_tiers.py <glb> <prefix> -> work/viewer_<prefix>_hw_{a,b,c}.glb"""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'claude_shared'))
import region_variants as RV
GLB, PREFIX = Path(sys.argv[1]), sys.argv[2]
for k, t in enumerate('abc'):
    doc, binary = RV.read_glb(GLB)
    for mesh in doc['meshes']:
        for prim in mesh['primitives']:
            for mp in prim.get('extensions', {}).get('KHR_materials_variants', {}).get('mappings', []):
                if k in mp['variants']: prim['material'] = mp['material']
            prim.get('extensions', {}).pop('KHR_materials_variants', None)
            if not prim.get('extensions'): prim.pop('extensions', None)
    for m_ in doc['materials']:
        m_.setdefault('extensions', {})['KHR_materials_specular'] = {'specularFactor': 0.3 if m_['name'].startswith('HwWeapon') else 0.0}
    doc.get('extensions', {}).pop('KHR_materials_variants', None)
    doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants'] + ['KHR_materials_specular']
    d2, b2 = RV._compact(doc, bytes(binary))
    RV.write_glb(HERE / 'work' / f'viewer_{PREFIX}_hw_{t}.glb', d2, b2)
print('VIEWER', PREFIX)
