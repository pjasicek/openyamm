#!/usr/bin/env python3
"""work/<id>/export.glb -> material modes -> tools/link_static_model_lods.py -> tools/cut_foliage_cards.py ->
validation -> work/<id>/mm8_deco_<id>.glb and work/<id>/stats.json [--install: tools/install_model.py --engine].
Materials: cut-out ones (Foliage, Twigs, Spines, Flowers) MASK 0.5 double-sided; the rest (Bark, Wood, Body)
opaque single-sided. Every material carries the same openyamm_wind, so attached parts sway together.
Usage: post.py <id> [--install]"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link

CUTOUT = {'Foliage', 'Twigs', 'Spines', 'Flowers', 'Leaves'}


def accessor(doc, binary, index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    x = np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(a['count'], n)
    if a.get('normalized') and dt != np.float32:
        x = x.astype(np.float64) / np.iinfo(dt).max
    return x


def main(sid, install):
    work = os.path.join(HERE, 'work', sid)
    name = f'mm8_deco_{sid}.glb'
    doc, binary = link.read_glb(Path(os.path.join(work, 'export.glb')))
    for m in doc['materials']:
        if m['name'] in CUTOUT:
            m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
        else:
            m.pop('alphaMode', None); m.pop('alphaCutoff', None); m['doubleSided'] = False
    print('LINKED', link.link(doc))
    linked = os.path.join(work, 'linked.glb')
    link.write_glb(Path(linked), doc, binary)
    out = os.path.join(work, name)
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'cut_foliage_cards.py'), linked, out], check=True,
                   stdout=subprocess.DEVNULL)
    doc, binary = link.read_glb(Path(out))
    winds = {m['name']: m.get('extras', {}).get('openyamm_wind') for m in doc['materials']}
    assert len(set(winds.values())) == 1, winds
    assert len(doc['nodes']) == 1, [n.get('name') for n in doc['nodes']]
    base = doc['nodes'][0]
    assert not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix'))
    assert 'skins' not in doc and 'animations' not in doc
    chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
    counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
    assert counts == sorted(counts, reverse=True) and len(set(counts)) == len(counts), counts
    lo, hi = [], []
    for i in chain:
        for p in doc['meshes'][i]['primitives']:
            assert 'COLOR_0' in p['attributes'], 'COLOR_0 missing'
            c = accessor(doc, binary, p['attributes']['COLOR_0'])
            assert c[:, :3].max() <= 1.0001 and c[:, :3].min() >= 0, (c.min(), c.max())
            pos = accessor(doc, binary, p['attributes']['POSITION'])
            lo.append(pos.min(0)); hi.append(pos.max(0))
    lo, hi = np.min(lo, 0), np.max(hi, 0)
    p0 = np.concatenate([accessor(doc, binary, p['attributes']['POSITION']) for p in doc['meshes'][chain[0]]['primitives']])
    stats = {'triangles': counts, 'bytes': os.path.getsize(out), 'bounds_min': lo.round(3).tolist(),
             'bounds_max': hi.round(3).tolist(), 'lod0_height': round(float(p0[:, 1].max() - p0[:, 1].min()), 4),
             'lod0_min_y': round(float(p0[:, 1].min()), 4),
             'materials': {m['name']: (m.get('alphaMode', 'OPAQUE'), m['doubleSided'], m.get('extras'))
                           for m in doc['materials']},
             'images': [(i.get('name'), doc['bufferViews'][i['bufferView']]['byteLength']) for i in doc['images']]}
    with open(os.path.join(work, 'stats.json'), 'w') as fh:
        json.dump(stats, fh, indent=1)
    print('VALID', name, json.dumps(stats))
    if install:
        subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), out, '--engine', '--name',
                        name], check=True)
        print('INSTALLED', name)


if __name__ == '__main__':
    main(sys.argv[1], '--install' in sys.argv)
