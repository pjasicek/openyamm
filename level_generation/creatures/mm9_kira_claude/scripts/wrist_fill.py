"""Close the wrist under the vambrace rim (user review 2026-11-02, right hand from above: "the graft has a hole").

Cause: the vambrace (armour shell, part 1) ends in two open boundary loops at the wrist, Meshy's outer wall (18 vertices,
slanted, t 0.2-3.3 cm past the hand joint, r 1.6-2.4 cm) and its inner layer (14 vertices); sleeve_tuck.py 0.6 pulled
the glove stub to 60 % of the sleeve radius up to 3 cm past the hand joint, so at the rim the glove was a 0.7-1.2 cm
stalk inside a 1.6-2.4 cm tube: a bent wrist showed the open hollow end and the thin stalk.

Per side, rest pose, geometry and weights only on existing vertices (UVs unchanged, the paid paint stays valid):
1. Glove flare: glove (hand-face) vertices between T_IN behind the joint and 1 mm inside the rim (past it they showed as
   teeth under the rim), whose perpendicular
   ray from the forearm axis meets the vambrace, move out to K x the first wall hit (K blends from 0 at T_IN to FLARE at
   T_FULL), never inward; a glove face that then passes through the outer wall (a point inside the rim's span whose
   outward ray meets no wall) steps its flared vertices back 20 % towards their old place, up to 8 rounds (6 faces
   per side at the slanted rim already did so before the flare and still do). Their weights become the nearest vambrace vertex's (smoothstep from the glove's own at
   +6 mm to the vambrace's at T_FULL), so glove top, rim and cap move together in every clip (no poke, no gap).
2. Rim cap: one new ring of faces from the outer loop inward to CAP x its radius (or 0.9 x the flared glove radius, at
   least 0.3 x the rim radius,
   on the rim's own plane, if smaller), recessed 2 mm, facing out of the vambrace towards the hand. Vertices and faces
   copy the rim's attributes and weights (BMesh example elements); every column takes the rim face's own texel (30 % into the
   face) on all UV layers: the cap reads as the vambrace's rolled metal edge.
Args: <in blend> <out blend> [flare 0.9] [cap 0.72]"""
import bpy, bmesh, sys, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.kdtree import KDTree
a = sys.argv[sys.argv.index('--') + 1:]
IN, OUT = a[0], a[1]
FLARE = float(a[2]) if len(a) > 2 else 0.9
CAP = float(a[3]) if len(a) > 3 else 0.72
T_IN, T_FULL, T_OWN, RECESS = -0.015, -0.004, 0.006, 0.002
bpy.ops.wm.open_mainfile(filepath=IN)
body = bpy.data.objects['Body']; rig = body.parent; me = body.data
if rig.animation_data: rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
assert all(abs(x - (1.0 if i % 5 == 0 else 0.0)) < 1e-9 for i, x in enumerate([c for r in body.matrix_world for c in r]))
bm = bmesh.new(); bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
lp, lk = bm.faces.layers.int['part'], bm.faces.layers.int['hand']
dl = bm.verts.layers.deform.active
uvs = list(bm.loops.layers.uv.values())
names = [g.name for g in body.vertex_groups]


def sst(x, a_, b_):
    t = min(max((x - a_) / (b_ - a_), 0.0), 1.0); return t * t * (3 - 2 * t)


rep = {}
for S in 'LR':
    fa = rig.matrix_world @ rig.data.bones[f'Bip01 {S} Forearm'].head_local
    hd = rig.matrix_world @ rig.data.bones[f'Bip01 {S} Hand'].head_local
    ax = (hd - fa).normalized()
    T = lambda p: (p - hd).dot(ax)
    R = lambda p: ((p - hd) - ax * (p - hd).dot(ax))
    side = lambda p: (p.x > 0) == (hd.x > 0)
    shell = [f for f in bm.faces if f[lp] == 1 and not f[lk] and side(f.calc_center_median())
             and abs(T(f.calc_center_median())) < 0.08 and R(f.calc_center_median()).length < 0.06]
    bvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in shell])
    sv = sorted({v for f in shell for v in f.verts}, key=lambda v: v.index)
    kd = KDTree(len(sv))
    for i, v in enumerate(sv): kd.insert(v.co, i)
    kd.balance()
    # boundary loops of the shell at the wrist; the outer = the one reaching furthest past the joint
    sset = set(shell)
    be = [e for e in bm.edges if e.is_boundary and e.link_faces[0] in sset]
    seen, loops = set(), []
    for e in be:
        if e in seen: continue
        st, comp = [e], []
        while st:
            x = st.pop()
            if x in seen: continue
            seen.add(x); comp.append(x)
            for v in x.verts: st += [y for y in v.link_edges if y in be and y not in seen]
        loops.append(comp)
    loops = [c for c in loops if len(c) >= 8]
    outer = max(loops, key=lambda c: max(T(v.co) for e in c for v in e.verts))
    ring = [outer[0].verts[0]]; left = set(outer)
    while left:
        nx = next((x for x in left if ring[-1] in x.verts), None)
        if nx is None: break
        left.discard(nx); o = nx.other_vert(ring[-1])
        if o is ring[0]: break
        ring.append(o)
    rim_t = {v: T(v.co) for v in ring}
    U = R(ring[0].co).normalized(); V = ax.cross(U)
    ang = lambda p: np.arctan2(R(p).dot(V), R(p).dot(U))
    ra = np.array([ang(v.co) for v in ring]); rt = np.array([rim_t[v] for v in ring]); o_ = np.argsort(ra)
    rim_at = lambda th: float(np.interp(th, ra[o_], rt[o_], period=2 * np.pi))
    # 1. glove flare
    gv = sorted({v for f in bm.faces if f[lk] for v in f.verts if side(v.co)}, key=lambda v: v.index)
    moved, maxout, rew = 0, 0.0, 0
    orig = {v.index: v.co.copy() for v in gv}
    for v in gv:
        t = T(v.co); r = R(v.co)
        if t < T_IN or t > rim_at(ang(v.co)) - 0.001 or r.length < 1e-5 or r.length > 0.06: continue
        p0 = hd + ax * t; rd = r.normalized()
        hit = bvh.ray_cast(p0, rd, 0.06)
        if hit[0] is None: continue
        rs = (hit[0] - p0).dot(rd)
        k = FLARE * sst(t, T_IN, T_FULL)
        target = k * rs
        if target > r.length:
            maxout = max(maxout, target - r.length); v.co = p0 + rd * target; moved += 1
        kk = 1.0 - sst(t, T_FULL, T_OWN)          # 1 inside the rim -> the vambrace's weights
        if kk > 0:
            _, j, _ = kd.find(v.co); src = sv[j]
            mix = {}
            for g, w in v[dl].items():
                if not names[g].startswith('MP_'): mix[g] = mix.get(g, 0) + (1 - kk) * w
            for g, w in src[dl].items():
                if not names[g].startswith('MP_'): mix[g] = mix.get(g, 0) + kk * w
            top = sorted(mix.items(), key=lambda x: -x[1])[:4]; s = sum(w for _, w in top)
            for g in [g for g in v[dl].keys() if not names[g].startswith('MP_')]: del v[dl][g]
            for g, w in top: v[dl][g] = w / s
            rew += 1
    # 1b. no glove face through the vambrace's outer wall: a glove point inside the rim's span whose outward ray meets no
    #     wall is outside the vambrace; the flared vertices of such faces step back towards their old radius
    def poking():
        out = []
        for f in bm.faces:
            if not f[lk] or not side(f.calc_center_median()): continue
            pts = [f.calc_center_median()] + [(e.verts[0].co + e.verts[1].co) / 2 for e in f.edges]
            for p in pts:
                t = T(p); r = R(p)
                if t < T_IN or t > rim_at(ang(p)) - 0.0005 or r.length < 1e-5: continue
                if bvh.ray_cast(p, r.normalized(), 0.06)[0] is None: out.append(f); break
        return out
    poke0 = len(poking()); steps = 0
    for _ in range(8):
        bad = poking()
        if not bad: break
        for f in bad:
            for v in f.verts:
                if v.index in orig and (v.co - orig[v.index]).length > 1e-6:
                    v.co = orig[v.index].lerp(v.co, 0.8); steps += 1
    rep_poke = (poke0, len(poking()), steps)
    bm.normal_update()
    gfaces = [f for f in bm.faces if f[lk] and side(f.calc_center_median())]
    gbvh = BVHTree.FromPolygons([v.co.copy() for v in bm.verts], [[v.index for v in f.verts] for f in gfaces])
    # 2. rim cap
    inner, radii = [], []
    for v in ring:
        t = rim_t[v] - RECESS; r = R(v.co); rd = r.normalized(); p0 = hd + ax * t
        h = gbvh.ray_cast(p0 + rd * 0.0005, rd, 0.06)
        rg = (h[0] - p0).dot(rd) if h[0] is not None else None
        rr = CAP * r.length if rg is None else max(min(CAP * r.length, 0.9 * rg), 0.3 * r.length)
        nv = bm.verts.new(p0 + rd * rr, v)
        inner.append(nv); radii.append((round(r.length, 4), None if rg is None else round(rg, 4), round(rr, 4)))
    n = len(ring); new = []
    for i in range(n):
        j = (i + 1) % n
        e = bm.edges.get((ring[i], ring[j])); f0 = e.link_faces[0]
        c = sum((Vector(l[uvs[0]].uv) for l in f0.loops), Vector((0, 0))) / 3
        for tri in ((ring[i], ring[j], inner[j]), (ring[i], inner[j], inner[i])):
            f = bm.faces.new(tri, f0); f.normal_update()
            if f.normal.dot(ax) < 0: f.normal_flip()
            for l in f.loops:
                for ly in uvs:
                    cc = sum((Vector(x[ly].uv) for x in f0.loops), Vector((0, 0))) / 3
                    l[ly].uv = Vector(f0.loops[0][ly].uv).lerp(cc, 0.3) if l.vert in (ring[i], inner[i]) else \
                        Vector(next(x for x in f0.loops if x.vert is ring[j])[ly].uv).lerp(cc, 0.3)
            new.append(f)
    rep[S] = dict(shell_faces=len(shell), loops=[len(c) for c in loops], rim_verts=n, glove_moved=moved,
                  glove_max_out_mm=round(maxout * 1000, 1), glove_reweighted=rew,
                  glove_faces_through_wall_before_after=rep_poke[:2], step_backs=rep_poke[2], cap_faces=len(new),
                  cap_radii=radii)
bm.to_mesh(me); bm.free(); me.update()
bpy.ops.wm.save_as_mainfile(filepath=OUT)
print('WRISTFILL ' + json.dumps({s: {k: v for k, v in d.items() if k != 'cap_radii'} for s, d in rep.items()}))
print('WRISTRADII ' + json.dumps({s: d['cap_radii'] for s, d in rep.items()}))
