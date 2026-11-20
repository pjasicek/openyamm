#!/usr/bin/env python3
"""Finish one succulent: work/<id>_export.glb -> material modes (opaque bodies and rock single-sided; spines, pads
and foliage MASK 0.5 double-sided) -> tools/link_static_model_lods.py -> tools/cut_foliage_cards.py for the card
models (pads and shrubs; not the barrel, whose spine layer tiles past 0..1) -> validation (one mesh node, four-level
LOD chain with decreasing triangles within budget, COLOR_0 on every primitive, base on the ground, material extras)
-> work/mm6_deco_<id>.glb, installed 0664 into assets_dev/worlds/mm6/models with --install.
Usage: finish.py <id> [--install]"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[3]
sys.path.insert(0, str(REPO / 'tools'))
import link_static_model_lods as link

OPAQUE = {'alpha': None, 'double': False}
CUTOUT = {'alpha': 'MASK', 'double': True}
SPEC = {
    'cac8': dict(budget=[1500, 900, 500, 170], cut=False, materials={'Body': OPAQUE, 'Spines': CUTOUT}),
    'cac5': dict(budget=[2500, 1200, 650, 200], cut=False, materials={'Body': OPAQUE}),
    'cac16': dict(budget=[1500, 950, 350, 180], cut=False, materials={'Body': OPAQUE}),
    'cac7': dict(budget=[2500, 450, 350, 230], cut=True, materials={'Pads': CUTOUT}),
    'cac10': dict(budget=[3000, 1600, 320, 230], cut=True, materials={'Pads': CUTOUT}),
    'cac15': dict(budget=[3000, 1600, 320, 250], cut=True, materials={'Pads': CUTOUT}),
    'cac27': dict(budget=[1500, 600, 300, 150], cut=True, materials={'Rock': OPAQUE, 'Foliage': CUTOUT}),
    'snoweed1': dict(budget=[600, 300, 150, 80], cut=True, materials={'Foliage': CUTOUT}),
}


def triangles(document, mesh):
    return sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][mesh]['primitives'])


def main():
    sid = sys.argv[1]
    spec = SPEC[sid]
    name = f'mm6_deco_{sid}.glb'
    document, binary = link.read_glb(HERE / 'work' / f'{sid}_export.glb')
    for material in document['materials']:
        mode = spec['materials'][material['name']]
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
        if mode['alpha']:
            material['alphaMode'] = mode['alpha']; material['alphaCutoff'] = 0.5
        material['doubleSided'] = mode['double']
    print('LINKED', link.link(document))
    linked = HERE / 'work' / f'{sid}_linked.glb'
    link.write_glb(linked, document, binary)
    out = HERE / 'work' / name
    if spec['cut']:
        subprocess.run([sys.executable, str(REPO / 'tools' / 'cut_foliage_cards.py'), str(linked), str(out)], check=True)
    else:
        out.write_bytes(linked.read_bytes())
    document, _ = link.read_glb(out)
    problems = []
    nodes = [n for n in document['nodes'] if 'mesh' in n]
    if len(nodes) != 1 or len(document['nodes']) != 1:
        problems.append(f'{len(document["nodes"])} nodes')
    base = nodes[0]
    if any(k in base for k in ('translation', 'rotation', 'scale', 'matrix')) or 'skins' in document \
            or 'animations' in document:
        problems.append('transform/skin/animation on the node')
    chain = [base['mesh']] + document['meshes'][base['mesh']].get('extras', {}).get('openyamm_lods', [])
    counts = [triangles(document, m) for m in chain]
    if len(chain) != 4 or any(b >= a for a, b in zip(counts, counts[1:])):
        problems.append(f'LOD chain {counts}')
    for count, budget in zip(counts, spec['budget']):
        if count > budget:
            problems.append(f'{count} triangles over {budget}')
    lo, hi = [1e9] * 3, [-1e9] * 3
    for m in chain:
        for p in document['meshes'][m]['primitives']:
            if 'COLOR_0' not in p['attributes'] or 'NORMAL' not in p['attributes'] or 'TEXCOORD_0' not in p['attributes']:
                problems.append('missing COLOR_0/NORMAL/TEXCOORD_0')
            acc = document['accessors'][p['attributes']['POSITION']]
            lo = [min(a, b) for a, b in zip(lo, acc['min'])]; hi = [max(a, b) for a, b in zip(hi, acc['max'])]
    if abs(lo[1]) > 0.01:
        problems.append(f'base at y {lo[1]:.3f}')
    materials = {}
    for m in document['materials']:
        extras = m.get('extras', {})
        if 'openyamm_specular' not in extras:
            problems.append(f'{m["name"]}: no openyamm_specular')
        materials[m['name']] = (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False), extras)
    size = os.path.getsize(out)
    print('VALID' if not problems else 'INVALID', name, 'triangles', counts, 'bounds', [round(v, 3) for v in lo],
          [round(v, 3) for v in hi], 'materials', json.dumps(materials), 'bytes', size, problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        destination = REPO / 'assets_dev' / 'worlds' / 'mm6' / 'models' / name
        subprocess.run(['install', '-m', '0664', str(out), str(destination)], check=True)
        print('INSTALLED', destination)


if __name__ == '__main__':
    main()
