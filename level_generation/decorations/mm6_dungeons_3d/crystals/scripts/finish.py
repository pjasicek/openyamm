#!/usr/bin/env python3
"""Finish one model of the crystal batch (copy of ../../scripts/finish.py with this batch's FINISH table):
work/<prop>_export.glb -> material settings (alpha mode, double-sided, unlit, emissive) -> tools/link_static_model_lods.py
-> validation (LOD chain, triangle budgets, COLOR_0 on every primitive, base on the ground, pulse extras on emissive
materials) -> work/<output>.glb, installed (0664, new names only) with --install.
Usage: finish.py <prop> [--install]"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]

# Pink inner glow of crystl0 (saturated, the hue of its native mean (133, 75, 96)); its level lifts the darkest facets
# to about the sprite's dark wine red (49, 32, 31), so the bases stay dark while the crystal glows.
CRYSTAL_GLOW = [0.06, 0.016, 0.03]
# Lavender glow of the Memory Crystal ball: its brightest texels (160, 150, 182), a small share of its mean.
MEMBALL_GLOW = [0.024, 0.02, 0.032]
TENS = [3000, 1200, 400]
FINISH = {
    'crystl0': {'output': 'mm6_deco_crystl0.glb', 'budget': TENS,
                'materials': {'Crystal': {'emissive': CRYSTAL_GLOW}}},
    'mcryst01': {'output': 'mm6_deco_mcryst01.glb', 'budget': TENS,
                 'materials': {'Ball': {'alpha': 'MASK', 'cutoff': 0.5, 'emissive': MEMBALL_GLOW}}},
    'crclstr': {'output': 'mm6_deco_crclstr.glb', 'budget': TENS, 'materials': {}},
    'crys6': {'output': 'mm6_deco_crys6.glb', 'budget': TENS, 'materials': {}},
    'crys5': {'output': 'mm6_deco_crys5.glb', 'budget': TENS, 'materials': {}},
    'stlmite1': {'output': 'mm6_deco_stlmite1.glb', 'budget': TENS, 'materials': {}},
    'stlmite2': {'output': 'mm6_deco_stlmite2.glb', 'budget': TENS, 'materials': {}},
    'stlmite3': {'output': 'mm6_deco_stlmite3.glb', 'budget': TENS, 'materials': {}},
    'corinth': {'output': 'mm6_deco_corinth.glb', 'budget': TENS,
                'materials': {'Leaves': {'double': True}}},
}


def main():
    sys.path.insert(0, str(REPO / 'tools'))
    import link_static_model_lods as link

    prop = sys.argv[1]
    spec = FINISH[prop]
    document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
    for material in document['materials']:
        settings = spec['materials'].get(material['name'], {})
        material.pop('alphaMode', None)
        material.pop('alphaCutoff', None)
        if settings.get('alpha'):
            material['alphaMode'] = settings['alpha']
            if settings['alpha'] == 'MASK':
                material['alphaCutoff'] = settings.get('cutoff', 0.5)
        material['doubleSided'] = settings.get('double', False)
        if settings.get('unlit'):
            material.setdefault('extensions', {})['KHR_materials_unlit'] = {}
            document.setdefault('extensionsUsed', [])
            if 'KHR_materials_unlit' not in document['extensionsUsed']:
                document['extensionsUsed'].append('KHR_materials_unlit')
        if settings.get('emissive'):
            material['emissiveFactor'] = settings['emissive']
    link.link(document)
    out = HERE / 'work' / spec['output']
    link.write_glb(out, document, binary)
    document, _ = link.read_glb(out)
    problems = []
    base = [node for node in document['nodes'] if 'mesh' in node]
    if len(base) != 1:
        problems.append(f'{len(base)} mesh nodes')
    chain = [base[0]['mesh']] + document['meshes'][base[0]['mesh']].get('extras', {}).get('openyamm_lods', [])
    triangles = [sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][i]['primitives'])
                 for i in chain]
    if len(chain) < 3:
        problems.append('LOD chain shorter than 3')
    for count, budget in zip(triangles, spec['budget']):
        if count > budget:
            problems.append(f'{count} triangles over {budget}')
    lowest = 1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            lowest = min(lowest, document['accessors'][primitive['attributes']['POSITION']]['min'][1])
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    for material in document['materials']:
        if 'emissiveFactor' in material and 'openyamm_pulse' not in material.get('extras', {}):
            problems.append(f'{material["name"]} glows without openyamm_pulse')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '',
                             m.get('emissiveFactor', ''), m.get('extras', {}))
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', os.path.getsize(out), problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / spec['output']
        if destination.exists() and destination.read_bytes() != out.read_bytes():
            # Never overwrite a GLB installed by someone else; only a rebuild of this batch's own file replaces it.
            if not (HERE / 'work' / f'.installed_{spec["output"]}').exists():
                sys.exit(f'{destination} exists and was not installed by this batch')
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        (HERE / 'work' / f'.installed_{spec["output"]}').touch()
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
