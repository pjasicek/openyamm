#!/usr/bin/env python3
"""work/dead_<id>/tree_export.glb -> material modes -> tools/link_static_model_lods.py -> validation ->
tools/cut_foliage_cards.py (twig cards and the impostor cut to their texture outline) -> [install].
Materials: Bark and Wood opaque single-sided; Twigs and Impostor MASK 0.5 double-sided with openyamm_specular 0.1
(thin cards seen edge-on would otherwise catch a bright sky sheen). Wind (openyamm_wind) is the same on every wood
and twig material, so twigs stay on their branches. Every primitive must carry COLOR_0; LOD triangles must fit the
budget. Usage: dead_post.py <id> [--install]"""
import os, subprocess, sys
from pathlib import Path
import numpy as np
import dead_common as dc

spec = dc.load(); W = spec['work']
sys.path.insert(0, os.path.join(dc.REPO, 'tools'))
import link_static_model_lods as link
STUMP = spec['kind'] == 'stump'
BUDGET = list(spec['budget']) + ([] if STUMP else [2])

doc, binary = link.read_glb(Path(os.path.join(W, 'tree_export.glb')))
for m in doc['materials']:
    if m['name'] in ('Bark', 'Wood'):
        m.pop('alphaMode', None); m.pop('alphaCutoff', None); m['doubleSided'] = False
    else:
        m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
        m.setdefault('extras', {})['openyamm_specular'] = 0.1
link.link(doc)
out = os.path.join(W, spec['output'])
link.write_glb(Path(out), doc, binary)

doc, binary = link.read_glb(Path(out))


def accessor(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(a['count'], n)


mats = {m['name']: m for m in doc['materials']}
want = {'Bark', 'Wood'} | (set() if STUMP else {'Twigs', 'Impostor'})
if spec['kind'] in ('shrub', 'gnarled', 'broad'):
    want.discard('Wood')
assert set(mats) == want, mats.keys()
winds = {m.get('extras', {}).get('openyamm_wind', 0.0) for n, m in mats.items() if n != 'Impostor'}
assert len(winds) == 1, winds
for name in ('Twigs', 'Impostor'):
    if name in mats:
        assert mats[name]['alphaMode'] == 'MASK' and mats[name]['doubleSided']
if 'Impostor' in mats:
    assert mats['Impostor']['extras']['openyamm_billboard'] is True
base = next(n for n in doc['nodes'] if n['name'] == 'Tree')
assert len(doc['nodes']) == 1 and not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix'))
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
assert len(chain) == 4, chain
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert all(c <= b for c, b in zip(counts, BUDGET)), (counts, BUDGET)
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], ('COLOR_0 missing', doc['meshes'][i]['name'])
allpos = np.concatenate([accessor(p['attributes']['POSITION']) for p in doc['meshes'][chain[0]]['primitives']])
print('VALID LOD triangles', counts, 'bounds', allpos.min(0).round(2).tolist(), allpos.max(0).round(2).tolist())
print('VALID materials', {k: (v.get('alphaMode', 'OPAQUE'), v['doubleSided'], v.get('extras')) for k, v in mats.items()})
cut = os.path.join(W, 'cut_' + spec['output'])
subprocess.run([sys.executable, os.path.join(dc.REPO, 'tools', 'cut_foliage_cards.py'), out, cut], check=True)
os.replace(cut, out)
print('VALID file bytes', os.path.getsize(out))
if '--install' in sys.argv:
    subprocess.run([sys.executable, os.path.join(dc.REPO, 'tools', 'install_model.py'), out, '--engine', '--name',
                    spec['output']], check=True)
    print('INSTALLED', os.path.join('assets_source', 'engine', 'models', spec['output']))
