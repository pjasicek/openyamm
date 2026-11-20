#!/usr/bin/env python3
"""Finish one dungeon decoration: work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode,
double-sided, unlit, emissive) -> tools/link_static_model_lods.py -> validation (LOD chain, triangle budgets, COLOR_0
on every primitive, base on the ground) -> work/<output>.glb, installed (0664) with --install.
Usage: finish.py <prop> [--install]"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
FINISH = {
    # Thousands of wall torches per world: a few hundred triangles.
    'torch': {'output': 'mm6_deco_torch.glb', 'budget': [500, 300, 160],
              'materials': {'Flame': FLAME, 'Embers': {'unlit': True}}},
    'torchnf': {'output': 'mm6_deco_torch_unlit.glb', 'budget': [500, 300, 160], 'materials': {}},
    # Torches standing away from any wall (free_model): the ring clamp without arm and plate.
    'torch_free': {'output': 'mm6_deco_torch_free.glb', 'budget': [500, 300, 160],
                   'materials': {'Flame': FLAME, 'Embers': {'unlit': True}}},
    'torchnf_free': {'output': 'mm6_deco_torch_unlit_free.glb', 'budget': [500, 300, 160], 'materials': {}},
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
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
