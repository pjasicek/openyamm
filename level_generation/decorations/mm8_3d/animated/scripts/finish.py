#!/usr/bin/env python3
"""Finish one model: work/<prop>_export.glb -> material settings from FINISH[prop] (alpha mode, double-sided,
unlit; review-only extras dropped) -> tools/link_static_model_lods.py -> validation (one mesh node, LOD chain of at
least three, triangle budgets, COLOR_0 on every primitive, base on the ground) -> work/<output>.glb; with --install
it runs tools/install_model.py <output> --engine --name <output> (source in assets_source/engine/models/, cooked
runtime copy in assets_dev/engine/models/). Usage: finish.py <prop> [--install]"""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402
sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_winding  # noqa: E402

from finish_table import FINISH  # noqa: E402

REVIEW_ONLY = ('openyamm_unlit_review',)


def main():
    prop = sys.argv[1]
    spec = FINISH[prop]
    document, binary = link.read_glb(HERE / 'work' / f'{prop}_export.glb')
    for material in document['materials']:
        # Per-card copies (Candle0, Candle1, ...) share their family's settings.
        settings = spec['materials'].get(material['name'],
                                         spec['materials'].get(re.sub(r'[0-9.]+$', '', material['name']), {}))
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
        for key in REVIEW_ONLY:
            material.get('extras', {}).pop(key, None)
        if 'extras' in material and not material['extras']:
            del material['extras']
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
    lowest, highest = 1e9, -1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            accessor = document['accessors'][primitive['attributes']['POSITION']]
            lowest = min(lowest, accessor['min'][1])
            highest = max(highest, accessor['max'][1])
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'height m',
          round(highest - lowest, 4), 'units', round((highest - lowest) * 81.7, 1), 'materials', materials,
          'bytes', os.path.getsize(out), problems)
    if check_winding.check(out):
        problems.append('inverted closed parts (outward normals required: the engine culls back faces)')
    if problems:
        print('INVALID', problems)
        sys.exit(1)
    if '--install' in sys.argv:
        subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine', '--name',
                        spec['output']], check=True, cwd=REPO)
        print('INSTALLED', spec['output'])


if __name__ == '__main__':
    main()
