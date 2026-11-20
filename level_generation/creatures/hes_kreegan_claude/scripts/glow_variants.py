#!/usr/bin/env python3
"""hkr: per-tier emissive colour for the glow materials (HKR_Glow on the plates, Rifle_Glow on the carbine): one copy
per variant with its own emissiveFactor / baseColorFactor, every primitive of the material mapped through
KHR_materials_variants (the variant list already set by region_variants.py). Tiers A and B glow orange, C (Spire
Guard) white-gold (concept fam_troopers.png). Usage: glow_variants.py in.glb out.glb"""
import copy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from merge_head_material import read_glb, write_glb, compact  # noqa
GLOW = {'hkr_a': (1.0, 0.42, 0.08), 'hkr_b': (1.0, 0.36, 0.06), 'hkr_c': (1.0, 0.86, 0.55)}
doc, binary = read_glb(Path(sys.argv[1]))
variants = [v['name'] for v in doc['extensions']['KHR_materials_variants']['variants']]
done = 0
for base_name in ('HKR_Glow', 'Rifle_Glow'):
    bases = [i for i, m in enumerate(doc['materials']) if m.get('name', '') == base_name or m.get('name', '').startswith(base_name + '.')]
    for b in bases:
        copies = []
        for v in variants:
            m = copy.deepcopy(doc['materials'][b]); m['name'] = f"{base_name}_{v.split('_')[-1].upper()}"
            c = GLOW[v]; m['emissiveFactor'] = list(c)
            m.setdefault('pbrMetallicRoughness', {})['baseColorFactor'] = [*c, 1.0]
            m['pbrMetallicRoughness']['metallicFactor'] = 0.0
            doc['materials'].append(m); copies.append(len(doc['materials']) - 1)
        for mesh in doc['meshes']:
            for p in mesh['primitives']:
                if p.get('material') == b:
                    p['material'] = copies[0]
                    p.setdefault('extensions', {})['KHR_materials_variants'] = {'mappings': [{'material': copies[i], 'variants': [i]} for i in range(len(variants))]}
                    done += 1
write_glb(Path(sys.argv[2]), *compact(doc, binary))
print('GLOWVARIANTS primitives mapped', done)
