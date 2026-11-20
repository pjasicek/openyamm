#!/usr/bin/env python3
"""Finish one MM7 plant (adapted from the MM6 succulents' finish.py): work/<id>_export.glb -> material modes (bodies,
bark and pots opaque single-sided; fronds, leaves, pads and spines MASK 0.5 double-sided) ->
tools/link_static_model_lods.py -> tools/cut_foliage_cards.py (cards cut to their texels) -> validation (one mesh
node, a three-level LOD chain with decreasing triangles within budget, COLOR_0/NORMAL/TEXCOORD_0 on every primitive,
base on the ground, no level taller than LOD0, openyamm_specular on every material) -> work/mm7_deco_<id>.glb.
With --install: tools/install_model.py <glb> --engine --name mm7_deco_<id>.glb.
Usage: finish.py <id> [--install]"""
import json, os, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO, SPECS   # noqa: E402
sys.path.insert(0, str(Path(REPO) / 'tools'))
import link_static_model_lods as link   # noqa: E402

OPAQUE = {'Body', 'Bark', 'Pot'}
CUTOUT = {'Fronds', 'Leaves', 'Pads', 'Spines'}


def triangles(document, mesh):
    return sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][mesh]['primitives'])


def bounds(document, mesh):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for p in document['meshes'][mesh]['primitives']:
        acc = document['accessors'][p['attributes']['POSITION']]
        lo = [min(a, b) for a, b in zip(lo, acc['min'])]; hi = [max(a, b) for a, b in zip(hi, acc['max'])]
    return lo, hi


def main():
    sid = sys.argv[1]
    budget = SPECS[sid][2]
    name = f'mm7_deco_{sid}.glb'
    document, binary = link.read_glb(HERE / 'work' / f'{sid}_export.glb')
    for material in document['materials']:
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
        if material['name'] in CUTOUT:
            material['alphaMode'] = 'MASK'; material['alphaCutoff'] = 0.5; material['doubleSided'] = True
        elif material['name'] in OPAQUE:
            material['doubleSided'] = False
        else:
            raise SystemExit(f'unknown material {material["name"]}')
    print('LINKED', link.link(document))
    linked = HERE / 'work' / f'{sid}_linked.glb'
    link.write_glb(linked, document, binary)
    out = HERE / 'work' / name
    subprocess.run([sys.executable, str(Path(REPO) / 'tools' / 'cut_foliage_cards.py'), str(linked), str(out)],
                   check=True)
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
    if len(chain) != 3 or any(b >= a for a, b in zip(counts, counts[1:])):
        problems.append(f'LOD chain {counts}')
    for count, limit in zip(counts, budget):
        if count > limit:
            problems.append(f'{count} triangles over {limit}')
    lo0, hi0 = bounds(document, chain[0])
    for m in chain:
        lo, hi = bounds(document, m)
        if abs(lo[1]) > 0.01:
            problems.append(f'base at y {lo[1]:.3f}')
        if hi[1] > hi0[1] + 0.005:
            problems.append(f'a level is taller than LOD0 ({hi[1]:.3f} > {hi0[1]:.3f})')
        for p in document['meshes'][m]['primitives']:
            if not {'COLOR_0', 'NORMAL', 'TEXCOORD_0'} <= set(p['attributes']):
                problems.append('missing COLOR_0/NORMAL/TEXCOORD_0')
    materials = {}
    for m in document['materials']:
        extras = m.get('extras', {})
        if 'openyamm_specular' not in extras:
            problems.append(f'{m["name"]}: no openyamm_specular')
        materials[m['name']] = (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False), extras)
    size = os.path.getsize(out)
    print('VALID' if not problems else 'INVALID', name, 'triangles', counts, 'bounds', [round(v, 3) for v in lo0],
          [round(v, 3) for v in hi0], 'w/h', round((hi0[0] - lo0[0]) / (hi0[1] - lo0[1]), 2), 'materials',
          json.dumps(materials), 'bytes', size, problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        subprocess.run([sys.executable, str(Path(REPO) / 'tools' / 'install_model.py'), str(out), '--engine',
                        '--name', name], check=True)
        print('INSTALLED', name)


if __name__ == '__main__':
    main()
