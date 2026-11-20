#!/usr/bin/env python3
"""A GLB showing one KHR_materials_variants tier: every primitive takes that variant's material, the variants extension is
dropped (three.js review viewer, Blender renders). Only for tiers without ramps (phom2_a: its own maps); the ramp tiers'
viewer GLBs come from ../mm9_peasanthom1_claude/v2/scripts/viewer_tiers.py (approved, copied unchanged).
Usage: variant_glb.py <in glb> <out glb> <variant>"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'claude_shared'))
import region_variants as RV
src, dst, variant = sys.argv[1:4]
doc, blob = RV.read_glb(src)
names = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
vi = names.index(variant)
for mesh in doc['meshes']:
    for p in mesh['primitives']:
        m = p.get('extensions', {}).pop('KHR_materials_variants', None)
        if m:
            p['material'] = next(x['material'] for x in m['mappings'] if vi in x['variants'])
        if 'extensions' in p and not p['extensions']:
            del p['extensions']
doc['extensions'].pop('KHR_materials_variants')
doc['extensionsUsed'] = [e for e in doc.get('extensionsUsed', []) if e != 'KHR_materials_variants']
RV.write_glb(dst, doc, blob)
print('VARIANT_GLB', dst, variant)
