"""Replace the five heads of the rigged reduced hydra (work/rig_v1.blend, rig.json) with the Smart Topology heads
(head_fit.py: work/heads/h<k>_st.blend + h<k>_fit.json), decimated to a triangle budget.

Each new head is cut just behind the skull (a plane across its own neck CUT_N model units from the snout tip; only
surface near the neck axis is cut, so horns and fins sweeping back stay whole) and placed RIGIDLY: tip onto our tip,
its skull axis onto our Head bone, up = world Z made perpendicular, scale sigma (skull width against our neck width).
Our neck is cut LOFT behind the head-model point PIECE_N (at or behind the skull ring), and a new tube (the loft) joins the two rings: a Hermite centreline
leaving the skull along its own neck direction and arriving along ours, cross-sections interpolated between the two
ring shapes, zipped to both rings. (v3 bent the Meshy neck stubs onto our necks; they arch the opposite way and some
are separate shells, which folded and tore at every joint.)
The old head is removed by a flood fill from its snout tip through everything in front of our neck's cut; old horn and
fin parts cut off behind it fall away as loose pieces; small holes in the body are capped.
Parts (face attribute 'part'): k = the new head (head texture; its band behind SPLIT_N is neck-coloured, vertex
attribute head_skull 0), 0 = the loft and the body (body texture). Weights: head rigid on Head<k>; the loft blends from
Head<k> at the skull ring to our neck's weights at our ring.
The high-res retextured heads (meshy/head<k>_retexture_v2) are mapped the same rigid way into work/heads_hi.blend
(objects HeadHi<k>): the head bake sources.
  blender --background work/rig_v1.blend --python scripts/graft_heads.py -- <out.blend> [b1 b2 b3 b4 b5]
(b<k> = head triangle budget of head k, 0 = undecimated). Prints per head the triangle counts."""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
args = sys.argv[sys.argv.index('--') + 1:]
OUT = args[0]
BUDGET = [int(a) for a in args[1:6]] if len(args) >= 6 else [1400, 1800, 1400, 2400, 2100]   # same look as 1800-3000 (work/budget/cmp_*.png)
HEAD_TO_NECK = 1.3          # skull width (10-90 percentile) / our neck's width at the cut (native heads are wider)
SCALE_FIX = {1: 0.8, 2: 1.0, 3: 0.95, 4: 0.88, 5: 0.95}  # per head: clear the neighbours (check_heads.py)
LAT_SQUEEZE = {2: 0.7, 4: 0.6}   # lateral parts beyond the skull's half width shortened (head 2 jaw spikes, head 4 fins)
SKULL_N, SPLIT_N = 0.33, 0.40   # head-model units from the snout tip: straight skull segment, skull/neck colour split
CUT_N = {1: 0.40, 2: 0.40, 3: 0.40, 4: 0.46, 5: 0.40}   # cut behind the skull: at the split, so no stub of Meshy's
                            # neck paint is left (its jagged edge read as stitching under the chin); head 4's fins
                            # are rooted behind the split, so it keeps its 0.46 cut
PIECE_N = 0.46             # separate pieces (fins, horns) reaching in front of this are kept, dorsal spines behind go;
                           # our neck is cut at this point + LOFT (the old body's head goes in front of it)
CUT_AXIS = 1.7              # the head cut removes only surface within this x the neck radius of its axis
LOFT, LOFT_STEP = 0.06, 0.025   # m: our neck is cut LOFT (along our curve) behind the skull ring; ring spacing
LOFT_MAX = 64
LOFT_SAMPLES = 24           # angular samples of the loft's cross-sections (40 at 12 mm spacing: 2.9k triangles for smooth tubes)
ZIP_RELAX = 3
OLD_PROTRUDE, OLD_REACH = 1.7, 0.15   # old protrusions within OLD_REACH m behind our cut, beyond OLD_PROTRUDE x radius
rig_json = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
body = bpy.data.objects['Hydra']; rig = bpy.data.objects['Hydra_Rig']; me = body.data


def smooth(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


class Curve:
    """Polyline from base to tip with arc-from-tip, radius and frames transported from the tip (T toward the tip)."""

    def __init__(self, P, R):
        self.P = np.asarray(P, float); self.R = np.asarray(R, float)
        L = np.linalg.norm(np.diff(self.P, axis=0), axis=1)
        self.s = np.concatenate([[0], np.cumsum(L[::-1])])[::-1]
        n = len(self.P) - 1
        T = [(self.P[i + 1] - self.P[i]) / L[i] for i in range(n)]
        U = [None] * n
        up = np.array([0, 0, 1.0]); u = up - (up @ T[-1]) * T[-1]; U[-1] = u / np.linalg.norm(u)
        for i in range(n - 2, -1, -1):
            u = U[i + 1] - (U[i + 1] @ T[i]) * T[i]; U[i] = u / np.linalg.norm(u)
        self.T, self.U = np.array(T), np.array(U)

    def frame_at(self, s):
        """Point, T, U, V and radius at arc s (clamped)."""
        s = min(max(s, 0.0), self.s[0])
        i = int(np.searchsorted(-self.s, -s)) - 1
        i = min(max(i, 0), len(self.P) - 2)
        t = (self.s[i] - s) / max(self.s[i] - self.s[i + 1], 1e-9)
        p = self.P[i] + t * (self.P[i + 1] - self.P[i])
        T, U = self.T[i], self.U[i]
        return p, T, U, np.cross(T, U), self.R[i] * (1 - t) + self.R[i + 1] * t

    def local(self, p):
        """(arc, local coords along T, U, V) of point p from its nearest polyline point."""
        best = (1e9, 0, 0.0)
        for i in range(len(self.P) - 1):
            a, b = self.P[i], self.P[i + 1]; d = b - a
            t = float(np.clip((p - a) @ d / (d @ d), 0, 1)); dist = float(np.linalg.norm(p - (a + t * d)))
            if dist < best[0]:
                best = (dist, i, t)
        _, i, t = best
        s = self.s[i] + t * (self.s[i + 1] - self.s[i])
        c = self.P[i] + t * (self.P[i + 1] - self.P[i]); T, U = self.T[i], self.U[i]; V = np.cross(T, U)
        r = p - c
        if i == len(self.P) - 2 and t >= 1.0:            # beyond the tip: keep the along-axis offset
            s = -float(r @ T)
        return s, np.array([r @ T, r @ U, r @ V])


chains = rig_json['chains']
ours = {k: Curve(chains[k]['joints'], chains[k]['radius']) for k in range(1, 6)}

# ---- our mesh: chain ownership and arc per vertex --------------------------------------------------------------------
bone_chain = {nm: ci for ci, c in enumerate(chains) for nm in c['names']}
gname = {g.index: g.name for g in body.vertex_groups}
gindex = {g.name: g.index for g in body.vertex_groups}
owner = np.array([bone_chain[gname[max(v.groups, key=lambda x: x.weight).group]] for v in me.vertices])
bm = bmesh.new(); bm.from_mesh(me)
deform = bm.verts.layers.deform.verify()
own_l = bm.verts.layers.int.new('chain_owner')          # survives reindexing; bisect vertices inherit from edge ends
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v[own_l] = int(owner[v.index])
part_layer = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
src_layer = bm.faces.layers.int.new('graft_src')          # 0 body, 1 new head (skull or stub), 2 zip
skull_out = bm.verts.layers.float.new('head_skull')        # 1 on the rigid skull of a new head (compose: H region)
app_layer = bm.faces.layers.int.new('appendage')          # k on faces of head k's separate pieces (fin membranes)
# loft texture coordinates (compose_hyd.loft_transfer): distance along the loft from the skull ring, and the point of
# our neck ring at the same angle round the loft (the neck surface the loft continues)
loft_s = bm.verts.layers.float.new('loft_s')
loft_ref = bm.verts.layers.float_vector.new('loft_ref')
for f in bm.faces:
    f[part_layer] = 0
uv_layers = list(bm.loops.layers.uv.values())
for layer in uv_layers:
    pass
bm.verts.ensure_lookup_table()
# per head: scale from the skull width against our neck width at 0.4 m from the tip (a plain stretch of neck)
SIGMA, S_CUT, LAT0 = {}, {}, {}
allco = np.array([tuple(v.co) for v in bm.verts]); allown = np.array([v[own_l] for v in bm.verts])
for k in range(1, 6):
    fit = json.load(open(os.path.join(HERE, 'work', 'heads', f'h{k}_fit.json')))
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend')) as (src, dst):
        dst.objects = [f'Head{k}']
    hco = np.array([tuple(v.co) for v in dst.objects[0].data.vertices]); bpy.data.objects.remove(dst.objects[0])
    nc = Curve(fit['centreline'], fit['radius']); tip = np.array(fit['tip'])
    _, Tn, Un, Vn, _ = nc.frame_at(0.0)
    r = hco - tip; skull = r[(r @ Tn) > -SKULL_N]
    new_w = np.percentile(skull @ Vn, 90) - np.percentile(skull @ Vn, 10)
    q, T, U, V, _ = ours[k].frame_at(0.4)
    ring = allco[(allown == k) & (np.abs((allco - q) @ T) < 0.02)] - q
    neck_w = np.percentile(ring @ V, 95) - np.percentile(ring @ V, 5)
    SIGMA[k] = HEAD_TO_NECK * neck_w / new_w * SCALE_FIX[k]
    LAT0[k] = 0.5 * new_w
    S_CUT[k] = SIGMA[k] * PIECE_N + LOFT        # our neck's cut (arc from our tip)
    print(f'SCALE head {k}: neck width {neck_w:.3f}, skull width {new_w * SIGMA[k]:.3f}, sigma {SIGMA[k]:.4f}, '
          f'neck cut at {S_CUT[k]:.3f}')
for k in range(1, 6):
    cv = ours[k]
    p0, T0, U0, V0, _ = cv.frame_at(S_CUT[k])
    sel = [v for v in bm.verts if v[own_l] == k]
    # bisect our neck at the cut plane (only the tube near the axis), then delete chain k in front of it
    near = [v for v in sel if np.linalg.norm(np.array(v.co) - p0) < 0.25]
    geom = list({e for v in near for e in v.link_edges}) + list({f for v in near for f in v.link_faces}) + near
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector(p0), plane_no=Vector(-T0))
    for v in res['geom_cut']:
        if isinstance(v, bmesh.types.BMVert):
            v[own_l] = k
    # the old head and upper neck: flood fill from the old snout tip through vertices in front of the cut (a test by
    # chain ownership alone also took the outer necks' ground runs in front of the plane)
    front = lambda v: (np.array(v.co) - p0) @ T0 > 1e-4
    tipv = min((v for v in bm.verts if v[own_l] == k), key=lambda v: np.linalg.norm(np.array(v.co) - cv.P[-1]))
    doomed = {tipv}; stack = [tipv]
    while stack:
        a_ = stack.pop()
        for e in a_.link_edges:
            b_ = e.other_vert(a_)
            if b_ not in doomed and front(b_):
                doomed.add(b_); stack.append(b_)
    # old horns and fins sweeping back past the cut, still attached to the neck behind it: protrusions in a narrow
    # band behind the cut (a wider band also took bulges of the outer necks' ground runs)
    for v in bm.verts:
        if v in doomed or v[own_l] != k:
            continue
        a_, r_ = cv.local(np.array(v.co))
        if (S_CUT[k] - 0.01 < a_ < S_CUT[k] + OLD_REACH
                and np.linalg.norm(r_[1:]) > OLD_PROTRUDE * cv.frame_at(a_)[4]):
            doomed.add(v)
    doomed = list(doomed)
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
# drop loose bits (old horn/fin crumbs)
bm.verts.ensure_lookup_table(); seen = set(); pieces = []
for v in bm.verts:
    if v in seen:
        continue
    stack = [v]; seen.add(v); piece = []
    while stack:
        a = stack.pop(); piece.append(a)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b not in seen:
                seen.add(b); stack.append(b)
    pieces.append(piece)
pieces.sort(key=len)
bmesh.ops.delete(bm, geom=[v for p in pieces[:-1] for v in p], context='VERTS')
print('BODY after head removal: triangles', sum(len(f.verts) - 2 for f in bm.faces), 'loose pieces dropped', len(pieces) - 1)


def ring_loop(edges):
    """Ordered vertex list of a closed boundary loop given its edges."""
    nbr = {}
    for e in edges:
        a, b = e.verts
        nbr.setdefault(a, []).append(b); nbr.setdefault(b, []).append(a)
    start = next(iter(nbr)); loop = [start]; prev = None; cur = start
    while True:
        nxt = [x for x in nbr[cur] if x is not prev]
        if not nxt or nxt[0] is start:
            break
        prev, cur = cur, nxt[0]; loop.append(cur)
        if len(loop) > len(nbr):
            break
    return loop


def boundary_loops(verts_filter):
    edges = [e for e in bm.edges if e.is_boundary and all(verts_filter(v) for v in e.verts)]
    loops = []; left = set(edges)
    while left:
        e = left.pop(); comp = {e}; stack = [e]
        while stack:
            a = stack.pop()
            for v in a.verts:
                for f in v.link_edges:
                    if f in left:
                        left.discard(f); comp.add(f); stack.append(f)
        loops.append(ring_loop(comp))
    return loops


def zip_rings(A, B, centre, axis):
    """Triangles between two closed rings around `axis` (A on the tip side): walk both by angle."""
    ref = np.array(A[0].co) - centre; ref -= (ref @ axis) * axis; ref /= np.linalg.norm(ref)
    side = np.cross(axis, ref)

    def ang(v):
        r = np.array(v.co) - centre
        return math.atan2(float(r @ side), float(r @ ref)) % (2 * math.pi)

    def order(R):
        a = [ang(v) for v in R]
        if np.sum(np.sign(np.diff(np.unwrap(a)))) < 0:
            R = R[::-1]; a = a[::-1]
        i = int(np.argmin(a)); R = R[i:] + R[:i]
        return R, [ang(v) for v in R]

    A, aa = order(A); B, ab = order(B)
    aa = aa + [aa[0] + 2 * math.pi]; ab = ab + [ab[0] + 2 * math.pi]
    i = j = 0; faces = []
    while i < len(A) or j < len(B):
        a0, a1 = A[i % len(A)], A[(i + 1) % len(A)]; b0, b1 = B[j % len(B)], B[(j + 1) % len(B)]
        if j >= len(B) or (i < len(A) and aa[i + 1] <= ab[j + 1]):
            faces.append((a0, b0, a1)); i += 1
        else:
            faces.append((a0, b0, b1)); j += 1
    made = []
    for tri in faces:
        if len(set(tri)) < 3:
            continue
        try:
            f = bm.faces.new(tri)
        except ValueError:
            continue
        made.append(f)
    # outward winding: the normal points away from the axis
    bmesh.ops.recalc_face_normals(bm, faces=made)
    for f in made:
        c = np.array(f.calc_center_median()) - centre; c -= (c @ axis) * axis
        if np.array(f.normal) @ c < 0:
            f.normal_flip()
    return made


def hermite(p0, m0, p1, m1, t):
    h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
    return h00 * p0 + h10 * m0 + h01 * p1 + h11 * m1


def ring_profile(loop, centre, U, V, samples):
    """Radius of a closed ring as a function of angle in the (U, V) plane, sampled at LOFT_SAMPLES angles."""
    P = np.array([np.array(v.co) for v in loop]) - centre
    ang = np.arctan2(P @ V, P @ U); rad = np.linalg.norm(P - np.outer(P @ np.cross(U, V), np.cross(U, V)), axis=1)
    o = np.argsort(ang); ang, rad = ang[o], rad[o]
    ang = np.concatenate([ang - 2 * np.pi, ang, ang + 2 * np.pi]); rad = np.tile(rad, 3)
    th = np.linspace(-np.pi, np.pi, samples, endpoint=False)
    return np.interp(th, ang, rad)


def loft(A, B, cA, dA, cB, dB):
    """Tube from ring A (centre cA, leaving along dA) to ring B (centre cB, arriving along dB): intermediate rings on a
    Hermite centreline with parallel-transported frames (twist matched to B linearly), cross-sections blended from
    A's to B's shape; zipped to both rings. Returns (faces, {vertex: t})."""
    L = float(np.linalg.norm(cB - cA)); n = max(2, int(round(L / LOFT_STEP)))
    # as many sides as the head ring (capped): a fan of long thin zip triangles from a dense ring to a sparse one
    # showed as a sawtooth under the jaws (user check 2026-10-09)
    samples = int(np.clip(len(A), LOFT_SAMPLES, LOFT_MAX))
    up = np.array([0, 0, 1.0])

    def frame(d, ref):
        u = ref - (ref @ d) * d
        if np.linalg.norm(u) < 1e-6:
            u = np.cross(d, [1, 0, 0])
        u /= np.linalg.norm(u); return u, np.cross(d, u)

    UA, VA = frame(dA, up); UB, VB = frame(dB, up)
    rA = ring_profile(A, cA, UA, VA, samples); rB = ring_profile(B, cB, UB, VB, samples)
    ts = np.linspace(0, 1, n + 1)[1:-1]
    C = [hermite(cA, dA * L, cB, dB * L, t) for t in ts]
    D = [(hermite(cA, dA * L, cB, dB * L, t + 1e-3) - hermite(cA, dA * L, cB, dB * L, t - 1e-3)) for t in ts]
    D = [d / np.linalg.norm(d) for d in D]
    # transport UA along the curve, then remove the residual twist against UB linearly
    Us = []; u = UA.copy(); prev = dA
    for d in D + [dB]:
        u = u - (u @ d) * d; u /= np.linalg.norm(u); Us.append(u); prev = d
    twist = math.atan2(float(np.cross(Us[-1], UB) @ dB), float(Us[-1] @ UB))
    th = np.linspace(-np.pi, np.pi, samples, endpoint=False)
    rings = []; tvals = {}
    for i, (c, d, t) in enumerate(zip(C, D, ts)):
        u = Us[i]; v = np.cross(d, u); a = twist * t
        u, v = u * math.cos(a) + v * math.sin(a), v * math.cos(a) - u * math.sin(a)
        w = smooth(t); r = (1 - w) * rA + w * rB
        ring = []
        for j, ang in enumerate(th):
            nv = bm.verts.new(Vector(c + r[j] * (math.cos(ang) * u + math.sin(ang) * v)))
            ring.append(nv); tvals[nv] = t
        rings.append(ring)
    faces = []
    for r0, r1 in zip(rings[:-1], rings[1:]):
        for j in range(samples):
            j1 = (j + 1) % samples
            for tri in ((r0[j], r1[j], r1[j1]), (r0[j], r1[j1], r0[j1])):
                faces.append(bm.faces.new(tri))
    mid = len(rings) // 2
    axis_mid = D[mid]; centre_mid = C[mid]
    for f in faces:
        c_ = np.array(f.calc_center_median()); k_ = int(np.argmin([np.linalg.norm(c_ - cc) for cc in C]))
        f.normal_update()
        out = c_ - C[k_]; out -= (out @ D[k_]) * D[k_]
        if np.array(f.normal) @ out < 0:
            f.normal_flip()
    # texture coordinates: the loft's frame turns into (UB, VB) at ring B, so angle j of every ring continues B's
    # surface at that angle; ring A's vertices take the B point at their angle in (UA, VA), ring B its own positions
    for ring in rings:
        for j, v_ in enumerate(ring):
            v_[loft_s] = tvals[v_] * L
            v_[loft_ref] = Vector(cB + rB[j] * (math.cos(th[j]) * UB + math.sin(th[j]) * VB))
    for v_ in A:
        r_ = np.array(v_.co) - cA; ang = math.atan2(float(r_ @ VA), float(r_ @ UA))
        v_[loft_s] = 0.0
        rad = float(np.interp(ang, th, rB, period=2 * np.pi))
        v_[loft_ref] = Vector(cB + rad * (math.cos(ang) * UB + math.sin(ang) * VB))
    for v_ in B:
        v_[loft_s] = L; v_[loft_ref] = v_.co.copy()
    faces += zip_rings(list(A), rings[0], (cA + C[0]) / 2, ((dA + D[0]) / 2) / np.linalg.norm((dA + D[0]) / 2))
    faces += zip_rings(rings[-1], list(B), (C[-1] + cB) / 2, ((D[-1] + dB) / 2) / np.linalg.norm((D[-1] + dB) / 2))
    return faces, tvals


def components(bmesh_, verts=None):
    verts = list(bmesh_.verts) if verts is None else verts
    seen = set(); out = []
    for v in verts:
        if v in seen:
            continue
        stack = [v]; seen.add(v); piece = []
        while stack:
            a_ = stack.pop(); piece.append(a_)
            for e in a_.link_edges:
                b_ = e.other_vert(a_)
                if b_ not in seen:
                    seen.add(b_); stack.append(b_)
        out.append(piece)
    return out


report = {}
HIGH = []
new_all = set()
for k in range(1, 6):
    fit = json.load(open(os.path.join(HERE, 'work', 'heads', f'h{k}_fit.json')))
    sigma = SIGMA[k]; nc = Curve(fit['centreline'], fit['radius']); oc = ours[k]
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend')) as (src, dst):
        dst.objects = [f'Head{k}']
    head = dst.objects[0]; bpy.context.scene.collection.objects.link(head)
    hm = head.data
    # ---- cut behind the skull (in the head's own frame)
    hb = bmesh.new(); hb.from_mesh(hm); bmesh.ops.triangulate(hb, faces=hb.faces)
    pc, Tc, Uc, Vc, rc = nc.frame_at(CUT_N[k])
    loc = {v: nc.local(np.array(v.co)) for v in hb.verts}
    near_axis = lambda v: np.linalg.norm(loc[v][1][1:]) < CUT_AXIS * nc.frame_at(max(loc[v][0], 0))[4] \
        if v in loc else True
    near = [v for v in hb.verts if near_axis(v) and abs((np.array(v.co) - pc) @ Tc) < 4 * rc]
    geom = list({e for v in near for e in v.link_edges}) + list({f for v in near for f in v.link_faces}) + near
    bmesh.ops.bisect_plane(hb, geom=geom, dist=1e-6, plane_co=Vector(pc), plane_no=Vector(Tc))
    behind = lambda v: (np.array(v.co) - pc) @ Tc < -1e-6
    bmesh.ops.delete(hb, geom=[v for v in hb.verts if behind(v) and near_axis(v)], context='VERTS')
    # keep pieces reaching in front of the cut (skull, fins, horns); drop the rest (dorsal spines behind the cut)
    pp, Tp = nc.frame_at(PIECE_N)[:2]
    for piece in components(hb):
        if len(piece) < 30 or all((np.array(v.co) - pp) @ Tp < 0 for v in piece):
            bmesh.ops.delete(hb, geom=piece, context='VERTS')
    # the main ring: the boundary loop nearest the cut centre; every other open loop (spine stumps) is capped
    bnd = [e for e in hb.edges if e.is_boundary]
    loops = []; left = set(bnd)
    while left:
        e = left.pop(); comp = {e}; stack = [e]
        while stack:
            a_ = stack.pop()
            for v in a_.verts:
                for f in v.link_edges:
                    if f in left:
                        left.discard(f); comp.add(f); stack.append(f)
        loops.append(comp)
    main_loop = min(loops, key=lambda l: np.linalg.norm(np.mean([np.array(v.co) for e in l for v in e.verts], 0) - pc)
                    + 0.0 * len(l))
    for l in loops:
        if l is not main_loop and len(l) < 0.5 * len(main_loop):
            bmesh.ops.holes_fill(hb, edges=list(l), sides=0)
    bmesh.ops.triangulate(hb, faces=[f for f in hb.faces if len(f.verts) > 3])
    hb.to_mesh(hm); hb.free(); hm.update()
    # ---- decimate the head to its budget (sharp spikes keep their tips best with the plain collapse)
    for o in bpy.context.view_layer.objects:
        o.select_set(o is head)
    bpy.context.view_layer.objects.active = head
    total = sum(len(p.vertices) - 2 for p in hm.polygons)
    if BUDGET[k - 1] and total > BUDGET[k - 1]:
        m = head.modifiers.new('dec', 'DECIMATE'); m.ratio = BUDGET[k - 1] / total
        bpy.ops.object.modifier_apply(modifier=m.name)
    hb = bmesh.new(); hb.from_mesh(hm); bmesh.ops.triangulate(hb, faces=hb.faces)
    # ---- rigid placement
    tipn = np.array(fit['tip']); _, Tn0, Un0, Vn0, _ = nc.frame_at(0.0); po0, To0, Uo0, Vo0, _ = oc.frame_at(0.0)
    Mn = np.stack([Tn0, Un0, Vn0]); Mo = np.stack([To0, Uo0, Vo0]); R0 = Mo.T @ Mn

    def place(p):
        q = p - tipn
        if k in LAT_SQUEEZE:
            # far-lateral parts (fins, side spikes) pulled toward the skull so the heads clear each other
            lat = float(q @ Vn0); half = LAT0[k]
            if abs(lat) > half:
                q = q - Vn0 * (lat - np.sign(lat) * (half + (abs(lat) - half) * LAT_SQUEEZE[k]))
        return po0 + sigma * (R0 @ q)

    vmap = {}
    for v in hb.verts:
        a_, r_ = nc.local(np.array(v.co))
        nv = bm.verts.new(Vector(place(np.array(v.co)))); vmap[v] = nv
        nv[deform].clear(); nv[deform][gindex[f'Head{k}']] = 1.0
        nv[skull_out] = 1.0 if (a_ < SPLIT_N or np.linalg.norm(r_[1:]) > 1.6 * nc.frame_at(max(a_, 0))[4]) else 0.0
    pieces = components(hb)
    main_piece = set(max(pieces, key=lambda p_: max(nc.local(np.array(v.co))[0] for v in p_)))
    for f in hb.faces:
        try:
            nf = bm.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[part_layer] = k; nf.smooth = True; nf[src_layer] = 1
        nf[app_layer] = 0 if f.verts[0] in main_piece else k
    head_faces = len(hb.faces)
    # ---- the high-res retextured head (bake source), the same rigid placement
    hi_path = os.path.join(HERE, 'meshy', f'head{k}_retexture_v2', 'model_urls_glb.glb')
    if os.path.exists(hi_path):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=hi_path)
        added = set(bpy.data.objects) - before
        hi = next(o for o in added if o.type == 'MESH')
        for o in added:
            if o is not hi:
                bpy.data.objects.remove(o, do_unlink=True)
        hi.parent = None
        for o in bpy.context.view_layer.objects:
            o.select_set(o is hi)
        bpy.context.view_layer.objects.active = hi
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        # Meshy returns the upload centred and scaled to a 2-unit box: undo it from the upload's own box
        with bpy.data.libraries.load(os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend')) as (src, dst):
            dst.objects = [f'Head{k}_upload']
        Up = np.array([tuple(v.co) for v in dst.objects[0].data.vertices]); bpy.data.objects.remove(dst.objects[0])
        Hc = np.array([tuple(v.co) for v in hi.data.vertices])
        scale = (Up.max(0) - Up.min(0)).max() / (Hc.max(0) - Hc.min(0)).max()
        shift = (Up.max(0) + Up.min(0)) / 2 - scale * (Hc.max(0) + Hc.min(0)) / 2
        hi.data.transform(Matrix.Translation(Vector(shift)) @ Matrix.Scale(scale, 4))
        for v in hi.data.vertices:
            v.co = Vector(place(np.array(v.co)))
        hi.data.update()
        hi.name = f'HeadHi{k}'; HIGH.append(hi)
    # ---- loft from the skull ring to our neck ring
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    new_set = set(vmap.values()); new_all |= new_set
    cA0 = place(pc); dA = R0 @ (-Tc); dA /= np.linalg.norm(dA)            # away from the tip, along the Meshy neck
    pB, TB, _, _, _ = oc.frame_at(S_CUT[k]); dB = -TB
    def on_plane(loop, c, d):
        """Loop lying on the cut plane (point c, normal d): mean plane distance, used to pick the cut ring."""
        P = np.array([np.array(v.co) for v in loop])
        return float(np.abs((P - c) @ d).mean())

    loops_new = [l for l in boundary_loops(lambda v: v in new_set) if len(l) >= 6]
    A = max([l for l in loops_new if on_plane(l, cA0, dA) < 0.004] or loops_new, key=len)
    loops_old = [l for l in boundary_loops(lambda v: v not in new_set and np.linalg.norm(np.array(v.co) - pB) < 0.2)
                 if len(l) >= 6]
    B = max([l for l in loops_old if on_plane(l, pB, TB) < 0.004] or loops_old, key=len)
    cA = np.mean([np.array(v.co) for v in A], 0); cB = np.mean([np.array(v.co) for v in B], 0)
    lfaces, tvals = loft(A, B, cA, dA, cB, dB)
    for f in lfaces:
        f[part_layer] = 0; f.smooth = True; f[src_layer] = 2; f[app_layer] = 0
    # weights: Head<k> at the skull ring blending into our neck's weights at the ring B
    bw = {}
    for v in B:
        for g, w in v[deform].items():
            bw[g] = bw.get(g, 0.0) + w / len(B)
    for v, t in tvals.items():
        dv = v[deform]; w = smooth(t)
        dv[gindex[f'Head{k}']] = 1.0 - w
        for g, x in bw.items():
            dv[g] = dv.get(g, 0.0) + w * x
        v[skull_out] = 0.0
    lv = set(tvals) | set(A) | set(B)
    lv |= {e.other_vert(v) for v in list(set(tvals)) for e in v.link_edges}
    inner = [v for v in lv if v in tvals]
    for _ in range(ZIP_RELAX):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    report[k] = {'sigma': round(sigma, 4), 'head triangles': head_faces, 'loft triangles': len(lfaces),
                 'rings': (len(A), len(B)), 'loft length': round(float(np.linalg.norm(cB - cA)), 3)}
    hb.free(); bpy.data.objects.remove(head, do_unlink=True)

# holes left by removing old protrusions (not the five neck joints, which the lofts closed)
# (open edges on the new heads are Meshy's own: fin membranes and mouth interiors are single sheets; they stay open)
bnd = [e for e in bm.edges if e.is_boundary and not any(v in new_all for v in e.verts)]
for l in boundary_loops(lambda v: v not in new_all):
    c = np.mean([np.array(v.co) for v in l], 0)
    print('OPEN body loop', len(l), 'at', c.round(3))
if bnd and not os.environ.get('NO_CAP'):
    res = bmesh.ops.holes_fill(bm, edges=bnd, sides=0)
    print('CAPPED', len(bnd), 'boundary edges with', len(res['faces']), 'faces')
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
for p in me.polygons:
    p.use_smooth = True
print('GRAFT', json.dumps(report))
print('TOTAL triangles', sum(len(p.vertices) - 2 for p in me.polygons),
      'unweighted', sum(1 for v in me.vertices if not v.groups))
if HIGH:
    # bake sources into their own file: work/heads_hi.blend (objects HeadHi<k>, textured)
    hi_scene = bpy.data.scenes.new('HeadsHi')
    for o in HIGH:
        bpy.context.scene.collection.objects.unlink(o); hi_scene.collection.objects.link(o)
    bpy.data.libraries.write(os.path.join(HERE, 'work', 'heads_hi.blend'), set(HIGH), fake_user=True)
    for o in HIGH:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.scenes.remove(hi_scene)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
