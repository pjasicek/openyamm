#!/usr/bin/env python3
"""work/<id>/plant_export.glb -> material fix (MASK 0.5, double-sided) -> tools/link_static_model_lods.py ->
tools/cut_foliage_cards.py (foliage cards to their texture outline) -> validation -> [--install] into
assets_dev/worlds/mm6/models/mm6_deco_flower02.glb / mm6_deco_flower07.glb. Usage: post_process.py <id> [--install]"""
import json, os, subprocess, sys
from pathlib import Path
import numpy as np
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
sys.path.insert(0, os.path.join(REPO, 'tools'))
import link_static_model_lods as link
SID = sys.argv[1]
WORK = os.path.join(HERE, 'work', SID)
NAME = {'6flower02': 'mm6_deco_flower02.glb', '6flower07': 'mm6_deco_flower07.glb',
        '6flower06': 'mm6_deco_flower06.glb', '6flower08': 'mm6_deco_flower08.glb'}[SID]
DEST = os.path.join(REPO, 'assets_dev', 'worlds', 'mm6', 'models', NAME)
# The rose bush and the sunflower clump are 1-1.6 m mounds (the gazania and crocus about 0.3 m) and rare.
BUDGET = {'6flower06': [2200, 700, 260], '6flower08': [1600, 600, 220]}.get(SID, [1500, 600, 200])
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
assert not any(k in base for k in ('translation', 'rotation', 'scale', 'matrix')) and 'skins' not in doc and 'animations' not in doc
chain = [base['mesh']] + doc['meshes'][base['mesh']]['extras']['openyamm_lods']
counts = [sum(doc['accessors'][p['indices']]['count'] // 3 for p in doc['meshes'][i]['primitives']) for i in chain]
assert len(chain) == 3 and all(c <= b for c, b in zip(counts, BUDGET)) and counts[0] > counts[1] > counts[2], counts
for i in chain:
    for p in doc['meshes'][i]['primitives']:
        assert 'COLOR_0' in p['attributes'], 'COLOR_0 missing'
lo = np.min([doc['accessors'][p['attributes']['POSITION']]['min'] for i in chain for p in doc['meshes'][i]['primitives']], 0)
hi = np.max([doc['accessors'][p['attributes']['POSITION']]['max'] for i in chain for p in doc['meshes'][i]['primitives']], 0)
assert abs(lo[1]) < 0.01, lo
print('VALID', NAME, 'LOD triangles', counts, 'bounds', lo.round(3).tolist(), hi.round(3).tolist(), 'bytes', os.path.getsize(out))
if '--install' in sys.argv:
    subprocess.run(['install', '-m', '0664', out, DEST], check=True)
    print('INSTALLED', DEST)
