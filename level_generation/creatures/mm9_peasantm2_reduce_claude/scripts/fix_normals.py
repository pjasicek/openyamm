#!/usr/bin/env python3
"""LOD0 normals of the reduced Highwayman. Its own export (export_hw.py) took Blender's smooth vertex normals of the welded
master, which is what the candidate export writes for new vertices too; every candidate vertex that is a source vertex
(same primitive, position and UV within 1e-5) takes the installed normal byte for byte, so the kept face skin, neck and
eyes shade exactly as installed. The HwWeapon_A primitive (kept whole) is restored from the installed file byte for byte.
Joints and indices are re-encoded like the installed primitives (build_actor_lods merges the shadow primitives and needs
every primitive alike). Usage: fix_normals.py <source.glb> <in.glb> <out.glb>"""
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / 'scripts'))
import glbio  # noqa: E402
KEEP = []
src, inp, out = (Path(a) for a in sys.argv[1:4])
sdoc, sbin, snd, S = glbio.load(src, 'Thrall'); doc, binary, nd, C = glbio.load(inp, 'Thrall'); binary = bytearray(binary)
CT = {5121: '<u1', 5123: '<u2', 5125: '<u4'}
for name, c in C.items():
    if name in KEEP:
        continue
    s = S[name]; N = c['N'].copy()
    hits = cKDTree(s['P']).query_ball_point(c['P'], 1e-5); copied = 0
    for i, h in enumerate(hits):
        h = [j for j in h if np.abs(s['UV'][j] - c['UV'][i]).max() < 1e-5]
        if h:
            j = max(h, key=lambda j: float(s['N'][j] @ N[i])); N[i] = s['N'][j]; copied += 1
    acc = doc['accessors'][c['prim']['attributes']['NORMAL']]
    c['prim']['attributes']['NORMAL'] = glbio.append_accessor(doc, binary, acc, N.astype('<f4').tobytes())
    sj = sdoc['accessors'][s['prim']['attributes']['JOINTS_0']]['componentType']
    si = sdoc['accessors'][s['prim']['indices']]['componentType']
    assert c['J'].max() < (256 if sj == 5121 else 65536) and c['T'].max() < (65536 if si == 5123 else 2 ** 32)
    ja = dict(doc['accessors'][c['prim']['attributes']['JOINTS_0']], componentType=sj)
    c['prim']['attributes']['JOINTS_0'] = glbio.append_accessor(doc, binary, ja, c['J'].astype(CT[sj]).tobytes())
    ia = dict(doc['accessors'][c['prim']['indices']], componentType=si)
    c['prim']['indices'] = glbio.append_accessor(doc, binary, ia, c['T'].reshape(-1).astype(CT[si]).tobytes())
    print('NORMALS', name, 'vertices', len(N), 'installed normal kept', copied, 'export normal', len(N) - copied, 'tris', len(c['T']))
for name in KEEP:
    sp, cp = S[name]['prim'], C[name]['prim']
    assert len(S[name]['T']) - len(C[name]['T']) in range(0, 30), f'{name} was not kept whole'
    cp['attributes'] = {k: glbio.append_accessor(doc, binary, sdoc['accessors'][i], glbio.accessor_bytes(sdoc, sbin, i))
                        for k, i in sp['attributes'].items()}
    cp['indices'] = glbio.append_accessor(doc, binary, sdoc['accessors'][sp['indices']], glbio.accessor_bytes(sdoc, sbin, sp['indices']))
    print('KEPT PRIMITIVE', name, 'installed bytes,', len(S[name]['T']), 'triangles')
glbio.write_glb(out, doc, bytes(binary))
