#!/usr/bin/env python3
"""work/tree_export.glb -> material fixes -> tools/link_static_model_lods.py -> validation -> install.
Materials: Bark opaque single-sided; Leaves and Impostor MASK 0.5 double-sided; extras kept from Blender
(openyamm_wind / openyamm_billboard). Usage: post_process.py [--install]"""
import json, os, struct, subprocess, sys
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
WORK = os.path.join(HERE, 'work')
DEST = os.path.join(REPO, 'assets_dev', 'worlds', 'mm6', 'models', 'mm6_deco_tree01.glb')
BUDGET = [8000, 3000, 1000, 2]
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link

doc, binary = link.read_glb(__import__('pathlib').Path(os.path.join(WORK, 'tree_export.glb')))
for m in doc['materials']:
    if m['name'] == 'Bark':
        m.pop('alphaMode', None); m.pop('alphaCutoff', None); m['doubleSided'] = False
    else:
        m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
report = link.link(doc)
out = os.path.join(WORK, 'mm6_deco_tree01.glb')
link.write_glb(__import__('pathlib').Path(out), doc, binary)

# ---- validation (re-read the written file)
doc, binary = link.read_glb(__import__('pathlib').Path(out))


def accessor(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    return np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(a['count'], n)


mats = {m['name']: m for m in doc['materials']}
assert set(mats) == {'Bark', 'Leaves', 'Impostor'}, mats.keys()
assert mats['Bark'].get('alphaMode', 'OPAQUE') == 'OPAQUE' and not mats['Bark']['doubleSided']
assert mats['Bark']['extras']['openyamm_wind'] == 0.03
for name in ('Leaves', 'Impostor'):
    assert mats[name]['alphaMode'] == 'MASK' and mats[name]['alphaCutoff'] == 0.5 and mats[name]['doubleSided']
assert mats['Leaves']['extras']['openyamm_wind'] == 0.12 and mats['Impostor']['extras']['openyamm_billboard'] is True
base = next(n for n in doc['nodes'] if n['name'] == 'Tree')
assert len(doc['nodes']) == 1 and not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix'))
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
assert len(chain) == 4
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert all(c <= b for c, b in zip(counts, BUDGET)), counts
quad = doc['meshes'][chain[3]]['primitives']
assert len(quad) == 1 and doc['materials'][quad[0]['material']]['name'] == 'Impostor'
pos = accessor(quad[0]['attributes']['POSITION']); nrm = accessor(quad[0]['attributes']['NORMAL'])
assert np.allclose(pos[:, 2], 0, atol=1e-5) and abs(pos[:, 1].min()) < 1e-5
assert np.isclose(pos[:, 0].min(), -pos[:, 0].max(), atol=1e-4) and np.allclose(nrm, [0, 0, 1], atol=1e-4)
allpos = np.concatenate([accessor(p['attributes']['POSITION']) for p in doc['meshes'][chain[0]]['primitives']])
print('VALID materials', {k: (v.get('alphaMode', 'OPAQUE'), v['doubleSided'], v.get('extras')) for k, v in mats.items()})
print('VALID LOD triangles', counts, 'bounds', allpos.min(0).round(2).tolist(), allpos.max(0).round(2).tolist(),
      'impostor', pos.min(0).round(2).tolist(), pos.max(0).round(2).tolist())
print('VALID images', [(i['name'], doc['bufferViews'][i['bufferView']]['byteLength']) for i in doc['images']],
      'file bytes', os.path.getsize(out))
if '--install' in sys.argv:
    subprocess.run(['install', '-m', '0664', out, DEST], check=True)
    print('INSTALLED', DEST)
