"""Graft the five prepared head models (head_prep.py: work/heads/h<k>_st.blend 'Head<k>', cut behind the skull,
decimated and unwrapped; h<k>_fit.json) onto the rigged body (work/rig_v1.blend, rig.json), after
mm6_hyd_claude/scripts/graft_heads.py (multi-headed-creature notes of the quadruped playbook).

Per head k:
  - placement, rigid: snout tip onto our chain's tip, the head's forward (-Y) onto our Head<k> bone, its up (+Z) onto
    world up made perpendicular; scale sigma = HEAD_TO_NECK x our neck width / the skull's width (x 10-90 percentile),
    times SCALE_FIX[k];
  - our neck is cut where the placed head's cut ring sits plus LOFT further back (along our chain); the old head in
    front of it goes by a flood fill from the old snout;
  - a lofted tube joins the head's cut ring (A) to our neck's cut ring (B): a Hermite centreline leaving the head along
    its own neck direction and arriving along ours, cross-sections blended between the two ring shapes, zipped to both;
  - weights: the head rigid on Head<k>; the loft blends from Head<k> at A to ring B's weights;
  - UVs: the head keeps its own unwrap in the loop layer 'HeadUV' (the retexture of texturing/head<k>_upload.glb maps
    through it); face attribute 'part' = k on head faces, 0 on the body and lofts (body texture).
Writes the given blend. Args: -- <out.blend>"""
import bpy, bmesh, json, math, os, sys
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index('--') + 1]
HEAD_TO_NECK = float(os.environ.get('HEAD_TO_NECK', '1.4'))
SCALE_FIX = {1: 1.0, 2: 0.72, 3: 0.88, 4: 0.92, 5: 0.95}   # relative head sizes of the native front view
LOFT, LOFT_STEP = 0.06, 0.025
LOFT_MAX = 32
LOFT_SAMPLES = 24
ZIP_RELAX = 3
MAX_PITCH = math.radians(15)
TAN_A, RAD_T = 0.3, 0.6
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig_json = json.load(open(os.path.join(HERE, 'work', 'rig.json')))
body = bpy.data.objects['Body']; rig = bpy.data.objects['Rig']; me = body.data


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
    # short tangent at the head ring: a full-length one bulged the tube out behind the skull into a bald dome
    mA = dA * L * TAN_A
    C = [hermite(cA, mA, cB, dB * L, t) for t in ts]
    D = [(hermite(cA, mA, cB, dB * L, t + 1e-3) - hermite(cA, mA, cB, dB * L, t - 1e-3)) for t in ts]
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
        w = smooth(min(1.0, t / RAD_T)); r = (1 - w) * rA + w * rB     # down to the neck radius early
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



chains = rig_json['chains']
ours = {k: Curve(chains[k]['joints'], chains[k]['radius']) for k in range(1, 6)}
gindex = {g.name: g.index for g in body.vertex_groups}
owner = np.zeros(len(me.vertices), np.int32); me.attributes['chain_owner'].data.foreach_get('value', owner)
bm = bmesh.new(); bm.from_mesh(me)
deform = bm.verts.layers.deform.verify()
own_l = bm.verts.layers.int.get('chain_owner')
part_layer = bm.faces.layers.int.get('part') or bm.faces.layers.int.new('part')
for f in bm.faces:
    f[part_layer] = 0
huv = bm.loops.layers.uv.get('HeadUV') or bm.loops.layers.uv.new('HeadUV')
loft_s = bm.verts.layers.float.new('loft_s')
loft_ref = bm.verts.layers.float_vector.new('loft_ref')
bm.verts.ensure_lookup_table()
allco = np.array([tuple(v.co) for v in bm.verts]); allown = np.array([v[own_l] for v in bm.verts])

HEADS = {}
for k in range(1, 6):
    fit = json.load(open(os.path.join(HERE, 'work', 'heads', f'h{k}_fit.json')))
    with bpy.data.libraries.load(os.path.join(HERE, 'work', 'heads', f'h{k}_st.blend')) as (src, dst):
        dst.objects = [f'Head{k}']
    head = dst.objects[0]
    hco = np.array([tuple(v.co) for v in head.data.vertices])
    tip = np.array(fit['tip']); pcut = np.array(fit['cut']['point']); ncut = np.array(fit['cut']['normal'])
    # skull width across the cheeks (a slice behind the snout at mouth height; fins, horns and crests excluded)
    cheek = hco[(hco[:, 1] > tip[1] + 0.12) & (hco[:, 1] < tip[1] + 0.30) & (np.abs(hco[:, 2] - tip[2]) < 0.12)]
    head_w = np.percentile(cheek[:, 0], 95) - np.percentile(cheek[:, 0], 5)
    cv = ours[k]
    q, T, U, V, _ = cv.frame_at(0.4)
    ring = allco[(allown == k) & (np.abs((allco - q) @ T) < 0.02) & (np.linalg.norm(allco - q, axis=1) < 0.3)] - q
    neck_w = np.percentile(ring @ V, 95) - np.percentile(ring @ V, 5)
    sigma = HEAD_TO_NECK * neck_w / head_w * SCALE_FIX[k]
    po, To, Uo, Vo, _ = cv.frame_at(0.0)                         # our frame at the snout: T toward the tip
    pitch = math.asin(max(-1.0, min(1.0, float(To[2]))))
    if pitch < -MAX_PITCH:                                        # the old heads hang their snouts; the masters look ahead
        h = np.array([To[0], To[1], 0.0]); h /= np.linalg.norm(h)
        To = h * math.cos(MAX_PITCH) + np.array([0, 0, -math.sin(MAX_PITCH)])
        Uo = np.array([0, 0, 1.0]) - To[2] * To; Uo /= np.linalg.norm(Uo)
    Mh = np.array([[0, -1.0, 0], [0, 0, 1.0], [-1.0, 0, 0]])     # head frame rows: forward -Y, up +Z, forward x up
    Mo = np.stack([To, Uo, np.cross(To, Uo)])
    R0 = Mo.T @ Mh
    place = (lambda R0, po, tip, sigma: (lambda p: po + sigma * (R0 @ (np.asarray(p) - tip))))(R0, po, tip, sigma)
    # our neck cut: arc of the placed cut point along our chain, plus LOFT
    s_ring, _ = cv.local(place(np.array(fit['cut']['ring_centre'])))
    HEADS[k] = dict(obj=head, ring_centre=fit['cut']['ring_centre'], sigma=sigma, place=place, R0=R0, pcut=pcut, ncut=ncut, s_cut=s_ring + LOFT)
    print(f'SCALE head {k}: neck width {neck_w:.3f} m, skull width {head_w * sigma:.3f} m, sigma {sigma:.4f}, '
          f'ring at arc {s_ring:.3f}, neck cut at {s_ring + LOFT:.3f}')

# ---- remove the old heads: our necks cut at s_cut, flood fill from the old snout through the front side
for k in range(1, 6):
    cv = ours[k]; S = HEADS[k]['s_cut']
    p0, T0, _, _, _ = cv.frame_at(S)
    near = [v for v in bm.verts if v[own_l] == k and np.linalg.norm(np.array(v.co) - p0) < 0.3]
    geom = list({e for v in near for e in v.link_edges}) + list({f for v in near for f in v.link_faces}) + near
    res = bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-5, plane_co=Vector(p0), plane_no=Vector(-T0))
    for v in res['geom_cut']:
        if isinstance(v, bmesh.types.BMVert):
            v[own_l] = k
    front = lambda v: v[own_l] == k and (np.array(v.co) - p0) @ T0 > 1e-4      # leaks through fused old heads otherwise
    tipv = min((v for v in bm.verts if v[own_l] == k), key=lambda v: np.linalg.norm(np.array(v.co) - cv.P[-1]))
    doomed = {tipv}; stack = [tipv]
    while stack:
        a_ = stack.pop()
        for e in a_.link_edges:
            b_ = e.other_vert(a_)
            if b_ not in doomed and front(b_):
                doomed.add(b_); stack.append(b_)
    print('CUT neck', k, 'removed', len(doomed), 'owners left', {j: sum(1 for v in bm.verts if v[own_l] == j) - sum(1 for v in doomed if v[own_l] == j) for j in range(6)})
    bmesh.ops.delete(bm, geom=list(doomed), context='VERTS')
# crumbs: small loose remnants of the old heads lying in front of a neck's cut plane (a rule by distance alone deleted
# neck 1, a separate Meshy shell, once its upper half was cut away)
cutp = [ours[k].frame_at(HEADS[k]['s_cut'])[:2] for k in range(1, 6)]
small = [p for p in components(bm) if len(p) < 400 and
         any((np.mean([np.array(v.co) for v in p], 0) - c) @ T > 0.0 for c, T in cutp)
         and not any(v[own_l] == k + 1 and (np.array(v.co) - cutp[k][0]) @ cutp[k][1] < 0 for v in p for k in range(5))]
for p in small:
    bmesh.ops.delete(bm, geom=p, context='VERTS')
print('BODY after head removal: triangles', sum(len(f.verts) - 2 for f in bm.faces), 'crumbs dropped', len(small))

report = {}; new_all = set()
for k in range(1, 6):
    H = HEADS[k]; head = H['obj']; hm = head.data; place = H['place']; R0 = H['R0']; oc = ours[k]
    hb = bmesh.new(); hb.from_mesh(hm)
    huv_src = hb.loops.layers.uv.active
    vmap = {}
    for v in hb.verts:
        nv = bm.verts.new(Vector(place(np.array(v.co)))); vmap[v] = nv
        nv[deform].clear(); nv[deform][gindex[f'Head{k}']] = 1.0; nv[own_l] = k
    for f in hb.faces:
        try:
            nf = bm.faces.new([vmap[v] for v in f.verts])
        except ValueError:
            continue
        nf[part_layer] = k; nf.smooth = True
        for l_src, l_dst in zip(f.loops, nf.loops):
            l_dst[huv].uv = l_src[huv_src].uv
    new_set = set(vmap.values()); new_all |= new_set
    bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table()
    pcp = place(H['pcut']); dA = R0 @ (-H['ncut']); dA /= np.linalg.norm(dA)
    pB, TB, _, _, _ = oc.frame_at(H['s_cut']); dB = -TB

    def on_plane(loop, c, d):
        P = np.array([np.array(v.co) for v in loop])
        return float(np.abs((P - c) @ d).mean())

    def extent(loop):
        P = np.array([np.array(v.co) for v in loop]); return float(np.linalg.norm(P.max(0) - P.min(0)))
    loops_new = [l for l in boundary_loops(lambda v: v in new_set) if len(l) >= 6]
    rcen = place(np.array(H['ring_centre']))
    A = min(loops_new, key=lambda l: np.linalg.norm(np.mean([np.array(v.co) for v in l], 0) - rcen) - 0.2 * extent(l))
    loops_old = [l for l in boundary_loops(lambda v: v not in new_set and np.linalg.norm(np.array(v.co) - pB) < 0.3)
                 if len(l) >= 6]
    B = max([l for l in loops_old if on_plane(l, pB, TB) < 0.004] or loops_old, key=len)
    cA = np.mean([np.array(v.co) for v in A], 0); cB = np.mean([np.array(v.co) for v in B], 0)
    lfaces, tvals = loft(A, B, cA, dA, cB, dB)
    for f in lfaces:
        f[part_layer] = 0; f.smooth = True
    bw = {}
    for v in B:
        for g, w in v[deform].items():
            bw[g] = bw.get(g, 0.0) + w / len(B)
    for v, t in tvals.items():
        dv = v[deform]; w = smooth(t)
        dv[gindex[f'Head{k}']] = 1.0 - w
        for g, x in bw.items():
            dv[g] = dv.get(g, 0.0) + w * x
        v[own_l] = k
    inner = [v for v in tvals]
    for _ in range(ZIP_RELAX):
        bmesh.ops.smooth_vert(bm, verts=inner, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    report[k] = {'sigma': round(H['sigma'], 4), 'head triangles': len(hb.faces), 'loft triangles': len(lfaces),
                 'rings': (len(A), len(B)), 'loft length': round(float(np.linalg.norm(cB - cA)), 3)}
    hb.free(); bpy.data.objects.remove(head, do_unlink=True)

bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.normal_update()
bm.to_mesh(me); bm.free(); me.update()
for p in me.polygons:
    p.use_smooth = True
print('GRAFT', json.dumps(report))
print('TOTAL triangles', sum(len(p.vertices) - 2 for p in me.polygons),
      'unweighted', sum(1 for v in me.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(OUT))
