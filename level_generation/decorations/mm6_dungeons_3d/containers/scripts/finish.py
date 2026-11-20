#!/usr/bin/env python3
"""Finish one decoration of the containers batch (a copy of ../../scripts/finish.py with this batch's FINISH table;
it refuses to overwrite a GLB this batch did not install): work/<prop>_export.glb -> material settings from
FINISH[prop] (alpha mode, double-sided, unlit, emissive) -> tools/link_static_model_lods.py -> validation (LOD chain,
triangle budgets, COLOR_0 on every primitive, base on the ground) -> work/<output>.glb, installed (0664) with
--install. Usage: finish.py <prop> [--install]"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

SACK = [1500, 600, 250]
FINISH = {
    # Hundreds of sacks and bags per world: at most 1500 triangles.
    'bag_a': {'output': 'mm6_deco_bag_a.glb', 'budget': SACK, 'materials': {}},
    'bag01': {'output': 'mm6_deco_bag01.glb', 'budget': SACK, 'materials': {}},
    'floursac': {'output': 'mm6_deco_floursac.glb', 'budget': SACK, 'materials': {}},
    'bucket': {'output': 'mm6_deco_bucket.glb', 'budget': SACK, 'materials': {}},
    'trasheap': {'output': 'mm6_deco_trasheap.glb', 'budget': [4000, 1500, 450], 'materials': {}},
    'mushrm01': {'output': 'mm6_deco_mushrm01.glb', 'budget': SACK, 'materials': {}},
    'mushrm02': {'output': 'mm6_deco_mushrm02.glb', 'budget': SACK, 'materials': {}},
    'mushrm03': {'output': 'mm6_deco_mushrm03.glb', 'budget': SACK, 'materials': {}},
    'mushrm05': {'output': 'mm6_deco_mushrm05.glb', 'budget': SACK, 'materials': {}},
    'crysdisc': {'output': 'mm6_deco_crysdisc.glb', 'budget': [800, 400, 160], 'materials': {}},
}


def main():
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
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', os.path.getsize(out), problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / spec['output']
        # Never overwrite a GLB this batch did not install (outdoor bakes depend on installed bytes).
        ledger = HERE / 'work' / 'installed.txt'
        ours = ledger.read_text().split() if ledger.exists() else []
        if destination.exists() and spec['output'] not in ours:
            sys.exit(f'REFUSED {destination} exists and was not installed by this batch')
        if spec['output'] not in ours:
            with ledger.open('a') as stream:
                stream.write(spec['output'] + '\n')
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
