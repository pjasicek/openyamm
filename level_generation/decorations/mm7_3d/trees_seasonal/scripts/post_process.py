#!/usr/bin/env python3
"""work/<id>/tree_export.glb -> material fixes -> tools/link_static_model_lods.py -> validation ->
tools/cut_foliage_cards.py (leaf, clump and impostor cards cut to their texture's outline) -> install
(tools/install_model.py --engine; work/<id>/model.json keeps the LOD triangles and LOD0 bounds).
Materials: Bark opaque single-sided; Leaves, LeavesFar (LOD2 clump cards) and Impostor MASK 0.5 double-sided; extras kept from Blender
(openyamm_wind / openyamm_translucency / openyamm_billboard), plus openyamm_specular on the leaf and impostor cards;
every LOD mesh must carry COLOR_0.
A food tree's opaque Fruit material is validated too. Usage: post_process.py <id> [--install]"""
import json, os, struct, subprocess, sys
import numpy as np
import common
spec = common.load()
REPO = common.REPO
WORK = spec['work']
BUDGET = list(spec['bare']['triangles'] if spec['season'] == 'bare' else spec['lod']['triangles']) + [2]
SPECULAR = 0.1
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link

doc, binary = link.read_glb(__import__('pathlib').Path(os.path.join(WORK, 'tree_export.glb')))
for m in doc['materials']:
    if m['name'] in ('Bark', 'Fruit'):
        m.pop('alphaMode', None); m.pop('alphaCutoff', None); m['doubleSided'] = False
    else:
        m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
        # Leaf cards seen edge-on would catch a near-white Fresnel sheen at full specular (engine openyamm_specular).
        m.setdefault('extras', {})['openyamm_specular'] = SPECULAR
report = link.link(doc)
out = os.path.join(WORK, spec['output'])
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
BARE = spec['season'] == 'bare'
if BARE:                                # winter state (bare_build.py): wood and twig cards, the same sway on both
    assert set(mats) == {'Bark', 'Twigs', 'Impostor'}, mats.keys()
    assert mats['Twigs']['alphaMode'] == 'MASK' and mats['Twigs']['doubleSided']
    assert mats['Twigs']['extras']['openyamm_wind'] == mats['Bark']['extras']['openyamm_wind'] == 0.03
    assert mats['Impostor']['extras']['openyamm_billboard'] is True
else:
    assert set(mats) == {'Bark', 'Leaves', 'LeavesFar', 'Impostor'} | ({'Fruit'} if spec['fruit'] else set()) \
        | ({'Moss'} if spec['crown'].get('moss') else set()), mats.keys()
    for name in ('Leaves', 'LeavesFar', 'Impostor') + (('Moss',) if 'Moss' in mats else ()):
        assert mats[name]['alphaMode'] == 'MASK' and mats[name]['alphaCutoff'] == 0.5 and mats[name]['doubleSided']
    assert mats['Leaves']['extras']['openyamm_wind'] == 0.12 and mats['Impostor']['extras']['openyamm_billboard'] is True
    for name in ('Leaves', 'LeavesFar'):
        assert mats[name]['extras']['openyamm_wind'] == 0.12 and mats[name]['extras']['openyamm_translucency'] == 0.35
assert mats['Bark'].get('alphaMode', 'OPAQUE') == 'OPAQUE' and not mats['Bark']['doubleSided']
assert mats['Bark']['extras']['openyamm_wind'] == 0.03
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
colour_ranges = []
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], ('COLOR_0 missing', doc['meshes'][i]['name'])
        a = doc['accessors'][p['attributes']['COLOR_0']]
        c = accessor(p['attributes']['COLOR_0']).astype(np.float64)
        if a['componentType'] != 5126:
            c /= {5121: 255.0, 5123: 65535.0}[a['componentType']]
        colour_ranges.append((doc['meshes'][i]['name'], round(float(c[:, :3].min()), 3), round(float(c[:, :3].mean()), 3)))
print('VALID COLOR_0 (mesh, min, mean)', colour_ranges)
allpos = np.concatenate([accessor(p['attributes']['POSITION']) for p in doc['meshes'][chain[0]]['primitives']])
print('VALID materials', {k: (v.get('alphaMode', 'OPAQUE'), v['doubleSided'], v.get('extras')) for k, v in mats.items()})
print('VALID LOD triangles', counts, 'bounds', allpos.min(0).round(2).tolist(), allpos.max(0).round(2).tolist(),
      'impostor', pos.min(0).round(2).tolist(), pos.max(0).round(2).tolist())
print('VALID images', [(i['name'], doc['bufferViews'][i['bufferView']]['byteLength']) for i in doc['images']],
      'file bytes', os.path.getsize(out))
# Cards cut to their texture outlines: leaf and clump cards keep 4 vertices (same triangles, ~25-60 % less area the
# alpha test shades), the impostor gets 6. Validated above as authored quads.
cut = os.path.join(WORK, 'cut_' + spec['output'])
subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'cut_foliage_cards.py'), out, cut], check=True)
os.replace(cut, out)
# LOD0 bounds of the installed (cut) file: the engine scales a model so that its LOD0 height is the binding height,
# so every season of a family must share them (family_check.py)
doc, binary = link.read_glb(__import__('pathlib').Path(out))
base = next(n for n in doc['nodes'] if n['name'] == 'Tree')
cutpos = np.concatenate([accessor(p['attributes']['POSITION']) for p in doc['meshes'][base['mesh']]['primitives']])
json.dump({'lod_triangles': counts, 'bounds_min': cutpos.min(0).tolist(), 'bounds_max': cutpos.max(0).tolist(),
           'file_bytes': os.path.getsize(out)}, open(os.path.join(WORK, 'model.json'), 'w'), indent=1)
print('BOUNDS after cut', cutpos.min(0).round(3).tolist(), cutpos.max(0).round(3).tolist())
if '--install' in sys.argv:
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), out, '--engine', '--name',
                    spec['output']], check=True)
    print('INSTALLED', spec['output'])
