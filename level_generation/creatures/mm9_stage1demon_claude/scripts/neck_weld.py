"""Neck pass (user review 2026-11-01, "lesser demon - check the neck"). place_head.py left the head as a closed shell pushed
into a flat capped wall where Meshy's own head had been: the buried back of the head (dark, unpainted) and the wall (big flat
triangles with grey plate paint) came out under the jaw whenever MM9 lifts the head or drops the jaw.
Here, on the UV master (UVs and paints kept for every face that stays):
1. the head shell is cut by the plane y = HEAD_Y (inside |x| < 0.2, so the horns stay whole) and loses everything behind it
   (the buried plug); the mouth cavity's own cut ring is capped;
2. the body skin is cut along a rounded rectangle seen from the front (|x/A|^4 + |(z-ZC)/B|^4 = 1, forward-facing skin only)
   and loses the inside: the capped wall and the neck skin the head pierced;
3. the two smooth loops are bridged (Blender's bridge edge loops, SURFACE interpolation, CUTS rings): one continuous surface
   from the chest into the jaw, a short thick throat. Tube faces: body material, part 0, face attribute 'neck' = 1.
UVs: neck_uv.py; weights: neck_weights.py (both run on this output). Args: <in blend> <out blend>"""
import bpy, bmesh, sys, json, os
import numpy as np
from mathutils import Vector
IN, OUT = sys.argv[sys.argv.index('--') + 1:][:2]
HEAD_Y = -0.60
A, B, ZC = 0.26, 0.31, 0.61
CUTS = 6
SNAP = float(os.environ.get('NECK_SNAP', 0.25))
bpy.ops.wm.open_mainfile(filepath=IN)
o = bpy.data.objects['Body']; me = o.data
bm = bmesh.new(); bm.from_mesh(me)
pl = bm.verts.layers.int['part']; hl = bm.faces.layers.int['head']
nkl = bm.faces.layers.int.get('neck') or bm.faces.layers.int.new('neck')


def g_skin(p): return (abs(p.x) / A) ** 4 + (abs(p.z - ZC) / B) ** 4 - 1.0          # < 0 inside the hole
def g_head(p): return HEAD_Y - p.y                                                    # < 0 behind the cut plane


def cut(faces, g):
    """split every edge of the faces where g changes sign (linear root), connect the two new vertices across each face"""
    faces = set(faces); bm.edges.index_update(); newv = set()
    edges = sorted({e for f in faces for e in f.edges}, key=lambda e: e.index)        # a fixed order: snapping is order-dependent
    for e in edges:
        a, b = e.verts
        if a in newv or b in newv: continue
        ga, gb = g(a.co), g(b.co)
        if (ga < 0) == (gb < 0) or abs(ga - gb) < 1e-12: continue
        t = ga / (ga - gb)
        if t < SNAP or t > 1 - SNAP:              # no slivers: the near vertex moves onto the cut instead
            v = a if t < 0.5 else b; v.co = a.co.lerp(b.co, t); newv.add(v); continue
        ne, nv = bmesh.utils.edge_split(e, a, t); newv.add(nv)
    bm.faces.ensure_lookup_table()
    for f in list(bm.faces):
        vs = [v for v in f.verts if v in newv]
        if len(vs) == 2 and not any(set(e.verts) == set(vs) for e in f.edges):
            bmesh.ops.connect_verts(bm, verts=vs)
    return newv


# 1. head: cut and drop the plug
head_f = [f for f in bm.faces if all(v[pl] == 10 for v in f.verts) and all(abs(v.co.x) < 0.2 for v in f.verts)]
NH = cut(head_f, g_head)
bm.faces.ensure_lookup_table()
dead = [f for f in bm.faces if all(v[pl] == 10 for v in f.verts) and all(abs(v.co.x) < 0.2 for v in f.verts)
        and g_head(f.calc_center_median()) < 0]
print('HEAD plug faces', len(dead))
# 2. skin: cut and drop the hole
skin_f = [f for f in bm.faces if all(v[pl] == 0 for v in f.verts) and all(v.co.y < -0.25 for v in f.verts) and f.normal.y < 0.3
          and all(abs(v.co.x) < A + 0.08 and ZC - B - 0.08 < v.co.z < ZC + B + 0.08 for v in f.verts)]
NS = cut(skin_f, g_skin)
bm.faces.ensure_lookup_table()
hole = [f for f in bm.faces if all(v[pl] == 0 for v in f.verts) and all(v.co.y < -0.25 for v in f.verts)
        and g_skin(f.calc_center_median()) < 0 and f.calc_center_median().y < -0.3]
print('SKIN hole faces', len(hole))
dset = set(dead + hole)
rim = {e for f in dset for e in f.edges if any(g not in dset for g in e.link_faces)}
rim_v = {v for e in rim for v in e.verts}
bmesh.ops.delete(bm, geom=dead + hole, context='FACES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()


def loops(part, test, vset):
    es = [e for e in bm.edges if e.is_boundary and all(v[pl] == part for v in e.verts) and all(v in vset for v in e.verts)]
    left = set(es); out = []
    while left:
        e = left.pop(); grp = {e}; st = [e]
        while st:
            x = st.pop()
            for v in x.verts:
                for y in v.link_edges:
                    if y in left: left.discard(y); grp.add(y); st.append(y)
        out.append(grp)
    out.sort(key=len, reverse=True)
    return out


lb = loops(0, None, rim_v)
lh = loops(10, None, rim_v)
print('LOOPS skin', [len(g) for g in lb], 'head', [len(g) for g in lh])


def radial(g):
    """mean outward-ness of the faces along a loop (> 0: the outer skin, < 0: an inner cavity wall)"""
    vs = {v for e in g for v in e.verts}; c = sum((v.co for v in vs), Vector()) / len(vs); s = 0
    for e in g:
        f = e.link_faces[0]; r = f.calc_center_median() - c; r.y = 0
        s += f.normal.dot(r.normalized()) if r.length > 1e-6 else 0
    return s / len(g)


json.dump({'skin': [[[list(v.co) for v in e.verts] for e in g] for g in lb], 'head': [[[list(v.co) for v in e.verts] for e in g] for g in lh]},
          open(OUT + '.loops.json', 'w'))
def spread(g):
    P_ = np.array([list(v.co) for e in g for v in e.verts]); return float(np.linalg.norm(P_[:, [0, 2]] - P_[:, [0, 2]].mean(0), axis=1).mean())
lh = [g for g in lh if len(g) > 8]
rad = [spread(g) for g in lh]; print('HEAD loop mean radius', [round(r, 3) for r in rad])
k = int(np.argmax(rad)); eh = lh[k]; inner = [g for i, g in enumerate(lh) if i != k]; eb = lb[0]
# the cavity rings: capped (they sit deep in the throat behind the tongue)
for g in inner:
    ref = None                                  # the cavity's own colour at the ring: one head UV for the whole cap
    for e in g:
        for lp in e.link_faces[0].loops:
            if lp.vert in e.verts: ref = tuple(lp[bm.loops.layers.uv['HeadUV']].uv); break
        if ref: break
    bm.edges.index_update(); r_ = bmesh.ops.holes_fill(bm, edges=sorted(g, key=lambda e: e.index), sides=0); tr = bmesh.ops.triangulate(bm, faces=r_['faces'])
    for f in tr['faces']:
        f[hl] = 1
        for lp in f.loops: lp[bm.loops.layers.uv['HeadUV']].uv = ref; lp[bm.loops.layers.uv['UVMap']].uv = (0.0, 0.0)
    print('CAVITY cap', len(g), 'edges ->', len(r_['faces']), 'faces')
if '--loops-only' in sys.argv: raise SystemExit
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])

# 3. the tube: rings by angle round the neck axis (front view, centre (0, ZC)), Hermite between the body loop and the head
# loop with tangents in each surface's own tangent plane (C1 into both), RINGS inner rings of N samples; the loops' own
# vertices are zipped to the first and last ring by angle, so no twist is possible.
def ordered(g):
    vs = {v for e in g for v in e.verts}; adj = {v: [] for v in vs}
    for e in g: a_, b_ = e.verts; adj[a_].append(b_); adj[b_].append(a_)
    start = next(iter(vs)); out = [start]; prev = None; cur = start
    while True:
        nxt = [w for w in adj[cur] if w is not prev]
        if not nxt or nxt[0] is start: break
        prev, cur = cur, nxt[0]; out.append(cur)
    return out
def phi(p): return np.arctan2(p.z - ZC, p.x)
def vnormal(v):
    n_ = Vector()
    for f in v.link_faces: n_ += f.normal * f.calc_area()
    return n_.normalized()
LB, LH = ordered(eb), ordered(eh)
def sortloop(L):
    a_ = np.array([phi(v.co) for v in L]); k_ = int(np.argmin(a_)); L = L[k_:] + L[:k_]; a_ = np.r_[a_[k_:], a_[:k_]]
    if a_[1] < a_[0] or (len(a_) > 2 and np.mean(np.diff(np.unwrap(a_))) < 0): L = [L[0]] + L[1:][::-1]
    return L, np.unwrap(np.array([phi(v.co) for v in L]))
LB, AB = sortloop(LB); LH, AH = sortloop(LH)
def sample(L, A_, ang):
    """the loop point and the surface normal at angle ang (linear between loop vertices)"""
    A2 = np.r_[A_, A_[0] + 2 * np.pi]; L2 = L + [L[0]]; x = (ang - A2[0]) % (2 * np.pi) + A2[0]
    j = int(np.clip(np.searchsorted(A2, x) - 1, 0, len(L) - 1)); t_ = (x - A2[j]) / max(A2[j + 1] - A2[j], 1e-9)
    p_ = L2[j].co.lerp(L2[j + 1].co, t_); n_ = vnormal(L2[j]).lerp(vnormal(L2[j + 1]), t_).normalized()
    return p_, n_
N, RINGS, TG = int(os.environ.get('TUBE_N', 48)), int(os.environ.get('TUBE_RINGS', 3)), float(os.environ.get('TUBE_TAN', 0.6))
angs = -np.pi + (np.arange(N) + 0.5) * 2 * np.pi / N
rings = []
for a_ in angs:
    Bp, Bn = sample(LB, AB, a_); Hp, Hn = sample(LH, AH, a_)
    d_ = Hp - Bp; L_ = d_.length
    Tb = (d_ - Bn * d_.dot(Bn)).normalized() * L_ * TG          # leaves the body along the body surface
    Th = (d_ - Hn * d_.dot(Hn)).normalized() * L_ * TG          # arrives on the head along the head surface
    col = []
    for k in range(1, RINGS + 1):
        t = k / (RINGS + 1); h00, h10, h01, h11 = 2*t**3 - 3*t**2 + 1, t**3 - 2*t**2 + t, -2*t**3 + 3*t**2, t**3 - t**2
        col.append(Bp * h00 + Tb * h10 + Hp * h01 + Th * h11)
    rings.append(col)
RV = [[bm.verts.new(rings[i][k]) for i in range(N)] for k in range(RINGS)]
for row in RV:
    for v in row: v[pl] = 0
tube = []
def tri_(a_, b_, c_):
    f = bm.faces.new((a_, b_, c_)); f[nkl] = 1; tube.append(f); return f
for k in range(RINGS - 1):
    for i in range(N):
        j = (i + 1) % N; a_, b_, c_, d2 = RV[k][i], RV[k][j], RV[k + 1][j], RV[k + 1][i]
        tri_(a_, b_, c_); tri_(a_, c_, d2)
def zipper(L, A_, R, ra, rev=False):
    """triangles between loop L (angles A_) and ring R (angles ra), both increasing, cyclic"""
    t0 = len(tube); i = j = 0; nL, nR = len(L), len(R)
    A2 = np.r_[A_, A_ + 2 * np.pi]; R2 = np.r_[ra, ra + 2 * np.pi]
    j0 = int(np.searchsorted(ra, A_[0])) % nR
    if j0 > 0: R2 = np.r_[ra[j0:], ra[:j0] + 2 * np.pi, ra[j0:] + 2 * np.pi]; R = R[j0:] + R[:j0]
    while i < nL or j < nR:
        if j >= nR or (i < nL and A2[i + 1] < R2[j + 1]):
            tri_(L[i % nL], L[(i + 1) % nL], R[j % nR]); i += 1
        else:
            tri_(L[i % nL], R[(j + 1) % nR], R[j % nR]); j += 1
    if rev:
        for f in tube[t0:]: f.normal_flip()
zipper(LB, AB, RV[0], angs); zipper(LH, AH, RV[-1], angs, rev=True)
# winding: a tube face sharing an edge with an old face must run that edge the other way
old = set(bm.faces) - set(tube); agree = 0
for f in tube:
    for lp in f.loops:
        for g in lp.edge.link_faces:
            if g in old:
                gl = next(l for l in g.loops if l.edge is lp.edge)
                agree += 1 if gl.vert is lp.vert else -1
if agree > 0:
    for f in tube: f.normal_flip()
agree2 = 0
for f in tube:
    for lp in f.loops:
        for g in lp.edge.link_faces:
            if g is not f:
                gl = next(l for l in g.loops if l.edge is lp.edge)
                agree2 += 1 if gl.vert is lp.vert else 0
print('TUBE inconsistent edge-sides after fix', agree2)
print('TUBE built', len(tube), 'faces, rings', RINGS, 'x', N, 'winding check', agree)
# 4. tube UVs: one strip in the free right-hand column of the body atlas: x along the tube (rail arc length from the body
# loop), y round the neck (the rail's mean fraction of the ring length, times the mean ring length: straight rails, at most
# about 25 % anisotropy between the body and the head end); seam at the top (+90 deg, under the hump), TEXELS per metre
TEXELS = 414.0 / 2048; X0, Y0 = 1932 / 2048, 40 / 2048
uvl = bm.loops.layers.uv['UVMap']; huvl = bm.loops.layers.uv['HeadUV']
seam = int(np.argmin(np.abs(((angs - np.pi / 2) + np.pi) % (2 * np.pi) - np.pi)))
order_ = [(seam + q) % N for q in range(N)]
ringpts = [[sample(LB, AB, angs[i])[0] for i in range(N)]] + [[RV[k][i].co for i in range(N)] for k in range(RINGS)] + \
          [[sample(LH, AH, angs[i])[0] for i in range(N)]]
frac = np.zeros(N); lens = []
for R_ in ringpts:
    acc = [0.0]
    for q in range(1, N + 1): acc.append(acc[-1] + (R_[order_[q % N]] - R_[order_[q - 1]]).length)
    lens.append(acc[-1])
    for q in range(N): frac[order_[q]] += acc[q] / acc[-1] / len(ringpts)
Lmean = float(np.mean(lens))
railS = np.zeros((N, RINGS + 2))
for i in range(N):
    pts = [R_[i] for R_ in ringpts]
    railS[i] = np.r_[0, np.cumsum([(pts[q + 1] - pts[q]).length for q in range(len(pts) - 1)])]
info = {}
for k in range(RINGS):
    for i in range(N): info[RV[k][i]] = (frac[i], railS[i, k + 1])
def loop_info(v, head_):
    a_ = phi(v.co); x = (a_ - angs[0]) / (2 * np.pi / N); i0 = int(np.floor(x)) % N; i1 = (i0 + 1) % N; t_ = x - np.floor(x)
    f0, f1 = frac[i0], frac[i1]
    if abs(f1 - f0) > 0.5: f1 = f1 + 1 if f1 < f0 else f1 - 1
    fr = (f0 * (1 - t_) + f1 * t_) % 1.0
    return fr, (railS[i0, -1] * (1 - t_) + railS[i1, -1] * t_) if head_ else 0.0
for v in LB: info[v] = loop_info(v, False)
for v in LH: info[v] = loop_info(v, True)
for f in tube:
    fr = [info[lp.vert][0] for lp in f.loops]
    if max(fr) - min(fr) > 0.5: fr = [x + 1 if x < 0.5 else x for x in fr]
    for lp, x in zip(f.loops, fr):
        lp[uvl].uv = (X0 + info[lp.vert][1] * TEXELS, 1 - (Y0 + x * Lmean * TEXELS)); lp[huvl].uv = (0.0, 0.0)
    f[hl] = 0
print('TUBE uv: ring lengths', [round(x, 2) for x in lens], 'strip', round(Lmean * 414), 'px tall, rails up to', round(railS[:, -1].max() * 414), 'px')
nf_ = len(bm.faces)
if 'neck' in [a.name for a in me.attributes]: pass
print('NECK flags', sum(f[nkl] for f in bm.faces))
bm.to_mesh(me); bm.free()
print('TUBE faces', len(tube), 'mesh faces', len(me.polygons))
bpy.ops.wm.save_as_mainfile(filepath=OUT)
