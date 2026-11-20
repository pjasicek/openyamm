"""One subdivision level on the face (front of the head skin, eyes, mouth), after merge.py: the decimated face read
faceted at full size. New edge points by Loop's edge rule on the welded surface (UV-split copies share a position),
UVs and weights interpolated, so the paid paint stays valid; neighbour faces with one or two split edges are split too
(no T-junctions). Original vertices do not move. Args: <mesh npz> <out npz>"""
import sys
import numpy as np
IN, OUT = sys.argv[1:3]
D = dict(np.load(IN)); co, tri, uv, mat, W, comp, orig = D['co'], D['tri'], D['uv'], D['mat'], D['W'], D['comp'], D['orig']
matnames = [str(x) for x in D['matnames']]
key = np.where(orig >= 0, orig, -1 - np.arange(len(orig)) - 10 ** 7)        # weld body copies by asm index
c = co[tri].mean(1)
HEADPARTS = {0, 6, 9}                     # body, eyes, mouth (assemble.py NAMES)
sel = (mat == matnames.index('EboraHead')) & np.isin(comp[tri[:, 0]], list(HEADPARTS)) & (c[:, 1] < 0.040) & (c[:, 2] > 0.775) & (c[:, 2] < 0.97)
print('faces selected', int(sel.sum()))
K = key[tri]
def ek(a, b): return (a, b) if a < b else (b, a)
# welded edge -> opposite welded vertices (all faces)
opp = {}
for f in range(len(tri)):
    for i in range(3):
        a, b, o = K[f, i], K[f, (i + 1) % 3], K[f, (i + 2) % 3]
        opp.setdefault(ek(a, b), []).append((o, f))
pos_of = {}
for i, k in enumerate(key): pos_of.setdefault(int(k), i)
split = set()
for f in np.where(sel)[0]:
    for i in range(3): split.add(ek(K[f, i], K[f, (i + 1) % 3]))
edge_pos = {}
for e in split:
    a, b = co[pos_of[e[0]]], co[pos_of[e[1]]]
    os_ = opp[e]
    if len(os_) == 2 and all(sel[f] for _, f in os_):
        p = 0.375 * (a + b) + 0.125 * (co[pos_of[os_[0][0]]] + co[pos_of[os_[1][0]]])
    else:
        p = 0.5 * (a + b)
    edge_pos[e] = p
co = list(co); uv = list(uv); W = list(W); comp = list(comp); orig = list(orig); key = list(key)
mid = {}
def midv(va, vb):
    k_ = (min(va, vb), max(va, vb))
    if k_ not in mid:
        e = ek(key[va], key[vb])
        mid[k_] = len(co); co.append(edge_pos[e]); uv.append((uv[va] + uv[vb]) / 2); W.append((W[va] + W[vb]) / 2)
        comp.append(comp[va]); orig.append(-5 * 10 ** 6 - len(mid)); key.append(-5 * 10 ** 6 - len(mid))
    return mid[k_]
nt = []; nm = []
for f, t in enumerate(tri):
    s = [ek(key[t[i]], key[t[(i + 1) % 3]]) in split for i in range(3)]
    n = sum(s)
    if n == 0: nt.append(t); nm.append(mat[f]); continue
    if n == 3:
        a, b, cc = t; ab, bc, ca = midv(a, b), midv(b, cc), midv(cc, a)
        out = [(a, ab, ca), (ab, b, bc), (ca, bc, cc), (ab, bc, ca)]
    else:
        r = [i for i in range(3) if s[i]]
        if n == 1:
            i = r[0]; a, b, cc = t[i], t[(i + 1) % 3], t[(i + 2) % 3]; m = midv(a, b)
            out = [(a, m, cc), (m, b, cc)]
        else:
            i = [k for k in range(3) if not s[k]][0]        # unsplit edge i: (t[i], t[i+1])
            a, b, cc = t[i], t[(i + 1) % 3], t[(i + 2) % 3]
            mbc, mca = midv(b, cc), midv(cc, a)
            out = [(a, b, mbc), (a, mbc, mca), (mca, mbc, cc)]
    nt += out; nm += [mat[f]] * len(out)
D.update(co=np.array(co), tri=np.array(nt), uv=np.array(uv), W=np.array(W, np.float32), comp=np.array(comp), orig=np.array(orig), mat=np.array(nm))
np.savez(OUT, **D)
print('SUBDIV', len(tri), '->', len(nt), 'faces')
