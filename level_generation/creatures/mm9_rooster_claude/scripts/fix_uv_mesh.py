"""Post-UV repairs of the rooster 'Body' (no change to UVs or the paid retexture: vertices move or weld, loops keep
their UVs). Args: <in blend> <out blend> <fit_v2.json> <fit_v1.npz> <fit_v2.npz>
1. Throat slit: the head/loft bridge left a slit at the front of the neck (viewer, 2026-10-30). The open boundary is
   split at its two x ends into an upper and a lower chain, the chains weld at midpoints, the triangle that stays
   open gets a face whose UVs sit on one feather texel area, and the throat around it is relaxed (no step).
2. Leg: leg_fit.py closed the leg chain at an exit it found at z 0.1 (the spur stopped the slice scan) and laid the
   shank across a 6 cm jump to Xleg, a Z-fold (viewer). Each leg vertex goes back to its pre-leg_fit place (nearest
   point on the fit_v2 surface -> the same barycentric point of fit_v1, same topology), then the straight Meshy shank
   (height za..ZE) is laid on MM9's true leg path: ankle, Xlowrleg hock, a short way up to Xleg. The foot is moved
   and yawed as in leg_fit; above ZE the offset fades into the thigh over FADE, radially too.
3. Shank weights: Xlowrleg between the ankle and the hock, blending into Xleg over HOCK_BLEND around the hock and
   into Xfoot just above the ankle.
"""
import bpy, bmesh, sys, json, os
import math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, FIT, N1, N2 = a
FADE, RAD0, RAD1 = 0.09, 0.04, 0.09
ZE = 0.14            # the shank's top in the global fit (fit_v1)
HOCK_BLEND = 0.015
SIDES = {'r': (-1, 'Xlowrleg', 'Xleg'), 'l': (1, 'Xlowrleg01', 'Xleg01')}
bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']; rig = bpy.data.objects['MM9_Rig']
J = {b.name: np.array(rig.matrix_world @ b.head_local) for b in rig.data.bones}
fit = json.load(open(FIT))
rep = {}
# ---- 1. throat slit
bm = bmesh.new(); bm.from_mesh(ob.data)
bnd = [e for e in bm.edges if e.is_boundary]
es = set(bnd); seen = set(); loops = []
for e in bnd:
    if e in seen:
        continue
    st, lp = [e], []; seen.add(e)
    while st:
        x = st.pop(); lp.append(x)
        for v in x.verts:
            for y in v.link_edges:
                if y in es and y not in seen:
                    seen.add(y); st.append(y)
    loops.append(lp)
lp = max([l for l in loops if np.mean([v.co.y for e in l for v in e.verts]) < -0.15],
         key=lambda l: max(v.co.x for e in l for v in e.verts) - min(v.co.x for e in l for v in e.verts))
vs = list({v for e in lp for v in e.verts})
a_ = min(vs, key=lambda v: v.co.x); b_ = max(vs, key=lambda v: v.co.x)
mid = [v for v in vs if v not in (a_, b_)]
line = lambda v: a_.co.z + (b_.co.z - a_.co.z) * (v.co.x - a_.co.x) / max(b_.co.x - a_.co.x, 1e-9)
c1 = [a_] + sorted([v for v in mid if v.co.z >= line(v)], key=lambda v: v.co.x) + [b_]
c2 = [a_] + sorted([v for v in mid if v.co.z < line(v)], key=lambda v: v.co.x) + [b_]
sh, lg = (c1, c2) if len(c1) <= len(c2) else (c2, c1)
tm = {}
for v in sh[1:-1]:
    u = min(lg[1:-1], key=lambda w: (w.co - v.co).length) if len(lg) > 2 else None
    if u is None:
        continue
    m = (v.co + u.co) / 2
    v.co = m; u.co = m
    if u not in tm and u is not v:
        tm[u] = v
for u in lg[1:-1]:
    if u not in tm:
        tm[u] = min(sh, key=lambda w: (w.co - u.co).length)
rep['throat'] = {'loop_edges': len(lp), 'x': [a_.co.x, b_.co.x], 'welds': len(tm)}
bmesh.ops.weld_verts(bm, targetmap=tm)
rep['throat']['open_left_near'] = sum(1 for e in bm.edges if e.is_boundary and e.verts[0].co.y < -0.15 and
                                       0.5 < e.verts[0].co.z < 0.56)
# the triangle (or small loop) left open: one face, UVs on a feather area next to it
left = [e for e in bm.edges if e.is_boundary and min(v.co.y for v in e.verts) < -0.15 and
        0.5 < e.verts[0].co.z < 0.56]
uvl = bm.loops.layers.uv.active
vs2 = list({v for e in left for v in e.verts})
if len(vs2) == 3:
    A, B, C = vs2
    f = bm.faces.new((A, B, C))
    n = (B.co - A.co).cross(C.co - A.co)
    if n.y > 0:                                   # the throat faces forward (-Y)
        f.normal_flip()
    # the patch was never painted: its corners sit together on the feather texel nearest the median white nearby
    img = bpy.data.images.load(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'textures',
                                            'rooster_basecolor.png'))
    W_, H_ = img.size
    px = np.empty(W_ * H_ * 4, np.float32); img.pixels.foreach_get(px); px = px.reshape(H_, W_, 4)
    cen = (A.co + B.co + C.co) / 3
    best, bl = 9.0, None
    for g in bm.faces:
        if g is f or (g.calc_center_median() - cen).length > 0.06:
            continue
        for l in g.loops:
            u_ = l[uvl].uv
            lum = float(px[min(int(u_.y * H_), H_ - 1), min(int(u_.x * W_), W_ - 1), :3] @ np.array([.2126, .7152, .0722]))
            if abs(lum - 0.85) < best:
                best, bl = abs(lum - 0.85), l
    rep['throat']['patch_lum_err'] = best
    for j, l in enumerate(f.loops):
        l[uvl].uv = bl[uvl].uv + Vector((0.0005 * j, 0.0005 * ((j + 1) % 2)))
    rep['throat']['filled'] = 1
    # the neck's front stands proud of the head's stub: the patch is a horizontal shelf (a throat step). Relax the
    # throat's vertices so the surface slopes from the head into the neck instead
    pl_ = bm.verts.layers.int['piece']
    bm.verts.ensure_lookup_table()
    sel = [v for v in bm.verts if v[pl_] == 0 and abs(v.co.x) < 0.075 and v.co.y < -0.13 and 0.49 < v.co.z < 0.575]
    sset = set(sel)
    for _ in range(40):
        new = {}
        for v in sel:
            nb = [e.other_vert(v).co for e in v.link_edges]
            if nb:
                new[v] = v.co.lerp(sum(nb, Vector()) / len(nb), 0.6)
        for v, c_ in new.items():
            v.co = c_
    rep['throat']['relaxed_verts'] = len(sel)
# stray shards: separate pieces of a few faces (detached_parts_audit: single triangles and loose vertices in the tail)
seen_v = set(); shards = []
for v in bm.verts:
    if v in seen_v:
        continue
    comp, st = [v], [v]; seen_v.add(v)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y not in seen_v:
                seen_v.add(y); st.append(y); comp.append(y)
    if len({f for c_ in comp for f in c_.link_faces}) <= 6:
        shards += comp
rep['shard_verts'] = len(shards)
bmesh.ops.delete(bm, geom=shards, context='VERTS')
bm.to_mesh(ob.data); bm.free()
# ---- 2. leg
me = ob.data
P = np.array([tuple(v.co) for v in me.vertices])
piece = np.array([d.value for d in me.attributes['piece'].data])
d1, d2 = np.load(N1), np.load(N2)
P1, P2, F = d1['P'], d2['P'], d2['F']
assert len(P1) == len(P2)
bvh = BVHTree.FromPolygons([tuple(p) for p in P2], [tuple(int(i) for i in f) for f in F])
dy0 = fit['shift_y']
Pn = P.copy()
legm = (np.abs(P[:, 0]) > 0.012) & (piece == 0) & (P[:, 2] < ZE + FADE + 0.02)
back = {}
for i in np.nonzero(legm)[0]:
    loc, nrm, fi, dist = bvh.find_nearest(Vector(P[i]))
    if dist > 0.012:
        continue
    t = F[fi]
    a0, b0, c0 = P2[t[0]], P2[t[1]], P2[t[2]]
    v0, v1, v2 = b0 - a0, c0 - a0, np.array(loc) - a0
    d00, d01, d11, d20, d21 = v0 @ v0, v0 @ v1, v1 @ v1, v2 @ v0, v2 @ v1
    den = max(d00 * d11 - d01 * d01, 1e-16)
    w1 = (d11 * d20 - d01 * d21) / den; w2 = (d00 * d21 - d01 * d20) / den; w0 = 1 - w1 - w2
    back[int(i)] = w0 * P1[t[0]] + w1 * P1[t[1]] + w2 * P1[t[2]]
rep['leg_vertices_back'] = len(back)
for side, (s_, lw, kn) in SIDES.items():
    Fj, L9, K9 = J[kn.replace('Xleg', 'Xfoot')], J[lw], J[kn]
    L = fit['landmarks'][side]
    za, floor = L['ankle_z'], L['floor']
    ids = [i for i, p in back.items() if s_ * p[0] > 0]
    O = np.array([back[i] for i in ids])
    # the original shank's centre by height
    zs = np.arange(za, ZE + 1e-6, 0.005)
    ank0 = np.array(L['ankle'])
    cl = []
    c = ank0[:2]
    for z in zs:
        m = (s_ * P1[:, 0] > 0.01) & (np.abs(P1[:, 2] - z) < 0.004) & (np.hypot(P1[:, 0] - c[0], P1[:, 1] - c[1]) < 0.03)
        if m.sum() >= 3:
            c = np.median(P1[m, :2], axis=0)
        cl.append(c.copy())
    cl = np.array(cl)
    for _ in range(3):
        cl[1:-1] = (cl[:-2] + 2 * cl[1:-1] + cl[2:]) / 4
    # MM9's path: ankle (at our new ankle height), hock, a little up towards the knee
    A0 = Fj.copy(); A0[2] = za - floor
    Ee = L9 + 0.12 * (K9 - L9)
    poly = [A0, L9, Ee]
    seg = [np.linalg.norm(poly[k + 1] - poly[k]) for k in range(2)]
    tot = sum(seg)

    def path(u):
        x = u * tot
        if x <= seg[0]:
            return poly[0] + (poly[1] - poly[0]) * (x / seg[0])
        return poly[1] + (poly[2] - poly[1]) * ((x - seg[0]) / seg[1])
    disp_ex = path(1.0) - np.array([cl[-1, 0], cl[-1, 1] + dy0, ZE])
    disp_ft = path(0.0) - np.array([cl[0, 0], cl[0, 1], za])     # the ankle slice's move (shift included)
    yaw = math.radians(fit[side]['foot_yaw_deg'])
    cy, sy = math.cos(yaw), math.sin(yaw)
    for i, o in zip(ids, O):
        z = o[2]
        if z < za:
            q = o + disp_ft
            x_, y_ = q[0] - A0[0], q[1] - A0[1]
            if np.hypot(x_, y_) > 0.2:
                continue
            q[0] = A0[0] + x_ * cy - y_ * sy
            q[1] = A0[1] + y_ * cy + x_ * sy
            Pn[i] = q
        elif z <= ZE:
            u = (z - za) / (ZE - za)
            c_ = np.array([np.interp(z, zs, cl[:, 0]), np.interp(z, zs, cl[:, 1])])
            off = o[:2] - c_
            if np.linalg.norm(off) > 0.05:
                continue
            q = path(u)
            yw = max(0.0, 1 - (z - za) / 0.02) * yaw
            cw, sw = math.cos(yw), math.sin(yw)
            Pn[i] = np.array([q[0] + off[0] * cw - off[1] * sw, q[1] + off[1] * cw + off[0] * sw, q[2]])
        else:
            r = np.hypot(o[0] - cl[-1, 0], o[1] - cl[-1, 1])
            wz = max(0.0, 1 - (z - ZE) / FADE)
            wr = float(np.clip((RAD1 - r) / (RAD1 - RAD0), 0, 1))
            w = wz * wr; w = w * w * (3 - 2 * w)
            if w > 0:
                Pn[i] = o + np.array([0, dy0, 0]) + w * disp_ex
    # ---- 3. shank weights
    gi = {g.name: g.index for g in ob.vertex_groups}
    ank_z, hock_z = za - floor, L9[2]
    foot_b, low_b, leg_b = kn.replace('Xleg', 'Xfoot'), lw, kn
    for nm in (low_b, leg_b):
        if nm not in gi:
            gi[nm] = ob.vertex_groups.new(name=nm).index
    for i, o in zip(ids, O):
        z0 = Pn[i, 2]
        if z0 < ank_z + 0.002 or z0 > hock_z + HOCK_BLEND:
            continue
        f = float(np.clip((z0 - ank_z) / 0.015, 0, 1)); f = f * f * (3 - 2 * f)
        h = float(np.clip((z0 - (hock_z - HOCK_BLEND)) / (2 * HOCK_BLEND), 0, 1)); h = h * h * (3 - 2 * h)
        w = {foot_b: 1 - f, low_b: f * (1 - h), leg_b: f * h}
        for g in list(me.vertices[i].groups):
            ob.vertex_groups[g.group].remove([i])
        for nm, x in w.items():
            if x > 0.01:
                ob.vertex_groups[nm].add([i], float(x), 'REPLACE')
for v, p in zip(me.vertices, Pn):
    v.co = Vector(p)
# ---- 4. the skull under the comb is rigid with it: the comb runs back over the nape, and a nape following the neck
# leaves the comb's root in the air in the deepest head turns
hz = np.array([d.value for d in me.attributes['head_rz'].data])
from mathutils.kdtree import KDTree
bmc = bmesh.new(); bmc.from_mesh(me); bmc.verts.ensure_lookup_table()
seen_c = set(); comb = []
for v in bmc.verts:
    if piece[v.index] != 2 or v.index in seen_c:
        continue
    cc, st = [v.index], [v]; seen_c.add(v.index)
    while st:
        x = st.pop()
        for e in x.link_edges:
            y = e.other_vert(x)
            if y.index not in seen_c:
                seen_c.add(y.index); st.append(y); cc.append(y.index)
    C_ = Pn[cc]
    if abs(C_[:, 0].mean()) < 0.01 and hz[cc].min() > -4 and len(cc) > 100:
        comb += cc
bmc.free()
# the comb stood 4.5 mm off the filled skull under it: seat it
for i in comb:
    Pn[i, 2] -= 0.005
    me.vertices[i].co.z -= 0.005
kc = KDTree(len(comb))
for j, i in enumerate(comb):
    kc.insert(Vector(Pn[i]), j)
kc.balance()
xh = ob.vertex_groups['Xhead']
nc = 0
for i in np.nonzero(piece == 0)[0]:
    d = kc.find(Vector(Pn[i]))[2]
    if d > 0.035:
        continue
    w = 1.0 if d < 0.015 else 1 - (d - 0.015) / 0.02
    w = w * w * (3 - 2 * w)
    old = [(g.group, g.weight) for g in me.vertices[int(i)].groups]
    keep = [(g_, x * (1 - w)) for g_, x in old if g_ != xh.index]
    have = sum(x for g_, x in old if g_ == xh.index)
    for g_, x in old:
        ob.vertex_groups[g_].remove([int(i)])
    for g_, x in keep:
        if x > 0.01:
            ob.vertex_groups[g_].add([int(i)], x, 'REPLACE')
    xh.add([int(i)], (1 - w) * have + w, 'REPLACE')
    nc += 1
rep['comb_rigid_verts'] = nc
me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('FIXED ' + json.dumps(rep, default=float))
