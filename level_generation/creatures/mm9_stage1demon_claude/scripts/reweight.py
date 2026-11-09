"""Weight fixes on the UV master (topology untouched).
Pass 2 (2026-10-31, coordinator review: 32 of 144 pieces parted). The first version copied the nearest SKIN vertex onto each
small piece, but most pieces rest on another piece (shards on the skirt shell, talons in the gauntlet flange, the tail's
arrowhead on the shaft, the tongue on the jaw floor), so their roots moved with a different blend than their holder.
Linear blend skinning is linear in the weights, so a vertex that takes the barycentric blend of the weights at its nearest
point on the holder moves exactly with that point. Here every piece but the body skin and the head shell: its vertices in
or within CONTACT of a holder (the faces of all larger components) take the holder's barycentric weights, faded out to
FADE; the rest keep their own weights (talons keep MM9's finger chains, the tongue tip its tongue bones).
Args: <in blend> <out blend>"""
import bpy, bmesh, sys, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
IN, OUT = sys.argv[sys.argv.index('--') + 1:]
CONTACT, FADE = 0.03, 0.08
SMALL = 30
SINK_BELOW, SINK = 60, 0.008
sunk = 0                                 # pieces under SMALL triangles go wholly onto their holder
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data; n = len(me.vertices)
pa = np.zeros(n, int); me.attributes['part'].data.foreach_get('value', pa)
G = len(o.vertex_groups); W = np.zeros((n, G))
for v in me.vertices:
    for g in v.groups: W[v.index, g.group] = g.weight
P = np.array([v.co[:] for v in me.vertices])
F = np.array([p.vertices[:] for p in me.polygons]); assert F.shape[1] == 3
# components welded by position (as the audit sees them)
key = np.round(P / 1e-5).astype(np.int64); _, wid = np.unique(key, axis=0, return_inverse=True); wid = wid.ravel()
par = np.arange(wid.max() + 1)
def find(x):
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
for f in wid[F]:
    a = find(f[0])
    for b in f[1:]:
        b = find(b)
        if a != b: par[b] = a
comp = np.array([find(x) for x in wid]); fc = comp[F[:, 0]]
ids, cnt = np.unique(fc, return_counts=True); order = ids[np.argsort(-cnt)]; size = dict(zip(ids, cnt))
skip = set()
for pid in (0, 10):                        # the body skin and the head shell are holders only
    m = fc[np.isin(F[:, 0], np.nonzero(pa == pid)[0])]
    if len(m): skip.add(int(np.bincount(m).argmax()))
# the palms are limbs, not ornaments: a palm resting in its gauntlet keeps the hand's own weights (taking the gauntlet's
# forearm blend put the hand 5.9 cm into the chest in Death)
hand_g = [g.index for g in o.vertex_groups if g.name in ('Bip01 L Hand', 'Bip01 R Hand')]
for c in order:
    vv = np.unique(F[fc == c])
    if W[vv][:, hand_g].sum(1).mean() > 0.5 or np.bincount(pa[vv]).argmax() == 5: skip.add(int(c))   # palms and talons
Wn = W.copy(); done = 0; moved = 0
for c in order:
    if int(c) in skip: continue
    holder = (fc != c) & np.array([size[x] > size[c] or x in skip for x in fc])
    pc = int(np.bincount(pa[F[fc == c, 0]]).argmax())
    fp = pa[F[:, 0]]; fz = P[F[:, 0], 2]
    if pc == 4:   # the tail's pieces rest on the other tail pieces whatever their size (and the body at the tail root), never on the legs
        holder &= (fp == 4) | ((fp == 0) & (fz > -0.5))
    elif pc == 5: holder &= np.isin(fp, (1, 2, 5))             # talons: palm and gauntlet only
    elif pc >= 10: holder &= np.isin(fp, (10, 12, 13, 14))     # head pieces on the head
    holder = np.nonzero(holder)[0]
    if not len(holder): continue
    tree = BVHTree.FromPolygons([tuple(p) for p in P], [tuple(F[i]) for i in holder])
    vs = np.unique(F[fc == c]); nsum = np.zeros(3); ncnt = 0
    for i in vs:
        loc, nrm, fi, dist = tree.find_nearest(Vector(P[i]))
        if loc is None: continue
        inside = (P[i] - np.array(loc)) @ np.array(nrm) < 0
        d = 0.0 if inside else dist
        w = 1.0 if (d <= CONTACT or (size[c] < SMALL and pc != 4)) else max(0.0, 1 - (d - CONTACT) / (FADE - CONTACT))
        if w <= 0: continue
        if w >= 1: nsum += np.array(nrm); ncnt += 1
        tri = F[holder[fi]]; A, B, C = P[tri]
        v0, v1, v2 = B - A, C - A, np.array(loc) - A
        d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
        den = d00 * d11 - d01 * d01
        bb = (d11 * d20 - d01 * d21) / den if den else 0.0; cc = (d00 * d21 - d01 * d20) / den if den else 0.0
        bary = np.clip(np.array([1 - bb - cc, bb, cc]), 0, 1); bary /= bary.sum()
        hw = bary @ Wn[tri]
        Wn[i] = W[i] * (1 - w) + hw * w; moved += 1
    if size[c] < SINK_BELOW and ncnt:   # small pieces sit 8 mm into their holder (4-influence rounding left 5-10 mm gaps)
        nn = nsum / max(np.linalg.norm(nsum), 1e-9); P[vs] -= nn * SINK; sunk += 1
    done += 1
for v, p in zip(me.vertices, P): v.co = p.tolist()
print('SUNK pieces', sunk)
# neck pass (2026-11-01): the shards at the top of the chest rest on the welded throat, which stretches when MM9 lifts the head
# (Death 110 deg); with holder weights on every vertex they stretched into pale streaks under the jaw, and wholly rigid they
# lifted off it (2-2.7 cm in Death). So their base (within 1 cm of the skin) keeps the holder blend and the rest of the shard
# turns rigidly with its root (the mean holder blend of its five vertices nearest the skin), faded over 1-3 cm.
skf = np.nonzero((pa[F] == 0).all(1))[0]
sktree = BVHTree.FromPolygons([tuple(p) for p in P], [tuple(F[i]) for i in skf]); rigid = 0
for c in order:
    vs = np.unique(F[fc == c]); ctr = P[vs].mean(0)
    if int(c) in skip or int(np.bincount(pa[vs]).argmax()) != 2: continue
    if not (ctr[1] < -0.3 and 0.1 < ctr[2] < 0.6 and abs(ctr[0]) < 0.35): continue
    dd = np.array([sktree.find_nearest(Vector(P[i]))[3] for i in vs]); root = Wn[vs[np.argsort(dd)[:5]]].mean(0)
    wc = np.clip((0.03 - dd) / 0.02, 0, 1)[:, None]
    Wn[vs] = Wn[vs] * wc + root * (1 - wc); rigid += 1
print('RIGID neck shards', rigid)
W = Wn
# 4 influences
order4 = np.argsort(-W, axis=1)
for i in range(n):
    keep = order4[i, :4]; row = np.zeros(G); row[keep] = W[i, keep]; row[row < 0.015] = 0; W[i] = row / max(row.sum(), 1e-9)
for g in o.vertex_groups: g.remove(list(range(n)))
for i, j in zip(*np.nonzero(W)): o.vertex_groups[int(j)].add([int(i)], float(W[i, j]), 'REPLACE')
print('REWEIGHT pieces', done, 'of', len(order), 'vertices on holders', moved)
# the crotch shards (pieces under 20 triangles on the centre line between the thighs) stand across the gap the thighs open:
# no single weighting keeps them seated in Block, DodgeRight and Death (lifted 1.3-4.9 cm), so they go
import bmesh
dead = []
for c in order:
    if size[c] >= 30: continue
    fi = np.nonzero(fc == c)[0]; ctr = P[F[fi]].reshape(-1, 3).mean(0)
    if abs(ctr[0]) < 0.12 and -0.7 < ctr[2] < 0.0 and int(np.bincount(pa[F[fi, 0]]).argmax()) in (1, 2): dead += fi.tolist()
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
dset = set(dead)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.index in dset], context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.to_mesh(me); bm.free()
print('CROTCH shards removed, faces', len(dead))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
