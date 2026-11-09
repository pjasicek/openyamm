"""Labels the step-1 parts, removes the two back studs, cuts the hair at the shoulder blades (MM9's hair ends there and
the wing roots need the back clear) and caps it, shifts the figure in depth so its back lines up with MM9's.
Args: <s1 npz> <out npz>"""
import sys
import numpy as np
IN, OUT = sys.argv[1:3]
D = np.load(IN); co, tri, comp = D['co'].astype(float), D['tri'], D['comp']
c = lambda k: co[comp == k].mean(0)
names = []
lab = np.zeros(len(co), int)
NAMES = ['body', 'hair', 'belt', 'horns', 'fringe', 'emblem', 'eyes', 'ears', 'spikes', 'mouth', 'drop']
def L(k): return NAMES.index(k)
for k in range(comp.max() + 1):
    q = co[comp == k]; m = q.mean(0); n = len(q)
    if k == 0: nm = 'body'
    elif k == 1: nm = 'hair'
    elif n > 200 and m[2] < 0.4: nm = 'belt'
    elif m[2] > 0.98: nm = 'horns'
    elif m[2] > 0.88 and m[1] < -0.04 and abs(m[0]) < 0.01 and n > 60: nm = 'fringe'
    elif m[1] < -0.13 and m[2] < 0.3: nm = 'emblem'
    elif 0.86 < m[2] < 0.92 and m[1] < -0.03 and abs(m[0]) < 0.04: nm = 'eyes'
    elif 0.8 < m[2] < 0.95 and abs(m[0]) > 0.06: nm = 'ears'
    elif 0.6 < m[2] < 0.7 and m[1] < -0.07: nm = 'spikes'
    elif 0.8 < m[2] < 0.84 and abs(m[0]) < 0.01: nm = 'mouth'
    elif m[1] > 0.1 and 0.5 < m[2] < 0.7: nm = 'drop'
    else: raise SystemExit(f'unlabelled part {k} {m} {n}')
    lab[comp == k] = L(nm); print(k, nm, n, m.round(3))
keep_t = lab[tri[:, 0]] != L('drop')
tri = tri[keep_t]
# hair cut: faces whose centroid is below the cut go; the cut line rises 3 cm towards the sides
ZC = 0.60
hair_t = lab[tri[:, 0]] == L('hair')
cen = co[tri].mean(1)
zc = ZC + 0.03 * np.clip(np.abs(cen[:, 0]) / 0.09, 0, 1)
tri = tri[~(hair_t & (cen[:, 2] < zc))]
# clamp: long decimated triangles with a centroid above the cut still dip below it
hv = np.unique(tri[lab[tri[:, 0]] == L('hair')])
zl = ZC + 0.03 * np.clip(np.abs(co[hv, 0]) / 0.09, 0, 1)
low = co[hv, 2] < zl
co[hv[low], 2] = zl[low]; print('hair verts clamped', int(low.sum()))
# keep the largest connected hair piece (strips of the inner layer dangle below the cut otherwise)
hmask = lab[tri[:, 0]] == L('hair'); ht0 = tri[hmask]
par = {}
def fnd(x):
    while par.setdefault(x, x) != x: par[x] = par[par[x]]; x = par[x]
    return x
for t in ht0:
    r0 = fnd(t[0]); par[fnd(t[1])] = r0; par[fnd(t[2])] = r0
rt = np.array([fnd(t[0]) for t in ht0]); uu, cc = np.unique(rt, return_counts=True); big = uu[np.argmax(cc)]
print('hair pieces', sorted(cc)[-5:])
drop = np.zeros(len(tri), bool); drop[np.where(hmask)[0][rt != big]] = True; tri = tri[~drop]
# boundary loops of the hair, capped with a fan to an inset centre
ht = tri[lab[tri[:, 0]] == L('hair')]
e = np.vstack([ht[:, [0, 1]], ht[:, [1, 2]], ht[:, [2, 0]]])
k_ = np.sort(e, 1); u, cnt = np.unique(k_, axis=0, return_counts=True); bset = {tuple(x) for x in u[cnt == 1]}
bed = [tuple(x) for x in e if tuple(sorted(x)) in bset]          # oriented boundary half-edges
nxt = {a: b for a, b in bed}
loops = []; seen = set()
for a, b in bed:
    if a in seen: continue
    loop = [a]; seen.add(a); x = b
    while x != a and x not in seen and x in nxt:
        loop.append(x); seen.add(x); x = nxt[x]
    loops.append(loop)
newv = []; newt = []
co = list(co); lab = list(lab)
for lp in loops:
    p = np.array([co[i] for i in lp])
    if p[:, 2].mean() > 0.75 or len(lp) < 6: print('skip loop', len(lp), p.mean(0).round(3)); continue
    # smooth the cut rim a little (moves rim vertices toward their loop neighbours' mean height)
    for it in range(3):
        z = np.array([co[i][2] for i in lp]); zs = (np.roll(z, 1) + np.roll(z, -1) + 2 * z) / 4
        for i, zz in zip(lp, zs): co[i] = np.array([co[i][0], co[i][1], zz])
    ctr = np.array([co[i] for i in lp]).mean(0) + np.array([0, -0.01, 0.02])
    ci = len(co); co.append(ctr); lab.append(L('hair'))
    for a_, b_ in zip(lp, lp[1:] + lp[:1]): newt.append((b_, a_, ci))
    print('capped hair loop', len(lp), ctr.round(3))
tri = np.vstack([tri, np.array(newt, int).reshape(-1, 3)]) if newt else tri
co = np.array(co); lab = np.array(lab)
# drop unreferenced vertices
used = np.unique(tri); rem = -np.ones(len(co), int); rem[used] = np.arange(len(used))
co, lab, tri = co[used], lab[used], rem[tri]
co[:, 1] += 0.04          # back line onto MM9's (sections at Spine1-2: ours 4-6 cm forward)
np.savez(OUT, co=co, tri=tri, comp=lab, names=np.array(NAMES))
print('ASM', len(co), len(tri), {n: int((lab[tri[:, 0]] == i).sum()) for i, n in enumerate(NAMES)})
