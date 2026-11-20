#!/usr/bin/env python3
"""Finish one statuette pedestal (after ../../props/scripts/finish.py): work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode, double-sided, unlit,
emissive, extras) -> tools/link_static_model_lods.py -> validation (LOD chain, triangle budgets, COLOR_0 on every
primitive, base on the ground) -> work/<output>.glb, installed (0664) with --install.
Usage: finish.py <prop> [--install]"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link

# The five statuettes: the ped06 pedestal (1764 / 676 / 276) plus a gold figure of 1400 / 600 / 220 triangles.
FINISH = {animal: {'output': f'mm6_deco_pedestal_{animal}.glb', 'budget': [3300, 1350, 520], 'materials': {}}
          for animal in ('bear', 'tiger', 'eagle', 'wolf', 'dragon')}


def main():
    prop = sys.argv[1]
    spec = FINISH[prop]
    document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
    for material in document['materials']:
        settings = spec['materials'].get(material['name'], {})
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
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
        if settings.get('extras'):
            material.setdefault('extras', {}).update(settings['extras'])
    report = link.link(document)
    out = HERE / 'work' / spec['output']
    link.write_glb(out, document, binary)
    # validation on the written file
    document, _ = link.read_glb(out)
    problems = []
    base = [n for n in document['nodes'] if 'mesh' in n]
    if len(base) != 1:
        problems.append(f'{len(base)} mesh nodes')
    mesh = document['meshes'][base[0]['mesh']]
    chain = [base[0]['mesh']] + mesh.get('extras', {}).get('openyamm_lods', [])
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
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    size = os.path.getsize(out)
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', size, problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / spec['output']
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
