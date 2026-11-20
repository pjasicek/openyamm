#!/usr/bin/env python3
"""Finish one model of the MM7 dressing batch: work/<prop>_export.glb (or the entry's `export`) -> material settings
(alpha mode, double-sided, unlit, emissive, extras) -> tools/link_static_model_lods.py -> validation (one mesh node,
LOD chain of 3-4, triangle budgets, COLOR_0 on every primitive, base on the ground, no inside-out closed part by
the MM8 batch's check_winding.py) -> work/<output>.glb; --install
runs tools/install_model.py <work/output> --engine --name <output>. FINISH merges the TABLE of every
scripts/finish_<group>.py, so each group keeps its own table. Install refuses names that exist in
assets_source/engine/models unless this batch installed them before (work/installed.json).
Usage: finish.py <prop> [--install]"""
import glob
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

FINISH = {}
for path in sorted(glob.glob(str(HERE / 'scripts' / 'finish_*.py'))):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    FINISH.update(module.TABLE)
INSTALLED_LOG = HERE / 'work' / 'installed.json'


def main():
    prop = sys.argv[1]
    spec = FINISH[prop]
    source = HERE / spec['export'] if 'export' in spec else HERE / 'work' / f'{prop}_export.glb'
    document, binary = link.read_glb(source)
    for material in document['materials']:
        settings = spec.get('materials', {}).get(material['name'], {})
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
    if not 3 <= len(chain) <= 4:
        problems.append(f'LOD chain of {len(chain)}')
    for count, budget in zip(triangles, spec['budget']):
        if count > budget:
            problems.append(f'{count} triangles over {budget}')
    lowest = 1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            lowest = min(lowest, document['accessors'][primitive['attributes']['POSITION']]['min'][1])
    if abs(lowest) > spec.get('base_tolerance', 0.03):
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', os.path.getsize(out), problems)
    winding = subprocess.run([sys.executable, str(REPO / 'level_generation' / 'decorations' / 'mm8_3d' / 'animated' /
                                                  'scripts' / 'check_winding.py'), str(out)],
                             capture_output=True, text=True)
    report = [line for line in winding.stdout.splitlines() if line.startswith(('WINDING', 'INVERTED'))]
    print('\n'.join(report))
    if not report or not report[-1].rstrip().endswith('inverted closed parts: 0'):
        problems.append('inverted closed parts (check_winding.py)')
    if problems:
        print('INVALID', problems)
        sys.exit(1)
    if '--install' in sys.argv:
        installed = json.loads(INSTALLED_LOG.read_text()) if INSTALLED_LOG.exists() else []
        destination = REPO / 'assets_source' / 'engine' / 'models' / spec['output']
        if destination.exists() and spec['output'] not in installed:
            sys.exit(f'{destination} exists and was not installed by this batch')
        subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine', '--name',
                        spec['output']], check=True, cwd=REPO)
        if spec['output'] not in installed:
            installed.append(spec['output'])
            INSTALLED_LOG.write_text(json.dumps(sorted(installed), indent=1) + '\n')
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
