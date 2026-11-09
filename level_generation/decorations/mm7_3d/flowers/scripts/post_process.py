#!/usr/bin/env python3
"""work/<id>/plant_export.glb -> material fix (MASK 0.5, double-sided) -> tools/link_static_model_lods.py ->
tools/cut_foliage_cards.py (cards to their texture outline) -> validation (one node, three LODs, budgets, COLOR_0,
base on the ground) -> work/<id>/mm7_deco_<id>.glb; --install runs tools/install_model.py --engine.
Usage: post_process.py <id> [--install]"""
import os, subprocess, sys
from pathlib import Path
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import REPO, work
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link

SID = sys.argv[1]
WORK = work(SID)
NAME = f'mm7_deco_{SID}.glb'
BUDGET = [1500, 700, 300]
doc, binary = link.read_glb(Path(os.path.join(WORK, 'plant_export.glb')))
for m in doc['materials']:
    m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
linked = os.path.join(WORK, 'linked.glb')
print('LINKED', link.link(doc))
link.write_glb(Path(linked), doc, binary)
out = os.path.join(WORK, NAME)
subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'cut_foliage_cards.py'), linked, out], check=True)
doc, binary = link.read_glb(Path(out))
assert len(doc['materials']) == 1, doc['materials']
m = doc['materials'][0]
assert m['alphaMode'] == 'MASK' and m['alphaCutoff'] == 0.5 and m['doubleSided']
assert m['extras'] == {'openyamm_wind': 0.02, 'openyamm_specular': 0.1, 'openyamm_translucency': 0.3}, m['extras']
assert len(doc['nodes']) == 1 and doc['nodes'][0]['name'] == 'Plant'
base = doc['nodes'][0]
assert not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix')) and 'skins' not in doc
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert len(chain) == 3 and all(c <= b for c, b in zip(counts, BUDGET)) and counts[0] > counts[1] > counts[2], counts
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], 'COLOR_0 missing'
prims = [p for i in chain for p in doc['meshes'][i]['primitives']]
lo = np.min([doc['accessors'][p['attributes']['POSITION']]['min'] for p in prims], 0)
hi = np.max([doc['accessors'][p['attributes']['POSITION']]['max'] for p in prims], 0)
assert abs(lo[1]) < 0.01, lo
size = os.path.getsize(out)
print('VALID', NAME, 'LOD triangles', counts, 'bounds', lo.round(3).tolist(), hi.round(3).tolist(), 'bytes', size)
with open(os.path.join(WORK, 'stats.txt'), 'w') as f:
    f.write(f'{counts[0]} {counts[1]} {counts[2]} {size}\n')
if '--install' in sys.argv:
    subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'install_model.py'), out, '--engine', '--name', NAME],
                   check=True)
    print('INSTALLED', NAME)
