"""Braids out of the chest (female Honk, night pass 2, 2026-10-31). hair_gate.py found the two braids and the two short strands crossing the robe in every frame of
every clip, Standing included: in the rest pose they run into the chest from about 1.53 m and the tips come back out through the trim as small orange shards. Damping
cannot fix that, so:
- rest shape: each strand is cut into height bands and every band slides out over the chest by the same vector, enough to clear the cloth by `clear`, then
  smoothed along the strand, so it curves rather than squashes;
- weights: from `top` down to `low` metres above the floor the strand's weights blend to those of the cloth under it, and below `low` it moves with that cloth, so
  the tips ride the chest in every clip instead of swinging through it (a single chest bone failed: when she bows, the tips swing back into the belly).
Args (Blender): <in blend> <out blend> <report json> [clear=0.012 top=1.56 low=1.44 chest=Bip01 Spine2 band=0.008]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = a[:3]
opt = dict(x.split('=', 1) for x in a[3:])
CLEAR = float(opt.get('clear', 0.012)); TOP = float(opt.get('top', 1.56)); LOW = float(opt.get('low', 1.44)); BAND = float(opt.get('band', 0.008))
CHEST = opt.get('chest', 'Bip01 Spine2')
bpy.ops.wm.open_mainfile(filepath=IN)
b = bpy.data.objects['Body']; rig = b.parent
for p in rig.pose.bones:
    p.matrix_basis.identity()
bpy.context.view_layer.update()
me = b.data; M = b.matrix_world; Mi = M.inverted()
names = [g.name for g in b.vertex_groups]; gi = {n: i for i, n in enumerate(names)}
floor = min((M @ v.co).z for v in me.vertices)
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
dl = bm.verts.layers.deform.active
lh, lk = bm.faces.layers.int['head'], bm.faces.layers.int['hand']
seen, parts = set(), []
for v in bm.verts:
    if v in seen:
        continue
    st, cur = [v], []; seen.add(v)
    while st:
        x = st.pop(); cur.append(x)
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen:
                seen.add(y); st.append(y)
    parts.append(cur)


def hair_share(p):
    return sum(w for v in p for g, w in v[dl].items() if 'Ponytail' in names[g] or names[g].startswith('Y')) / len(p)


# strands: thin loose hair parts in front of the shoulders, reaching the chest (not the veil, which hangs behind)
strands = []
for p in parts:
    if hair_share(p) < 0.1 or not 30 < len(p) < 320:
        continue
    co = np.array([tuple(M @ v.co) for v in p])
    if co[:, 2].min() - floor > 1.46 or co[:, 1].mean() > 0.02:      # front is -y
        continue
    strands.append(p)
partof = {v: i for i, p in enumerate(strands) for v in p}
cloth = [f for f in bm.faces if not f[lk] and f.verts[0] not in partof and hair_share([f.verts[0]]) < 0.3 and not f[lh]]
cv = [M @ v.co for v in bm.verts]
idx = {v: i for i, v in enumerate(bm.verts)}
bvh = BVHTree.FromPolygons(cv, [[idx[v] for v in f.verts] for f in cloth])
rep = {'strands': [], 'cloth_faces': len(cloth)}
for p in strands:
    co = np.array([tuple(M @ v.co) for v in p])
    z = co[:, 2]
    lo, hi = z.min(), z.max()
    bands = ((z - lo) / BAND).astype(int)
    nb = bands.max() + 1
    D = np.zeros((nb, 3))
    worst = 0.0
    for it in range(4):
        need = np.zeros(nb); dirn = np.zeros((nb, 3))
        for v, c, k in zip(p, co, bands):
            q = Vector(c) + Vector(D[k])
            loc, n, _, d = bvh.find_nearest(q, 0.3)
            if loc is None:
                continue
            s = (q - loc).dot(n)
            lack = CLEAR - s
            if lack > need[k]:
                need[k] = lack; dirn[k] = np.array(n)
        worst = max(worst, float(need.max()))
        step = dirn * need[:, None]
        # hold the largest move through the neighbouring bands, then a Gaussian along the strand
        for _ in range(3):
            step = np.vstack([step[:1], (step[:-2] + 2 * step[1:-1] + step[2:]) / 4, step[-1:]])
        D += step * 1.2
    for _ in range(4):
        D = np.vstack([D[:1], (D[:-2] + 2 * D[1:-1] + D[2:]) / 4, D[-1:]])
    # nothing moves at the top of the strand
    fade = np.clip((hi - (lo + (np.arange(nb) + .5) * BAND)) / 0.06, 0, 1)
    D *= (fade * fade * (3 - 2 * fade))[:, None]
    for v, c, k in zip(p, co, bands):
        v.co = Mi @ Vector(c + D[k])
    # weights
    ch = gi[CHEST]
    for v, c in zip(p, co):
        h = c[2] - floor
        t = np.clip((TOP - h) / (TOP - LOW), 0, 1); t = float(t * t * (3 - 2 * t))
        if t <= 0:
            continue
        # the weights of the cloth under the strand: it moves with the surface it lies on, so no clip can carry it through (a single chest bone cannot: when she bows
        # the tips swing back into the belly)
        q = Vector(c + D[k])
        loc, _, fi, _ = bvh.find_nearest(q, 0.5)
        w = {g: x * (1 - t) for g, x in v[dl].items()}
        if loc is None:
            w[ch] = w.get(ch, 0.0) + t
        else:
            fv = cloth[fi].verts
            d_ = [max((M @ u.co - loc).length, 1e-4) for u in fv]
            inv_ = [1 / x for x in d_]
            tot_ = sum(inv_)
            for u, bw in zip(fv, inv_):
                for g, x in u[dl].items():
                    w[g] = w.get(g, 0.0) + t * x * bw / tot_
        top4 = sorted(w.items(), key=lambda kv: -kv[1])[:4]
        tot = sum(x for _, x in top4)
        for g in list(v[dl].keys()):
            del v[dl][g]
        for g, x in top4:
            v[dl][g] = x / tot
    rep['strands'].append({'verts': len(p), 'height': [round(lo - floor, 3), round(hi - floor, 3)], 'worst_need_cm': round(worst * 100, 1), 'moved_cm': round(float(np.linalg.norm(D, axis=1).max()) * 100, 1)})
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('BRAID_FIX', json.dumps(rep))
json.dump(rep, open(REP, 'w'), indent=1)
