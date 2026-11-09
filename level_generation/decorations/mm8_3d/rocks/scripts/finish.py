#!/usr/bin/env python3
"""Finish one rock: work/<rock>/<rock>_export.glb -> material settings (Tar: MASK on the base colour alpha, full
specular) -> tools/link_static_model_lods.py -> validation (LOD chain of 3-4, triangles within rocks.json targets,
COLOR_0 on every primitive, base on the ground, one or two materials) -> work/<rock>/mm8_deco_<rock>.glb; with
--install, tools/install_model.py --engine --name mm8_deco_<rock>.glb (refused over a model this batch did not
install). Usage: finish.py <rock> [--install]"""
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link  # noqa: E402

MATERIALS = {'Tar': {'extras': {'openyamm_specular': 1.0}},
             'Plant': {'alphaMode': 'MASK', 'alphaCutoff': 0.5, 'doubleSided': True}}
INSTALLED_LOG = HERE / 'work' / 'installed.json'


def main():
    prop = sys.argv[1]
    cfg = json.load(open(HERE / 'scripts' / 'rocks.json')).get(prop, {})
    source = HERE / 'work' / prop / f'{prop}_export.glb'
    document, binary = link.read_glb(source)
    for material in document['materials']:
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
        settings = MATERIALS.get(material['name'], {})
        material['doubleSided'] = settings.get('doubleSided', False)
        for key in ('alphaMode', 'alphaCutoff'):
            if key in settings:
                material[key] = settings[key]
        if settings.get('extras'):
            material.setdefault('extras', {}).update(settings['extras'])
    link.link(document)
    name = f'mm8_deco_{prop}.glb'
    out = HERE / 'work' / prop / name
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
    budget = cfg.get('budget', [int(t * (1.6 if cfg.get('tar') else 1.0)) + 8 for t in cfg.get('targets', [])])
    for count, limit in zip(triangles, budget):
        if count > limit:
            problems.append(f'{count} triangles over {limit}')
    lowest = 1e9
    for index in chain:
        for primitive in document['meshes'][index]['primitives']:
            if 'COLOR_0' not in primitive['attributes']:
                problems.append('missing COLOR_0')
            lowest = min(lowest, document['accessors'][primitive['attributes']['POSITION']]['min'][1])
    if abs(lowest) > 0.01:
        problems.append(f'base at y {lowest:.3f}')
    if not 1 <= len(document['materials']) <= cfg.get('materials', 2):
        problems.append(f"{len(document['materials'])} materials")
    images = [(i.get('name'), document['bufferViews'][i['bufferView']]['byteLength']) for i in document.get('images', [])]
    print('VALID' if not problems else 'INVALID', name, 'triangles', triangles, 'materials',
          [m['name'] for m in document['materials']], 'images', images, 'bytes', os.path.getsize(out), problems)
    if problems:
        sys.exit(1)
    # the engine culls back faces of single-sided materials: no inverted closed part may ship
    winding = subprocess.run([sys.executable, str(HERE.parent / 'animated' / 'scripts' / 'check_winding.py'), str(out)],
                             capture_output=True, text=True)
    print(winding.stdout.strip().splitlines()[-1] if winding.stdout.strip() else winding.stderr.strip())
    if winding.returncode:
        print(winding.stdout); sys.exit(1)
    if '--install' in sys.argv:
        own = json.loads(INSTALLED_LOG.read_text()) if INSTALLED_LOG.exists() else []
        if (REPO / 'assets_source' / 'engine' / 'models' / name).exists() and name not in own:
            print('REFUSED', name, 'exists and was not installed by this batch'); sys.exit(1)
        subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine', '--name', name],
                       check=True, cwd=REPO)
        own = json.loads(INSTALLED_LOG.read_text()) if INSTALLED_LOG.exists() else []
        INSTALLED_LOG.write_text(json.dumps(sorted(set(own) | {name}), indent=1))
        print('INSTALLED', name)


if __name__ == '__main__':
    main()
