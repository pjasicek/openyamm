#!/usr/bin/env python3
"""Finish one model of the hanging batch (a copy of ../../scripts/finish.py with this batch's FINISH table):
work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode, double-sided, unlit, emissive) ->
tools/link_static_model_lods.py -> validation (LOD chain, triangle budgets, COLOR_0 on every primitive, base on the
ground) -> work/<output>.glb, installed (0664) with --install, which refuses to
overwrite an existing installed model.
Usage: finish.py <prop> [--install [--reinstall]]  (--reinstall: replace this batch's own installed model; install
writes a new file, so hard links elsewhere keep the old bytes)"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
FINISH = {
    # Tens of placements (or fewer): up to 4000 triangles, chains of four levels down to about 200.
    # The Meshy prisoner (bones batch) costs 2400 / 1000 / 360 / 150 (hanging) and 2600 / 1000 / 360 / 150 (sitting).
    'hngncge2': {'output': 'mm6_deco_hngncge2.glb', 'budget': [5000, 2600, 700, 280], 'materials': {}},
    'empty': {'output': 'mm6_deco_empty.glb', 'budget': [4000, 2000, 500, 200], 'materials': {}},
    'bonecage': {'output': 'mm6_deco_bonecage.glb', 'budget': [4300, 2200, 650, 280], 'materials': {}},
    # One placement each (per-map bindings), with a long chain: one-off budget.
    'hngncge2_long': {'output': 'mm6_deco_hngncge2_long.glb', 'budget': [7500, 3800, 700, 280], 'materials': {}},
    'empty_long': {'output': 'mm6_deco_empty_long.glb', 'budget': [6000, 3000, 600, 250], 'materials': {}},
    # Three placements: the candle flames are crossed flipbook cards (blended, double-sided, unlit).
    'chndlir0': {'output': 'mm6_deco_chndlir0.glb', 'budget': [4000, 2000, 400], 'materials': {'Flame': FLAME}},
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
        if destination.exists() and '--reinstall' not in sys.argv:
            sys.exit(f'{destination} exists: installed models are never overwritten (--reinstall replaces it)')
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
