"""Arm weight repair of the installed dwarf (work/source.blend, original kept as work/source_orig.blend).
The Codex shirt keeps 15-60 % Spine/Spine1/Pelvis weight on the sleeve, so the raised arm leaves the sleeve flaring
behind it, and the separate elbow skin piece is rigid on UpperArm while the sleeve and the forearm piece use the twist
bones. In the rest pose the inner half of the sleeve lies against the torso side, and the original weights run as a
continuum from the outer sleeve (about 80 % arm) to the torso under the armpit, so a hard sleeve/torso split tears
that web (review round 2). Per arm:
1. shirt: blend factor b (0 = original weights, 1 = their arm part only: Clavicle/UpperArm/UpperArmTwist,
   renormalised) as a harmonic field over the shirt's edges, fixed at 1 on the outer half of the sleeve near the hem
   (s > S_HEM along the shoulder->elbow axis, lateral of the arm axis) and at 0 on the torso (|x| < 0.13 m or s < 0.1);
2. small pieces sitting on the repaired shirt (not on the yoke above it: studs) move rigidly with the shirt vertex nearest their centre (per-vertex
   copies split a yoke stud in Death);
3. elbow skin piece: UpperArm weight moves to UpperArmTwist (it rolls with the sleeve); its bottom rim copies the
   forearm piece under the bracer, fading into its own elbow weights 1-5 cm from that rim.
Writes work/arm_blend.npy (blend factor per vertex). Usage: blender -b -P fix_arm_weights.py   (REA_S_HEM, default 0.45)"""
import os, shutil, bmesh, bpy, numpy as np
from mathutils import kdtree
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, ORIG = os.path.join(HERE, 'work/source.blend'), os.path.join(HERE, 'work/source_orig.blend')
S_HEM = float(os.environ.get('REA_S_HEM', '0.45'))
if not os.path.exists(ORIG):
    shutil.copy(SRC, ORIG)
bpy.ops.wm.open_mainfile(filepath=ORIG)
o = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = o.data
gname = {g.index: g.name for g in o.vertex_groups}; gidx = {g.name: g.index for g in o.vertex_groups}
co = np.array([v.co[:] for v in me.vertices])
W = [{gname[g.group]: g.weight for g in v.groups if gname[g.group] != 'ReduceProtect' and g.weight > 0} for v in me.vertices]
bm = bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
edges = np.array([[e.verts[0].index, e.verts[1].index] for e in bm.edges])
boundary = np.array([v.is_boundary for v in bm.verts]); bm.free()
p = list(range(len(co)))


def find(i):
    while p[i] != i:
        p[i] = p[p[i]]; i = p[i]
    return i


for a, b in edges:
    ra, rb = find(a), find(b)
    if ra != rb:
        p[ra] = rb
pc = np.array([find(i) for i in range(len(co))]); size = np.bincount(pc, minlength=len(co))


def norm(w):
    t = sum(w.values()); return {k: x / t for k, x in w.items()} if t > 0 else w


def lerp(a, b, t):
    return norm({k: (1 - t) * a.get(k, 0) + t * b.get(k, 0) for k in set(a) | set(b)})


def smooth(x, e0, e1):
    t = np.clip((x - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t)


def tree(ids):
    t = kdtree.KDTree(len(ids))
    for j in ids:
        t.insert(co[j], int(j))
    t.balance(); return t


def piece_at(x, z, lo, hi):
    ks = [k for k in np.unique(pc) if lo < size[k] < hi and abs(co[pc == k].mean(0)[0] - x) < .04
          and abs(co[pc == k].mean(0)[2] - z) < .04]
    assert len(ks) == 1, ks
    return ks[0]


new = list(W); blend = np.zeros(len(co))
shirt = piece_at(0, .9, 400, 500)           # green shirt with both sleeves (442 vertices, z 0.74-1.07)
report = {}
for side, sx in (('R', -1), ('L', 1)):
    head = np.array(rig.matrix_world @ rig.data.bones[f'B_{side}_UpperArm'].head_local)
    elbow_j = np.array(rig.matrix_world @ rig.data.bones[f'B_{side}_Forearm'].head_local)
    axis = elbow_j - head; L = np.linalg.norm(axis); axis /= L
    d = co - head; s = d @ axis / L
    lat = (d - np.outer(d @ axis, axis)) @ np.array([sx, 0, 0])      # + = away from the body
    arm = (f'B_{side}_Clavicle', f'B_{side}_UpperArm', f'B_{side}_UpperArmTwist')
    # 1. harmonic blend factor over this side of the shirt
    region = np.flatnonzero((pc == shirt) & (co[:, 0] * sx > .05))
    fix1 = (s > S_HEM) & (lat > -.02)
    fix0 = (np.abs(co[:, 0]) < .13) | (s < .1)
    bfac = np.where(fix1, 1.0, 0.0)
    free = [i for i in region if not fix1[i] and not fix0[i]]
    inr = np.zeros(len(co), bool); inr[region] = True
    nb = {i: [] for i in region}
    for a, b in edges:
        if inr[a] and inr[b]:
            nb[a].append(b); nb[b].append(a)
    for _ in range(3000):                    # Jacobi iterations of the graph Laplacian
        upd = {i: np.mean(bfac[nb[i]]) for i in free if nb[i]}
        for i, x in upd.items():
            bfac[i] = x
    for i in region:
        if bfac[i] > 1e-3:
            armw = norm({k: x for k, x in W[i].items() if k in arm})
            if armw:
                new[i] = lerp(W[i], armw, float(bfac[i]))
    # 2. studs on the sleeve
    st = tree(region); studs = 0
    host = tree(np.flatnonzero(size[pc] > 40))       # the surface a stud sits on (shirt, yoke, belt ...)
    for k in np.unique(pc[co[:, 0] * sx > .1]):
        ids = np.flatnonzero(pc == k)
        if size[k] > 40 or pc[host.find(co[ids].mean(0))[1]] != shirt:
            continue
        c, j, dist = st.find(co[ids].mean(0))
        if dist < .02 and bfac[j] > 1e-3:      # one rigid weight set per stud, only over the repaired shirt
            for i in ids:
                new[i] = dict(new[j])
            studs += 1
    # 3. elbow skin piece
    ep = piece_at(.285 * sx, .796, 60, 200); fa = piece_at(.39 * sx, .55, 400, 600)
    ids = np.flatnonzero(pc == ep); ft = tree(np.flatnonzero(pc == fa))
    bot = tree([i for i in ids if boundary[i] and co[i, 2] <= .77])     # the lower rim loop, under the bracer
    for i in ids:
        w = dict(W[i]); u = w.pop(f'B_{side}_UpperArm', 0)
        if u:
            w[f'B_{side}_UpperArmTwist'] = w.get(f'B_{side}_UpperArmTwist', 0) + u
        a_bot = 1 - smooth(bot.find(co[i])[2], .01, .05)
        if a_bot > 0:
            w = lerp(w, W[ft.find(co[i])[1]], float(a_bot))
        new[i] = norm(w)
    blend[region] = np.maximum(blend[region], bfac[region])
    report[side] = dict(region=len(region), fixed_arm=int(fix1[region].sum()), fixed_orig=int(fix0[region].sum()),
                        studs=studs, elbow_vertices=len(ids))
# write back, at most 8 influences, normalised
changed = 0
for i, v in enumerate(me.vertices):
    if new[i] == W[i]:
        continue
    w = norm(dict(sorted(norm(new[i]).items(), key=lambda kv: -kv[1])[:8])); changed += 1
    for g in list(v.groups):
        if gname[g.group] != 'ReduceProtect':
            o.vertex_groups[g.group].remove([i])
    for k, x in w.items():
        if k not in gidx:
            gidx[k] = o.vertex_groups.new(name=k).index
        o.vertex_groups[gidx[k]].add([i], x, 'REPLACE')
np.save(os.path.join(HERE, 'work/arm_blend.npy'), blend)   # per vertex, for keeping the repaired area exact
print('FIXED', report, 'changed vertices', changed)
bpy.ops.wm.save_as_mainfile(filepath=SRC)
