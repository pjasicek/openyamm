#!/usr/bin/env python3
"""work/<id>/plant_export.glb -> material modes -> tools/link_static_model_lods.py -> validation ->
tools/cut_foliage_cards.py (leaf cards and the impostor cut to their texture outline) -> [--install] with
tools/install_model.py --engine --name mm8_deco_<id>.glb (source in assets_source/engine/models/, cooked runtime copy in
assets_dev/engine/models/). Adapted from the MM6 desert post-processing.
Materials: Bark opaque single-sided; Leaves and Impostor MASK 0.5 double-sided. Extras from Blender: the same
openyamm_wind on every material (so leaves stay on their stems), openyamm_specular (palm_common) and openyamm_translucency on
Leaves, openyamm_billboard + openyamm_specular on Impostor. Usage: post_process.py <id> [--install]"""
import os, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import palm_common as dc
sys.path.insert(0, os.path.join(dc.REPO, 'tools'))
import link_static_model_lods as link

SID = sys.argv[1]
WORK = dc.work(SID)
OUT_NAME = dc.output(SID)
BUDGET = dc.BUDGET
doc, binary = link.read_glb(Path(os.path.join(WORK, 'plant_export.glb')))
for m in doc['materials']:
    if m['name'] == 'Bark':
        m.pop('alphaMode', None); m.pop('alphaCutoff', None); m['doubleSided'] = False
    else:
        m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
print('LINKED', link.link(doc))
linked = os.path.join(WORK, 'linked.glb')
link.write_glb(Path(linked), doc, binary)
out = os.path.join(WORK, OUT_NAME)
subprocess.run([sys.executable, os.path.join(dc.REPO, 'tools', 'cut_foliage_cards.py'), linked, out], check=True)

# ---- validation of the written file
doc, binary = link.read_glb(Path(out))


def accessor(index):
    a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
    n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
    dt = {5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}[a['componentType']]
    off = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    x = np.frombuffer(bytes(binary[off:off + a['count'] * n * np.dtype(dt).itemsize]), dt).reshape(a['count'], n)
    if a.get('normalized') and dt != np.float32:
        x = x.astype(np.float64) / np.iinfo(dt).max
    return x


mats = {m['name']: m for m in doc['materials']}
assert set(mats) == {'Bark', 'Leaves', 'Impostor'}, mats.keys()
assert 'Bark' not in mats or (mats['Bark'].get('alphaMode', 'OPAQUE') == 'OPAQUE' and not mats['Bark']['doubleSided'])
for name in ('Leaves', 'Impostor'):
    assert mats[name]['alphaMode'] == 'MASK' and mats[name]['alphaCutoff'] == 0.5 and mats[name]['doubleSided']
winds = {k: v['extras']['openyamm_wind'] for k, v in mats.items()}
assert len(set(winds.values())) == 1 and 0 < winds['Leaves'] <= 0.2, winds
SPEC = dc.SPECIES[SID].get('specular', dc.SPECULAR)
assert abs(mats['Leaves']['extras']['openyamm_specular'] - SPEC) < 1e-6
assert mats['Leaves']['extras']['openyamm_translucency'] == dc.TRANSLUCENCY
assert mats['Impostor']['extras']['openyamm_billboard'] is True and abs(mats['Impostor']['extras']['openyamm_specular'] - SPEC) < 1e-6
assert len(doc['nodes']) == 1 and doc['nodes'][0]['name'] == 'Plant'
base = doc['nodes'][0]
assert not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix')) and 'skins' not in doc and 'animations' not in doc
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
assert len(chain) == 4
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert all(c <= b for c, b in zip(counts, BUDGET)) and counts == sorted(counts, reverse=True), (counts, BUDGET)
colours = []
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], ('COLOR_0 missing', doc['meshes'][i]['name'])
        c = accessor(p['attributes']['COLOR_0']).astype(np.float64)
        colours.append((doc['meshes'][i]['name'], doc['materials'][p['material']]['name'], round(float(c[:, :3].min()), 3),
                        round(float(c[:, :3].mean()), 3)))
quad = doc['meshes'][chain[3]]['primitives']
assert len(quad) == 1 and doc['materials'][quad[0]['material']]['name'] == 'Impostor'
qpos = accessor(quad[0]['attributes']['POSITION'])
assert np.allclose(qpos[:, 2], 0, atol=1e-5) and qpos[:, 1].min() >= -1e-4 and qpos[:, 1].min() < 0.1 * qpos[:, 1].max()
pos = np.concatenate([accessor(p['attributes']['POSITION']) for i in chain[:3] for p in doc['meshes'][i]['primitives']])
assert abs(pos[:, 1].min()) < 0.02, pos[:, 1].min()
print('VALID COLOR_0 (mesh, material, min, mean)', colours)
print('VALID materials', {k: (v.get('alphaMode', 'OPAQUE'), v['doubleSided'], v.get('extras')) for k, v in mats.items()})
print('VALID', OUT_NAME, 'LOD triangles', counts, 'bounds', pos.min(0).round(2).tolist(), pos.max(0).round(2).tolist(),
      'impostor', qpos.min(0).round(2).tolist(), qpos.max(0).round(2).tolist())
print('VALID images', [(i.get('name'), doc['bufferViews'][i['bufferView']]['byteLength']) for i in doc['images']],
      'file bytes', os.path.getsize(out))
with open(os.path.join(WORK, 'tris.txt'), 'w') as fh:
    fh.write(' '.join(str(c) for c in counts))
# face orientation (the engine culls back faces of the single-sided bark; Blender's renders do not)
subprocess.run([sys.executable, os.path.join(dc.PALMS, '..', 'animated', 'scripts', 'check_winding.py'), out], check=True)
if '--install' in sys.argv:
    subprocess.run([sys.executable, os.path.join(dc.REPO, 'tools', 'install_model.py'), out, '--engine', '--name',
                    OUT_NAME], check=True)
    print('INSTALLED', OUT_NAME)
