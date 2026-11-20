#!/usr/bin/env python3
"""Finish one leftover dungeon decoration: its export GLB (work/<prop>_export.glb unless the entry names `export`)
-> material settings from FINISH[prop] (alpha mode, double-sided, unlit, emissive, extras) ->
tools/link_static_model_lods.py -> validation (LOD chain of 3-4, triangle budgets, COLOR_0 on every primitive, base on
the ground) -> work/<output>.glb, installed (0664) with --install, never over an existing GLB.
FINISH merges the TABLE of every scripts/finish_<group>.py (corpses, rocks, plants), so each group keeps its own table.
Usage: finish.py <prop> [--install] [--replace-own]   (--replace-own: overwrite a GLB this batch installed before)"""
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

FLAME = {'alpha': 'BLEND', 'double': True, 'unlit': True}
FINISH = {}
for path in sorted(glob.glob(str(HERE / 'scripts' / 'finish_*.py'))):
    spec = importlib.util.spec_from_file_location(Path(path).stem, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    FINISH.update(module.TABLE)
INSTALLED_LOG = HERE / 'work' / 'installed.json'     # outputs this batch installed (may be replaced by a rebuild)


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
    if abs(lowest) > 0.03:
        problems.append(f'base at y {lowest:.3f}')
    materials = {m['name']: (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False),
                             'unlit' if 'KHR_materials_unlit' in m.get('extensions', {}) else '', m.get('extras', {}))
                 for m in document['materials']}
    print('VALID' if not problems else 'INVALID', spec['output'], 'triangles', triangles, 'materials', materials,
          'bytes', os.path.getsize(out), problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / spec['output']
        own = json.loads(INSTALLED_LOG.read_text()) if INSTALLED_LOG.exists() else []
        if destination.exists() and not (spec['output'] in own and '--replace-own' in sys.argv):
            print('REFUSED', destination, 'exists' + (' (ours: pass --replace-own)' if spec['output'] in own else ''))
            sys.exit(1)
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        if spec['output'] not in own:
            # re-read: another group's finish may have logged meanwhile
            own = json.loads(INSTALLED_LOG.read_text()) if INSTALLED_LOG.exists() else []
            INSTALLED_LOG.write_text(json.dumps(sorted(set(own) | {spec['output']}), indent=1))
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
