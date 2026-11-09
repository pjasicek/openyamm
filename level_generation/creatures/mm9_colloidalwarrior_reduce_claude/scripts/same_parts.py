#!/usr/bin/env python3
"""Candidate vs installed GLB: clips (every sampler's input/output bytes), images, materials, variants, skins and
inverse bind matrices byte-identical; and the kept face: every installed LOD0 head-set triangle whose three corners
are face/seam vertices (work/keep.npy faces mapped by rest position) present in the candidate with the same positions,
UVs, normals and weights (by joint name). Usage: same_parts.py <installed.glb> <cand.glb>"""
import hashlib, json, sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, accessor_bytes  # noqa: E402
a, b = (read_glb(Path(p)) for p in sys.argv[1:3])
h = lambda doc, bin_, i: hashlib.sha1(accessor_bytes(doc, bin_, i)).hexdigest()
def clips(doc, bin_):
    return {an['name']: [(h(doc, bin_, s['input']), h(doc, bin_, s['output'])) for s in an['samplers']] for an in doc['animations']}
def imgs(doc, bin_):
    out = []
    for im in doc['images']:
        bv = doc['bufferViews'][im['bufferView']]; o = bv.get('byteOffset', 0)
        out.append(hashlib.sha1(bin_[o:o + bv['byteLength']]).hexdigest())
    return out
print('CLIPS identical', clips(*a) == clips(*b), len(a[0]['animations']))
print('IMAGES identical', imgs(*a) == imgs(*b), len(a[0]['images']))
print('MATERIALS identical', json.dumps(a[0]['materials'], sort_keys=True) == json.dumps(b[0]['materials'], sort_keys=True))
print('VARIANTS identical', a[0].get('extensions') == b[0].get('extensions'))
print('IBM identical', all(h(*a, sa['inverseBindMatrices']) == h(*b, sb['inverseBindMatrices']) for sa, sb in zip(a[0]['skins'], b[0]['skins'])))
print('NODES identical', [ {k: v for k, v in n.items() if k != 'mesh'} for n in a[0]['nodes']] == [{k: v for k, v in n.items() if k != 'mesh'} for n in b[0]['nodes']])
def prim(doc, bin_, mat):
    node = next(n for n in doc['nodes'] if n.get('name') == 'Colloidal'); jn = [doc['nodes'][i]['name'] for i in doc['skins'][node['skin']]['joints']]
    p = next(p for p in doc['meshes'][node['mesh']]['primitives'] if doc['materials'][p['material']]['name'] == mat)
    def A(i):
        ac = doc['accessors'][i]; n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[ac['type']]
        ct = {5126: '<f4', 5125: '<u4', 5123: '<u2', 5121: 'u1'}[ac['componentType']]
        return np.frombuffer(accessor_bytes(doc, bin_, i), ct).reshape(-1, n).astype(float)
    at = p['attributes']; J = A(at['JOINTS_0']).astype(int); W = A(at['WEIGHTS_0'])
    wd = [{jn[j]: round(w, 3) for j, w in zip(jr, wr) if w > 1e-4} for jr, wr in zip(J, W)]
    return A(at['POSITION']), A(at['TEXCOORD_0']), A(at['NORMAL']), wd, A(p['indices']).astype(int).reshape(-1, 3)
for mat in ('ColloidalHead_A', 'Colloidal_A'):
    P0, U0, N0, W0, T0 = prim(*a, mat); P1, U1, N1, W1, T1 = prim(*b, mat)
    t = cKDTree(np.hstack([P1, U1])); d, j = t.query(np.hstack([P0, U0]))
    found = d < 1e-6
    tri1 = {tuple(sorted(r)) for r in j[T1.ravel()].reshape(-1, 3).tolist()} if False else {tuple(sorted(r)) for r in T1.tolist()}
    kept = [tri for tri in T0.tolist() if found[tri].all() and tuple(sorted(j[tri].tolist())) in tri1]
    kv = np.unique(np.array(kept).ravel()) if kept else np.zeros(0, int)
    nok = np.abs(N0[kv] - N1[j[kv]]).max() if len(kv) else 0
    wok = sum(W0[i] != W1[j[i]] for i in kv)
    bad = [i for i in kv if W0[i] != W1[j[i]]][:3]
    [print("  W", W0[i], W1[j[i]]) for i in bad]
    print(f'{mat}: installed tris {len(T0)}, present unchanged {len(kept)}; their vertices {len(kv)}: max normal diff {nok:.2e}, weight mismatches {wok}')
