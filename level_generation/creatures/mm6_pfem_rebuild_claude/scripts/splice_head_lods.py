#!/usr/bin/env python3
"""Follow-up 4: put the head primitive's new LOD1-3 (from tools/build_actor_lods.py run on the fixed level zero) into the fixed GLB,
keeping the installed body LOD primitives byte for byte, and rebuild the four merged shadow meshes from the new LOD primitives
(shrink_shadow_lods.py and fix_winding.py run after this, as in build_runtime.sh).
Usage: splice_head_lods.py <fixed glb (LOD0 changed)> <lods glb from build_actor_lods> <out glb>"""
import sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts')); sys.path.insert(0, str(HERE.parents[2] / 'tools'))
from glbio import Glb, CT, NC  # noqa: E402
from build_actor_lods import merge_shadow  # noqa: E402

g, L = Glb(sys.argv[1]), Glb(sys.argv[2])
HEADMAT = next(i for i, m in enumerate(g.j['materials']) if m['name'] == 'PeasantHead')
lods_g = g.j['meshes'][0]['extras']['openyamm_lods']; shad_g = g.j['meshes'][0]['extras']['openyamm_shadow_lods']
lods_L = L.j['meshes'][0]['extras']['openyamm_lods']


def copy_acc(i):
    a = L.j['accessors'][i]
    arr = L.acc(i)
    return g.add(arr, a['componentType'], a['type'], 34963 if a['type'] == 'SCALAR' else 34962)


counts = {}
for lg, ll in zip(lods_g, lods_L):
    pl = next(p for p in L.j['meshes'][ll]['primitives'] if p['material'] == HEADMAT)
    k = next(i for i, p in enumerate(g.j['meshes'][lg]['primitives']) if p['material'] == HEADMAT)
    newp = {'attributes': {s: copy_acc(i) for s, i in pl['attributes'].items()}, 'indices': copy_acc(pl['indices']), 'material': HEADMAT}
    if 'mode' in g.j['meshes'][lg]['primitives'][k]: newp['mode'] = g.j['meshes'][lg]['primitives'][k]['mode']
    g.j['meshes'][lg]['primitives'][k] = newp
    counts[g.j['meshes'][lg]['name']] = L.j['accessors'][pl['indices']]['count'] // 3
# shadows: merged again from the level's colour primitives (merge_shadow appends to a document/binary pair)
while len(g.bin) % 4: g.bin.append(0)
for src, dst in zip([0] + lods_g, shad_g):
    sh = merge_shadow(g.j, g.bin, g.j['meshes'][src])
    old = g.j['meshes'][dst]; sh['name'] = old['name']
    if 'extras' in old: sh['extras'] = old['extras']
    for k in ('material', 'extensions', 'mode'):                # tier material and its KHR_materials_variants mapping
        if k in old['primitives'][0]: sh['primitives'][0][k] = old['primitives'][0][k]
    g.j['meshes'][dst] = sh
g.compact(); g.save(sys.argv[3])
print('SPLICED head LOD triangles', counts)
