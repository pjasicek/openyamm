#!/usr/bin/env python3
"""Leftovers copy of the outdoor flowers' post_process.py: work/plants/<id>/plant_export.glb -> material fix (MASK
0.5, double-sided) -> tools/cut_foliage_cards.py -> work/plants/<id>/plant_cut.glb (unlinked; the batch's finish.py
links and installs it), validated on a linked copy (one material with the flower extras, one node, three decreasing
LODs within the budget, COLOR_0 everywhere, base on the ground). Usage: post_process.py <id>"""
import os, subprocess, sys
from pathlib import Path
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link
SID = sys.argv[1]
WORK = os.path.join(HERE, 'work', 'plants', SID)
BUDGET = [1500, 600, 200]
doc, binary = link.read_glb(Path(os.path.join(WORK, 'plant_export.glb')))
for m in doc['materials']:
    m['alphaMode'] = 'MASK'; m['alphaCutoff'] = 0.5; m['doubleSided'] = True
fixed = os.path.join(WORK, 'plant_fixed.glb'); cut = os.path.join(WORK, 'plant_cut.glb')
link.write_glb(Path(fixed), doc, binary)
subprocess.run([sys.executable, os.path.join(REPO, 'tools', 'cut_foliage_cards.py'), fixed, cut], check=True)
doc, binary = link.read_glb(Path(cut))
print('LINKED', link.link(doc))
assert len(doc['materials']) == 1, doc['materials']
m = doc['materials'][0]
assert m['alphaMode'] == 'MASK' and m['alphaCutoff'] == 0.5 and m['doubleSided']
assert m['extras'] == {'openyamm_wind': 0.02, 'openyamm_specular': 0.1, 'openyamm_translucency': 0.3}, m['extras']
assert len(doc['nodes']) == 1 and doc['nodes'][0]['name'] == 'Plant'
base = doc['nodes'][0]
assert not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix'))
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert len(chain) == 3 and all(c <= b for c, b in zip(counts, BUDGET)) and counts[0] > counts[1] > counts[2], counts
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], 'COLOR_0 missing'
lo = np.min([doc['accessors'][p['attributes']['POSITION']]['min'] for i in chain for p in doc['meshes'][i]['primitives']], 0)
hi = np.max([doc['accessors'][p['attributes']['POSITION']]['max'] for i in chain for p in doc['meshes'][i]['primitives']], 0)
assert abs(lo[1]) < 0.01, lo
print('VALID', SID, 'LOD triangles', counts, 'bounds', lo.round(3).tolist(), hi.round(3).tolist(), 'cut', cut)
