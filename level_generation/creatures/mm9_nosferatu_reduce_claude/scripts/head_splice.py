#!/usr/bin/env python3
"""Candidate GLB (LODs rebuilt by tools/build_actor_lods.py) -> the same file with the NosferatuHead primitive of LOD1-3
taken from the installed GLB byte for byte (Blender's LOD decimation is not bit-reproducible; the head set must not change
anywhere). LOD0's head is already the installed bytes (swap_inst.py leaves it). Prints whether the rebuilt heads differed.
Usage: head_splice.py <installed.glb> <candidate.glb> <out.glb>"""
import copy, hashlib, sys
import numpy as np
import glbpack as G

I, ib = G.read(sys.argv[1]); C, cb = G.read(sys.argv[2])
h = lambda doc, b, i: hashlib.sha1(bytes(G.raw_rows(doc, b, i))).hexdigest()
iname = {m['name']: k for k, m in enumerate(I['meshes'])}
cmat = [m['name'] for m in C['materials']]; imat = [m['name'] for m in I['materials']]
assert cmat == imat
for m in C['meshes']:
    if not m['name'].startswith('Nosferatu_LOD') or m['name'].endswith('Shadow'):
        continue
    mi = I['meshes'][iname[m['name']]]
    for k, p in enumerate(m['primitives']):
        if not cmat[p['material']].startswith('NosferatuHead'):
            continue
        pi = next(q for q in mi['primitives'] if q['material'] == p['material'])
        same = h(C, cb, p['indices']) == h(I, ib, pi['indices']) and all(
            h(C, cb, p['attributes'][s]) == h(I, ib, pi['attributes'][s]) for s in pi['attributes'])
        q = copy.deepcopy(pi)
        q['attributes'] = {s: G.append(C, cb, I['accessors'][v], G.raw_rows(I, ib, v)) for s, v in pi['attributes'].items()}
        for s, v in q['attributes'].items():
            G.set_minmax(C, cb, v)
        q['indices'] = G.append(C, cb, I['accessors'][pi['indices']], G.raw_rows(I, ib, pi['indices']))
        m['primitives'][k] = q
        print('HEAD', m['name'], 'rebuilt head identical' if same else 'rebuilt head differed: installed bytes restored',
              I['accessors'][pi['indices']]['count'] // 3, 'tris')
C, cb = G.compact(C, cb)
G.write(sys.argv[3], C, cb)
