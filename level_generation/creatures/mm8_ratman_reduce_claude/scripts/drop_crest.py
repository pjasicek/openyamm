#!/usr/bin/env python3
"""Remove the crest of fur flaps that stands up behind and above the Ratman's skull (user review 4: "on top of his
head behind these fur strips ... we can just remove them if it causes this black area").

The crest is part of the vest's fur collar and loose tufts (body texture set, pieces other than the body skin) that
the source model wraps up around the back of the head; in the installed ready pose the head hung forward out of it,
since the head lift (lift_neck_clips.py) it stands above the head with the dark gap to the skull showing. Faces of
those pieces whose centroid lies above CREST_Y (rest pose, glTF Y up, metres) or that ride the head (mean B_Head
weight above CREST_HEAD) are dropped; vertices are kept (unused ones are harmless and are compacted by the LOD
build). Run it on the full-detail file after reweight_head.py. Usage: drop_crest.py <in.glb> <out.glb>"""
import os
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / 'tools'))
from build_actor_lods import read_glb, write_glb, accessor_bytes, append_accessor  # noqa: E402

CREST_Y = float(os.environ.get('CREST_Y', '1.55'))
CREST_HEAD = float(os.environ.get('CREST_HEAD', '0.5'))
HEAD_U = 1056 / 2080
src, dst = Path(sys.argv[1]), Path(sys.argv[2])
doc, binary = read_glb(src); binary = bytearray(binary)
N = doc['nodes']
CT = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read(i):
    a = doc['accessors'][i]
    arr = np.frombuffer(accessor_bytes(doc, binary, i), CT[a['componentType']]).reshape(a['count'], NC[a['type']])
    return arr.astype(np.float64) / np.iinfo(CT[a['componentType']]).max if a.get('normalized') else arr.astype(np.float64)


HEAD = [N[j]['name'] for j in doc['skins'][0]['joints']].index('B_Head')
for m in doc['meshes']:
    if not any('skin' in n and n.get('mesh') == doc['meshes'].index(m) for n in N):
        continue
    for p in m['primitives']:
        at = p['attributes']
        pos = read(at['POSITION']); tri = read(p['indices']).astype(int).reshape(-1, 3)
        hw = (read(at['WEIGHTS_0']) * (read(at['JOINTS_0']).astype(int) == HEAD)).sum(1)
        body = ~(read(at['TEXCOORD_0'])[:, 0] > HEAD_U)[tri].any(1)
        _, weld = np.unique(np.round(pos / 1e-6).astype(np.int64), axis=0, return_inverse=True); weld = weld.ravel()
        e = weld[np.concatenate([tri[:, [0, 1]], tri[:, [1, 2]], tri[:, [2, 0]]])]; n = weld.max() + 1
        _, lab = connected_components(coo_matrix((np.ones(len(e)), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
        piece = lab[weld][tri[:, 0]]
        skin = np.argmax(np.bincount(piece[body], minlength=lab.max() + 1))
        drop = body & (piece != skin) & ((pos[tri].mean(1)[:, 1] > CREST_Y) | (hw[tri].mean(1) > CREST_HEAD))
        keep = tri[~drop]
        ia = doc['accessors'][p['indices']]
        p['indices'] = append_accessor(doc, binary, dict(ia, count=keep.size), keep.astype(CT[ia['componentType']]).tobytes())
        print('CREST', m['name'], f'{int(drop.sum())} of {len(tri)} faces dropped ({len(np.unique(piece[drop]))} pieces)')
write_glb(dst, doc, bytes(binary))
