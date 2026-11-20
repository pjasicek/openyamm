#!/usr/bin/env python3
"""Finish one meadow bush: work/<id>_export.glb -> material modes (Bark opaque single-sided; Leaves MASK 0.5
double-sided) -> tools/link_static_model_lods.py (LOD meshes listed in the base mesh's extras.openyamm_lods) ->
tools/cut_foliage_cards.py (cards cut to their texels) -> validation -> work/<id>.glb and work/<id>_final.json.
Validation: one node without transform, a three-level chain with decreasing triangles within budget,
COLOR_0/NORMAL/TEXCOORD_0 on every primitive, base on the ground (y within 4 cm below 0, the stems' buried ends),
no level taller than LOD0, LOD0's cut top at the target height, the expected material extras, identical shared images in every bush.
With --install: tools/install_model.py <glb> --engine --name <id>.glb. Usage: finish.py <id> [--install]"""
import hashlib
import json
import os
import subprocess
import sys

import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE / 'scripts'))
sys.path.insert(0, str(REPO / 'tools'))
from bushes import BUSHES   # noqa: E402
import link_static_model_lods as link   # noqa: E402


def triangles(document, mesh):
    return sum(document['accessors'][p['indices']]['count'] // 3 for p in document['meshes'][mesh]['primitives'])


def bounds(document, mesh):
    lo, hi = [1e9] * 3, [-1e9] * 3
    for p in document['meshes'][mesh]['primitives']:
        acc = document['accessors'][p['attributes']['POSITION']]
        lo = [min(a, b) for a, b in zip(lo, acc['min'])]; hi = [max(a, b) for a, b in zip(hi, acc['max'])]
    return lo, hi


def positions(document, binary, accessor_index):
    accessor = document['accessors'][accessor_index]
    view = document['bufferViews'][accessor['bufferView']]
    assert accessor['componentType'] == 5126 and view.get('byteStride', 12) == 12
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    return offset, np.frombuffer(bytes(binary[offset:offset + accessor['count'] * 12]), np.float32).reshape(-1, 3).copy()


def fit_height(document, binary, height):
    """Cutting the cards to their texels lowers the top of LOD0 a little (the top card's transparent corner is gone):
    scale every level uniformly so LOD0's cut top is the target height again, then clamp the coarser levels'
    vertices to that height, so no level pops above LOD0 at a switch."""
    chain = [document['nodes'][0]['mesh']] + document['meshes'][document['nodes'][0]['mesh']]['extras']['openyamm_lods']
    top = max(document['accessors'][p['attributes']['POSITION']]['max'][1]
              for p in document['meshes'][chain[0]]['primitives'])
    scale = height / top
    seen = set()
    for level, mesh in enumerate(chain):
        for p in document['meshes'][mesh]['primitives']:
            index = p['attributes']['POSITION']
            if index in seen:
                continue
            seen.add(index)
            offset, pos = positions(document, binary, index)
            pos *= scale
            if level:
                pos[:, 1] = np.minimum(pos[:, 1], height)
            binary[offset:offset + pos.nbytes] = pos.astype(np.float32).tobytes()
            document['accessors'][index]['min'] = pos.min(0).tolist()
            document['accessors'][index]['max'] = pos.max(0).tolist()
    print('FIT height scale', round(scale, 4))


def main():
    bid = sys.argv[1]
    spec = BUSHES[bid]
    document, binary = link.read_glb(HERE / 'work' / f'{bid}_export.glb')
    for material in document['materials']:
        material.pop('alphaMode', None); material.pop('alphaCutoff', None)
        if material['name'] == 'Leaves':
            material['alphaMode'] = 'MASK'; material['alphaCutoff'] = 0.5; material['doubleSided'] = True
        elif material['name'] == 'Bark':
            material['doubleSided'] = False
        else:
            raise SystemExit(f'unknown material {material["name"]}')
    print('LINKED', link.link(document))
    linked = HERE / 'work' / f'{bid}_linked.glb'
    link.write_glb(linked, document, binary)
    out = HERE / 'work' / f'{bid}.glb'
    subprocess.run([sys.executable, str(REPO / 'tools' / 'cut_foliage_cards.py'), str(linked), str(out)], check=True)
    document, binary = link.read_glb(out)
    fit_height(document, binary, spec['height'])
    link.write_glb(out, document, binary)
    document, binary = link.read_glb(out)
    problems = []
    if len(document['nodes']) != 1 or 'mesh' not in document['nodes'][0]:
        problems.append(f'{len(document["nodes"])} nodes')
    base = document['nodes'][0]
    if any(k in base for k in ('translation', 'rotation', 'scale', 'matrix')) or 'skins' in document \
            or 'animations' in document:
        problems.append('transform/skin/animation on the node')
    chain = [base['mesh']] + document['meshes'][base['mesh']].get('extras', {}).get('openyamm_lods', [])
    counts = [triangles(document, m) for m in chain]
    if len(chain) != 3 or any(b >= a for a, b in zip(counts, counts[1:])):
        problems.append(f'LOD chain {counts}')
    for count, limit in zip(counts, spec['budget']):
        if count > limit:
            problems.append(f'{count} triangles over {limit}')
    lo0, hi0 = bounds(document, chain[0])
    for m in chain:
        lo, hi = bounds(document, m)
        if not -0.04 <= lo[1] <= (0.01 if m == chain[0] else 0.06):
            problems.append(f'base at y {lo[1]:.3f}')
        if hi[1] > hi0[1] + 0.005:
            problems.append(f'a level is taller than LOD0 ({hi[1]:.3f} > {hi0[1]:.3f})')
        for p in document['meshes'][m]['primitives']:
            if not {'COLOR_0', 'NORMAL', 'TEXCOORD_0'} <= set(p['attributes']):
                problems.append('missing COLOR_0/NORMAL/TEXCOORD_0')
    if abs(hi0[1] - spec['height']) > 0.002:
        problems.append(f'height {hi0[1]:.3f} against {spec["height"]}')
    materials = {}
    for m in document['materials']:
        extras = m.get('extras', {})
        want = {'openyamm_specular': 0.1, 'openyamm_wind': spec['wind'] if m['name'] == 'Leaves'
                else round(spec['wind'] * 0.25, 4)}
        if m['name'] == 'Leaves':
            want['openyamm_translucency'] = 0.35
        if any(abs(extras.get(k, -1) - v) > 1e-6 for k, v in want.items()):
            problems.append(f'{m["name"]} extras {extras}')
        materials[m['name']] = (m.get('alphaMode', 'OPAQUE'), m.get('doubleSided', False), extras)
    images = {}
    for image in document['images']:
        view = document['bufferViews'][image['bufferView']]
        data = bytes(binary[view.get('byteOffset', 0):view.get('byteOffset', 0) + view['byteLength']])
        images[image['name']] = (len(data), hashlib.sha256(data).hexdigest()[:16])
    size = os.path.getsize(out)
    result = {'id': bid, 'triangles': counts, 'bounds_gltf': [[round(v, 3) for v in lo0], [round(v, 3) for v in hi0]],
              'height_m': round(hi0[1], 3), 'footprint_m': [round(hi0[0] - lo0[0], 3), round(hi0[2] - lo0[2], 3)],
              'materials': materials, 'images': images, 'bytes': size, 'problems': problems}
    json.dump(result, open(HERE / 'work' / f'{bid}_final.json', 'w'), indent=1)
    print('VALID' if not problems else 'INVALID', bid, 'triangles', counts, 'height', result['height_m'],
          'footprint', result['footprint_m'], 'materials', json.dumps(materials), 'images', images, 'bytes', size,
          problems)
    if problems:
        sys.exit(1)
    if '--install' in sys.argv:
        subprocess.run([sys.executable, str(REPO / 'tools' / 'install_model.py'), str(out), '--engine',
                        '--name', f'{bid}.glb'], check=True)
        print('INSTALLED', bid)


if __name__ == '__main__':
    main()
