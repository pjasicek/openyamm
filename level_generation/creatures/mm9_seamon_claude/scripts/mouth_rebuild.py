"""Mouth rebuild for the Sea Monster (2026-10-30 review: lower teeth through the face when the jaw closes, torn
slivers at the mouth corners, a flat stretched panel inside the open mouth). Runs after symmetrize_head.py.

Args: <symmetrized blend (symmetrize_head.py)> <out blend> <report json>

Causes (see README "Mouth rebuild"):
- MM9's jaw joint (Bone08) sits 0.4 m behind and 0.12 m below the corners of the Meshy mouth, so the 33-41 degree
  closing of standwater/attacks swung the front of our lower jaw (and its teeth) up through the snout and the
  front of the jaw's root up through the cheeks and eyes;
- Meshy's mouth interior is a shallow wedge (a flat floor panel up to the palate); symmetrize_head.py has already
  removed the thread triangles across the corners and the broken right eye.

Steps:
1. Closure range from the MM9 source clips of every role (Death only up to build_export's cut).
2. Teeth and eyeballs: the head's small pieces; lower teeth by the rig's jaw weight (the corner tooth with a mixed
   weight by its tip direction).
3. Mouth interior: the jaw is closed virtually (PROBE_*), faces that then see little sky (hemisphere rays) are inside;
   grown from the most enclosed face, plus adjacent slivers and leftover islands; deleted.
4. Lip loop (largest hole), its two corners (rear-most loop vertex per side), upper/lower halves.
5. Jaw pivot = mid-point of the corners: Bone08 moves there (orientation kept; the clips rotate it unchanged).
6. Jaw weights: below the plane through the pivot that bisects the bind gape -> Bone08, above -> Bone07, faded out
   behind the pivot; only the existing Bone07+Bone08 share is redistributed.
7. Gape: the jaw is closed virtually in 1 degree steps until lower skin/teeth first touch upper skin/teeth (BVH
   overlap; the lower teeth meet the upper lip first, at 55 degrees); the jaw is pre-rotated so that contact sits at
   the clips' largest closure + MARGIN_DEG (the bite snaps shut without overlap, standing keeps a small gap).
8. Cavity: rings from the lip loop (lip roll, gum, palate/floor dome, tongue) to a throat point behind the pivot,
   deeper rings coarser (about square triangles), stitched by u;
   upper half on Bone07, lower half on Bone08 fading into Bone07 toward the throat; own UV rect (UV_RECT,
   u: 0 corner A, 0.5 corner B (upper half), 1 back to A (lower half); v: 0 lip .. 1 throat).
9. Teeth reseated along their axes so a quarter of each tooth sits under the gum; rigid on Bone07/Bone08.
10. Back/tail spines (and the forehead spike): per vertex the weights of the nearest body vertex (stay rooted).
Labels: vertex groups 'Mouth' (cavity) and 'Eye', int point attribute 'mlab' (0 skin, 1 cavity, 2 upper teeth,
3 lower teeth, 4 eye) for mouth_gates.py and compose_sea.py.
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import clips_mm9 as C

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
CUT_S = 0.45                       # build_export.py: Death keeps diewater2 up to here
PROBE_PIVOT, PROBE_DEG = (-1.57, 0.47), 45.0   # rough closure for the interior probe only (y, z)
OPEN_T = 0.35                      # interior: fraction of escaping hemisphere rays below this
HEAD_Y = -1.2                      # head region: y below this
MARGIN_DEG = 1.0
SPLIT = float(os.environ.get("MOUTH_SPLIT", 0.05))        # half width of the upper/lower weight transition (m)
BACK_FADE = float(os.environ.get("MOUTH_BACK", 0.32))    # jaw weight fades out this far behind the pivot (m)
THROAT = (0.10, -0.03)             # throat point behind / below the pivot (y, z offsets)
LIP_ROLL, GUM = (0.018, 0.012), (0.032, 0.035)   # (inward, deeper) offsets of the first two rings
RING_T = (0.14, 0.32, 0.5, 0.68, 0.84)          # depth fractions gum -> throat of the deeper rings
BULGE, TONGUE_H = 0.045, 0.045
UV_RECT = (0.15, 0.915, None, 0.995)            # free strip of the Smart-UV atlas: u0, v0, (u1 from the aspect), v1
SINK = 0.25                                     # tooth length fraction under the gum

bpy.ops.wm.open_mainfile(filepath=IN)
sc = bpy.context.scene
rig = bpy.data.objects['MM9_Rig']
ob = bpy.data.objects['Body']
me = ob.data
if rig.animation_data:
    rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
bpy.context.view_layer.update()
rep = {}

# ---------------------------------------------------------------- 1. closure range of the MM9 clips
fps_mm9 = sc.render.fps / sc.render.fps_base
B7, B8 = rig.data.bones['Bone07'], rig.data.bones['Bone08']
rest_rel = B7.matrix_local.inverted() @ B8.matrix_local
R8 = B8.matrix_local.to_3x3()


def closure_series(action, t_max=None):
    rig.animation_data_create()
    rig.animation_data.action = action
    try:
        rig.animation_data.action_slot = action.slots[0]
    except Exception:
        pass
    f0, f1 = (int(round(x)) for x in action.frame_range)
    out = []
    for f in range(f0, f1 + 1):
        if t_max is not None and (f - f0) / fps_mm9 > t_max + 1e-6:
            break
        sc.frame_set(f)
        rel = rig.pose.bones['Bone07'].matrix.inverted() @ rig.pose.bones['Bone08'].matrix
        X = rest_rel.inverted() @ rel
        fr = (R8 @ X.to_3x3() @ R8.inverted()) @ Vector((0, -1, 0))
        out.append(math.degrees(math.atan2(fr.z, -fr.y)))
    return out


closures = {}
for role, (sources, _loop) in C.SEA.items():
    for s in sources:
        closures[s] = closure_series(bpy.data.actions[s], CUT_S if role == 'Death' else None)
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis.identity()
sc.frame_set(0)
bpy.context.view_layer.update()
MAX_CLOSE = max(max(v) for v in closures.values())
MAX_OPEN = min(min(v) for v in closures.values())
rep['closure_deg'] = {k: [round(min(v), 1), round(max(v), 1)] for k, v in closures.items()}
rep['max_close_deg'], rep['max_open_deg'] = round(MAX_CLOSE, 2), round(MAX_OPEN, 2)

# ---------------------------------------------------------------- 2. pieces: teeth, eyeball
gi = {g.name: g.index for g in ob.vertex_groups}
for name in ('Bone07', 'Bone08'):
    if name not in gi:
        ob.vertex_groups.new(name=name)
        gi[name] = ob.vertex_groups[name].index
n = len(me.vertices)
names = [g.name for g in ob.vertex_groups]
W = np.zeros((n, len(names)))
for v in me.vertices:
    for g in v.groups:
        W[v.index, g.group] = g.weight
J7, J8 = gi['Bone07'], gi['Bone08']
piece = np.array([d.value for d in me.attributes['piece'].data])
P0 = np.array([v.co[:] for v in me.vertices])
adj = [[] for _ in range(n)]
for e in me.edges:
    a, b = e.vertices
    adj[a].append(b); adj[b].append(a)
comp = -np.ones(n, int)
comps = []
for s in range(n):
    if comp[s] >= 0 or piece[s] != 2:
        continue
    st, ids = [s], [s]
    comp[s] = len(comps)
    while st:
        x = st.pop()
        for y in adj[x]:
            if comp[y] < 0:
                comp[y] = len(comps); st.append(y); ids.append(y)
    comps.append(np.array(ids))
teeth_up, teeth_low, eyes = [], [], []
tooth_axis = {}
for k, ids in enumerate(comps):
    p = P0[ids]
    cen = p.mean(0)
    if cen[1] > -1.3 or cen[2] > 0.9:
        continue                      # spines and the forehead spike
    q = p - cen
    ev, evec = np.linalg.eigh(q.T @ q)
    ax = evec[:, -1]
    elong = math.sqrt(ev[-1] / max(ev[-2], 1e-12))
    t = q @ ax
    # base = the wider end (cross-section spread), tip = the narrow end
    lo, hi = t < np.percentile(t, 25), t > np.percentile(t, 75)
    spread = lambda m: np.linalg.norm(q[m] - np.outer(t[m], ax), axis=1).mean() if m.any() else 0
    if spread(hi) > spread(lo):
        ax, t = -ax, -t
    rep.setdefault('pieces', []).append([np.round(cen, 3).tolist(), round(elong, 2), round(float(ax[2]), 2)])
    if elong < 1.6 and cen[2] > 0.58:
        eyes.append(k)
        continue
    tooth_axis[k] = (ax, t.min(), t.max(), cen)
    jw = float(W[ids, J8].mean())     # the rig's labels; the corner tooth (jaw 0.26) by its direction
    (teeth_low if jw > 0.85 or (jw > 0.15 and ax[2] > 0) else teeth_up).append(k)
rep['teeth'] = {'upper': len(teeth_up), 'lower': len(teeth_low), 'eyes': len(eyes)}
eye_ids = np.concatenate([comps[k] for k in eyes]) if eyes else np.zeros(0, int)

# ---------------------------------------------------------------- 3. interior faces (closed-jaw openness)
jaw0 = W[:, J8]
piv0 = Vector((0, *PROBE_PIVOT))
Rp = Matrix.Rotation(math.radians(-PROBE_DEG), 3, 'X')
Pc = [Vector(p).lerp(Rp @ (Vector(p) - piv0) + piv0, float(w)) for p, w in zip(P0, jaw0)]
bm = bmesh.new()
bm.from_mesh(me)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
pl = bm.verts.layers.int['piece']
cl = bm.verts.layers.int['chain']
uvl = bm.loops.layers.uv.active
bvh = BVHTree.FromPolygons(Pc, [[v.index for v in f.verts] for f in bm.faces])
rng = np.random.default_rng(3)
dirs = rng.normal(size=(64, 3)); dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
openness = np.ones(len(bm.faces))
is_body = np.array([all(v[pl] == 0 for v in f.verts) for f in bm.faces])
fcen = np.array([f.calc_center_median()[:] for f in bm.faces])
head_face = is_body & (fcen[:, 1] < HEAD_Y) & (np.array([np.mean([W[v.index, J7] + W[v.index, J8] for v in f.verts])
                                                         for f in bm.faces]) > 0.5)
for f in bm.faces:
    if not head_face[f.index]:
        continue
    vs = [Pc[v.index] for v in f.verts]
    c = sum(vs, Vector()) / len(vs)
    nn = (vs[1] - vs[0]).cross(vs[2] - vs[0])
    if nn.length < 1e-12:
        openness[f.index] = 0.0
        continue
    nn.normalize()
    free = 0
    for d in dirs:
        d = Vector(d)
        if d.dot(nn) < 0:
            d = -d
        if bvh.ray_cast(c + nn * 0.002 + d * 0.001, d, 4.0)[0] is None:
            free += 1
    openness[f.index] = free / len(dirs)


def aspect(f):
    vs = [v.co for v in f.verts]
    L = max((vs[i] - vs[i - 1]).length for i in range(len(vs)))
    return L * L / max(2 * f.calc_area(), 1e-12)


seed = min((f for f in bm.faces if head_face[f.index]), key=lambda f: openness[f.index])
region = {seed.index}
st = [seed]
while st:
    f = st.pop()
    for e in f.edges:
        for g in e.link_faces:
            if g.index not in region and head_face[g.index] and openness[g.index] < OPEN_T:
                region.add(g.index); st.append(g)
for _ in range(3):   # adjacent slivers (the threads across the corners)
    add = {g.index for i in list(region) for e in bm.faces[i].edges for g in e.link_faces
           if g.index not in region and is_body[g.index] and fcen[g.index][1] < HEAD_Y and aspect(g) > 10}
    region |= add
# leftover thread triangles across the corners (symmetrize_head.py removes Meshy's loose webs)
tvs = np.concatenate([P0[comps[k]] for k in teeth_up])
CX0 = float((tvs[:, 0].max() + tvs[:, 0].min()) / 2)


def in_mouth_zone(c):
    return -1.95 < c[1] < -1.45 and 0.25 < c[2] < 0.75 and abs(c[0] - CX0) > 0.05


threads = set()
for f in bm.faces:
    if not is_body[f.index] or not in_mouth_zone(fcen[f.index]):
        continue
    L_ = max(e.calc_length() for e in f.edges)
    if (L_ > 0.15 and aspect(f) > 5) or aspect(f) > 12:
        threads.add(f.index)
rep['threads'] = len(threads)
region |= threads
for _ in range(4):   # concavities: faces with two region neighbours
    add = set()
    for f in bm.faces:
        if f.index in region or not head_face[f.index]:
            continue
        if sum(1 for e in f.edges for g in e.link_faces if g.index in region) >= 2:
            add.add(f.index)
    region |= add
rep['interior_faces'] = len(region)
# right eye: socket slivers near the mirrored eyeball position join the deletion (crater rim)
CX = None
# ---------------------------------------------------------------- delete, then find holes
old_faces = len(bm.faces)
bmesh.ops.delete(bm, geom=[bm.faces[i] for i in region], context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
# small islands of skin left inside the mouth (faces the probe did not reach) go too
islands, seen_f = [], set()
for f in bm.faces:
    if f in seen_f or not all(v[pl] == 0 for v in f.verts):
        continue
    st, comp_f = [f], [f]
    seen_f.add(f)
    while st:
        x = st.pop()
        for e in x.edges:
            for g in e.link_faces:
                if g not in seen_f and all(v[pl] == 0 for v in g.verts):
                    seen_f.add(g); st.append(g); comp_f.append(g)
    if len(comp_f) < 60 and all(g.calc_center_median().y < HEAD_Y for g in comp_f):
        islands.extend(comp_f)
rep['islands_removed'] = len(islands)
bmesh.ops.delete(bm, geom=islands, context='FACES')
bm.verts.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.faces.ensure_lookup_table()
bm.verts.index_update(); bm.faces.index_update()


def boundary_loops(bm, ymax):
    """Hole loops by half-edge walking (robust at pinch vertices where two hole segments touch)."""
    def ok(e):
        return len(e.link_faces) == 1 and all(v.co.y < ymax and v[pl] == 0 for v in e.verts)

    def nxt(l):
        lp = l.link_loop_prev
        for _ in range(64):
            if len(lp.edge.link_faces) == 1:
                return lp
            lr = lp.link_loop_radial_next
            if lr is lp or lr.vert is not l.vert:
                return None
            lp = lr.link_loop_prev
        return None

    used, loops = set(), []
    for e in bm.edges:
        if not ok(e) or e.index in used:
            continue
        l0 = e.link_loops[0]
        loop, cur = [l0.link_loop_next.vert], l0
        for _ in range(5000):
            used.add(cur.edge.index)
            loop.append(cur.vert)
            cur = nxt(cur)
            if cur is None or cur is l0 or cur.edge.index in used:
                break
        if loop[-1] is loop[0]:
            loop.pop()
        loops.append(loop)
    counts = {}
    for l in loops:
        for v in l:
            counts[v] = counts.get(v, 0) + 1
    return loops, sum(1 for c in counts.values() if c > 1)


loops, pinch = boundary_loops(bm, HEAD_Y)
loops.sort(key=len, reverse=True)
rep['holes'] = [len(l) for l in loops]
rep['hole_info'] = [[len(l), np.round(np.mean([v.co[:] for v in l], 0), 3).tolist(),
                     round(float(np.ptp(np.array([v.co[:] for v in l]), 0).max()), 3)] for l in loops]
rep['pinched_boundary_verts'] = pinch
lip = loops[0]
eye_loop = None


def fill_fan(loop, inward=0.01):
    c = sum((v.co for v in loop), Vector()) / len(loop)
    nrm = Vector()
    for e in {e for v in loop for e in v.link_edges if len(e.link_faces) == 1}:
        nrm += e.link_faces[0].normal
    nrm = nrm.normalized() if nrm.length else Vector((0, 0, 1))
    cv = bm.verts.new(c - nrm * inward)
    cv[pl] = 0; cv[cl] = -1
    faces = []
    for i in range(len(loop)):
        a, b = loop[i], loop[(i + 1) % len(loop)]
        try:
            f = bm.faces.new((a, b, cv))
        except ValueError:
            continue
        faces.append(f)
    # winding: agree with the neighbouring skin across each boundary edge
    for f in faces:
        e = bm.edges.get((f.verts[0], f.verts[1]))
        other = [g for g in e.link_faces if g is not f]
        if other:
            g = other[0]
            gv = [v for v in g.verts]
            i = gv.index(f.verts[0])
            if gv[(i + 1) % len(gv)] == f.verts[1]:   # same direction -> inconsistent
                f.normal_flip()
    return cv, faces


small_filled = 0
for l in loops[1:]:
    ext = float(np.ptp(np.array([v.co[:] for v in l]), 0).max())
    if (l is eye_loop or len(l) <= 12) and ext < 0.15 and not os.environ.get('NOFILL'):
        cv, faces = fill_fan(l, 0.01 if l is eye_loop else 0.0)
        for f in faces:
            f.smooth = True
            src = f.verts[0] if f.verts[0] is not cv else f.verts[1]
            uvsrc = next(lp[uvl].uv.copy() for lp in src.link_loops if lp.face is not f)
            for lp in f.loops:
                if lp.vert is cv:
                    lp[uvl].uv = uvsrc
        small_filled += 1
rep['small_holes_filled'] = small_filled

# ---------------------------------------------------------------- 4. lip loop: corners and halves
bm.verts.ensure_lookup_table(); bm.verts.index_update(); bm.faces.index_update()
L = [v for v in lip]
Lp = np.array([v.co[:] for v in L])
CX = float((Lp[:, 0].max() + Lp[:, 0].min()) / 2)
side = Lp[:, 0] - CX
ca = int(np.argmax(np.where(side > 0.04, Lp[:, 1], -9)))
cb = int(np.argmax(np.where(side < -0.04, Lp[:, 1], -9)))
N = len(L)
L = L[ca:] + L[:ca]
Lp = np.array([v.co[:] for v in L])
cb = (cb - ca) % N
half1, half2 = list(range(0, cb + 1)), list(range(cb, N)) + [0]
if Lp[half1, 2].mean() < Lp[half2[:-1], 2].mean():
    L = [L[0]] + L[1:][::-1]
    Lp = np.array([v.co[:] for v in L])
    cb = N - cb
upper = np.zeros(N, bool); upper[1:cb] = True
lower = np.zeros(N, bool); lower[cb + 1:] = True
corner_a, corner_b = Lp[0], Lp[cb]
py, pz = float((corner_a[1] + corner_b[1]) / 2), float((corner_a[2] + corner_b[2]) / 2)
piv = Vector((0, py, pz))
rep['corners'] = [np.round(corner_a, 3).tolist(), np.round(corner_b, 3).tolist()]
rep['pivot'] = [0.0, round(py, 4), round(pz, 4)]
rep['pivot_mm9'] = [round(x, 4) for x in B8.head_local]


def phi(p):
    return math.degrees(math.atan2(p[2] - pz, -(p[1] - py)))


fwd = -(Lp[:, 1] - py)
phis = np.array([phi(p) for p in Lp])
fu = upper & (fwd > 0.6 * fwd[upper].max())
fl = lower & (fwd > 0.6 * fwd[lower].max())
phi_u, phi_l = float(np.median(phis[fu])), float(np.median(phis[fl]))
G = phi_u - phi_l
rep['gape_bind_deg_lip_angles'] = round(G, 2)

# ---------------------------------------------------------------- 6. jaw weights (on the original bind positions)
phb = math.radians((phi_u + phi_l) / 2)
n_b = Vector((0, math.sin(phb), math.cos(phb)))   # up-normal of the plane bisecting the gape


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


dl = bm.verts.layers.deform.active
bm.verts.ensure_lookup_table()
nv = len(bm.verts)
Pb = np.array([v.co[:] for v in bm.verts])
pieceb = np.array([v[pl] for v in bm.verts])
h = (Pb - np.array(piv[:])) @ np.array(n_b[:])
s_lower = smoothstep(SPLIT, -SPLIT, h)
f_back = 1 - smoothstep(-0.02, BACK_FADE, Pb[:, 1] - py)
w8 = np.array([v[dl].get(J8, 0.0) for v in bm.verts])
w7 = np.array([v[dl].get(J7, 0.0) for v in bm.verts])
share = w7 + w8
new8 = np.where(pieceb == 0, share * s_lower * f_back, w8)
# smooth the new jaw weight over the head skin (2 passes, share kept)
nbrs = [[e.other_vert(v).index for e in v.link_edges] for v in bm.verts]
headv = (pieceb == 0) & (share > 0) & (Pb[:, 1] < py + 0.6)
frac = np.where(share > 0, new8 / np.maximum(share, 1e-9), 0)
for _ in range(2):
    avg = np.array([frac[nb].mean() if nb else frac[i] for i, nb in enumerate(nbrs)])
    frac = np.where(headv, 0.5 * frac + 0.5 * avg, frac)
new8 = np.where(headv, share * frac, new8)
for v in bm.verts:
    if share[v.index] <= 0 or pieceb[v.index] != 0:
        continue
    v[dl][J8] = float(new8[v.index])
    v[dl][J7] = float(share[v.index] - new8[v.index])
    for k in [k for k, w in v[dl].items() if w < 1e-4]:
        del v[dl][k]
# teeth rigid, eye rigid on the head
vmap = {}
for v in bm.verts:
    vmap.setdefault(tuple(np.round(v.co[:], 6)), v)
low_set = set()
for k in teeth_up + teeth_low + eyes:
    for i in comps[k]:
        v = vmap[tuple(np.round(P0[i], 6))]
        for g in list(v[dl].keys()):
            del v[dl][g]
        v[dl][J8 if k in teeth_low else J7] = 1.0
        if k in teeth_low:
            low_set.add(v.index)

# ---------------------------------------------------------------- 6b. contact: how far the jaw can close
bm.verts.index_update(); bm.faces.index_update()
w8v = np.array([v[dl].get(J8, 0.0) for v in bm.verts])
tooth_of = {}
for k in teeth_up + teeth_low:
    for i in comps[k]:
        tooth_of[vmap[tuple(np.round(P0[i], 6))].index] = 2 if k in teeth_up else 3
skin_f = [f for f in bm.faces if all(v[pl] == 0 for v in f.verts) and f.calc_center_median().y < HEAD_Y]
fw = {f.index: float(np.mean([w8v[v.index] for v in f.verts])) for f in skin_f}
sets = {'up': [f for f in skin_f if fw[f.index] < 0.2], 'lo': [f for f in skin_f if fw[f.index] > 0.8],
        'ut': [f for f in bm.faces if tooth_of.get(f.verts[0].index) == 2],
        'lt': [f for f in bm.faces if tooth_of.get(f.verts[0].index) == 3]}


def contacts(theta):
    R = Matrix.Rotation(math.radians(-theta), 3, 'X')
    pos = [v.co.lerp(R @ (v.co - piv) + piv, float(w)) for v, w in zip(bm.verts, w8v)]
    tr = {k: BVHTree.FromPolygons(pos, [[v.index for v in f.verts] for f in fs]) for k, fs in sets.items()}
    return len(tr['lo'].overlap(tr['up'])), len(tr['lt'].overlap(tr['up'])), len(tr['ut'].overlap(tr['lo']))


rep['contact_sets'] = {k: len(v) for k, v in sets.items()}
series = {th: contacts(th) for th in range(0, 85, 1)}
base = series[0]
first = []
for j in range(3):
    hit = [th for th, c in sorted(series.items()) if c[j] > base[j]]
    first.append(hit[0] if hit else 85)
G = min(first) - 1.0
DELTA = (MAX_CLOSE + MARGIN_DEG) - G
rep['contact_first_deg'] = {'lips': first[0], 'lower_teeth_upper_skin': first[1], 'upper_teeth_lower_skin': first[2],
                            'baseline': list(base)}
rep['contact_series'] = {th: list(c) for th, c in series.items() if th % 5 == 0}
rep['gape_bind_deg'] = round(G, 2)
rep['prerotation_open_deg'] = round(DELTA, 2)

# ---------------------------------------------------------------- 7. pre-rotate the jaw (opening by DELTA)
Ro = Matrix.Rotation(math.radians(DELTA), 3, 'X')
for v in bm.verts:
    w = v[dl].get(J8, 0.0)
    if w > 0:
        v.co = v.co.lerp(Ro @ (v.co - piv) + piv, w)
Lp = np.array([v.co[:] for v in L])

# ---------------------------------------------------------------- 8. cavity
Th = Vector((CX, py + THROAT[0], pz + THROAT[1]))
o = Vector(Lp.mean(0))
a = (Th - o).normalized()
wl = np.array([v[dl].get(J8, 0.0) for v in L])
# u: corner A 0, upper half to corner B 0.5, lower half back to 1 (by arc length per half)
seg = np.linalg.norm(np.roll(Lp, -1, 0) - Lp, axis=1)
u = np.zeros(N + 1)
up_len, lo_len = seg[:cb].sum(), seg[cb:].sum()
for i in range(1, N + 1):
    u[i] = u[i - 1] + (seg[i - 1] / up_len * 0.5 if i - 1 < cb else seg[i - 1] / lo_len * 0.5)
u[cb] = 0.5; u[N] = 1.0
ulow_mid = 0.75
rings = [list(L)]
ring_t = []
mi = []
for i in range(N):
    p = Vector(Lp[i])
    c = o + a * ((p - o).dot(a))
    mi.append((c - p).normalized())
lip_roll = [L[i].co + mi[i] * LIP_ROLL[0] + a * LIP_ROLL[1] for i in range(N)]
gum = [L[i].co + mi[i] * GUM[0] + a * GUM[1] for i in range(N)]
# relax the two lip rings along the ring (the inward offsets bunch up where the lips turn at the corners)
for ring in (lip_roll, gum):
    for _ in range(3):
        ring[:] = [ring[i] * 0.5 + (ring[i - 1] + ring[(i + 1) % N]) * 0.25 for i in range(N)]
pos_rings = [lip_roll, gum]
for t in RING_T:
    rp = []
    for i in range(N):
        g = gum[i]
        q = g + (Th - g) * t - mi[i] * (BULGE * math.sin(math.pi * t) * (1 - 0.3 * t))
        if lower[i] or i == 0 or i == cb:
            du = min(abs(u[i] - ulow_mid), 1)
            q = q + mi[i] * (TONGUE_H * math.exp(-(du / 0.1) ** 2) * math.sin(math.pi * min(t / 0.9, 1.0)) ** 0.7)
        rp.append(q)
    pos_rings.append(rp)
depth_t = [0.0, 0.0] + list(RING_T)


def jaw_w(i, t):
    return float(wl[i] * (1 - smoothstep(0.45, 0.95, t)))


# ring resolution: the lip roll and gum keep every lip vertex (teeth sit there); deeper rings shrink toward the
# throat, so they keep every s-th vertex (corners always) to stay about as long along the ring as between rings
chain = [[L[i].co for i in range(N)]] + pos_rings
dists = [float(np.mean([(chain[k + 1][i] - chain[k][i]).length for i in range(N)])) for k in range(len(chain) - 1)]
dists.append(float(np.mean([(Th - chain[-1][i]).length for i in range(N)])))
keep = [list(range(N))]
for k, rp in enumerate(pos_rings, start=1):
    if k <= 2:
        keep.append(list(range(N)))
        continue
    per = sum((rp[(i + 1) % N] - rp[i]).length for i in range(N))
    spacing = max(dists[k - 1], dists[k])
    step = max(1, int(round(N / max(8, per / (1.3 * spacing)))))
    keep.append(sorted({i for i in range(N) if i % step == 0} | {0, cb}))
mouth_verts = []
mparam = {v: (i, 0) for i, v in enumerate(L)}      # (lip loop index, ring) for the cavity paint parameters
for k, rp in enumerate(pos_rings, start=1):
    ring = []
    for i in keep[k]:
        v = bm.verts.new(rp[i])
        v[pl] = 0; v[cl] = -1
        w = jaw_w(i, depth_t[k - 1])
        if w > 1e-4:
            v[dl][J8] = w
        v[dl][J7] = 1 - w
        ring.append(v); mouth_verts.append(v)
        mparam[v] = (i, k)
    rings.append(ring)
thv = bm.verts.new(Th)
thv[pl] = 0; thv[cl] = -1; thv[dl][J7] = 1.0
mouth_verts.append(thv)
# v proportional to the mean distance between rings (lip -> throat), so the cavity's texels are spread evenly
cum = np.concatenate([[0], np.cumsum(dists)]) / sum(dists)
vk = list(cum[:-1])
rep['cavity_depth_m'] = round(sum(dists), 3)
rep['ring_sizes'] = [len(r) for r in rings]
# rect width from the gum ring's perimeter, so u and v have the same texel density
perim = sum((pos_rings[1][(i + 1) % N] - pos_rings[1][i]).length for i in range(N))
UV_RECT = (UV_RECT[0], UV_RECT[1], min(0.95, UV_RECT[0] + (UV_RECT[3] - UV_RECT[1]) * perim / sum(dists)), UV_RECT[3])
rep['cavity_perimeter_m'] = round(perim, 3)
U0, V0, U1, V1 = UV_RECT


def uvmap(uu, vv):
    return (U0 + uu * (U1 - U0), V1 - vv * (V1 - V0))


def stitch(ra, ia, va, rb, ib, vb):
    """Triangles between two closed rings ordered by u (index lists ia/ib into the lip loop), same winding as the
    lip -> roll quads: (a_i, a_next, b_next) / (a_i, b_next, b_i)."""
    ua = [u[i] for i in ia] + [1.0]
    ub = [u[i] for i in ib] + [1.0]
    x, y = 0, 0
    out = []
    while x < len(ia) or y < len(ib):
        a0, b0 = ra[x % len(ia)], rb[y % len(ib)]
        if y >= len(ib) or (x < len(ia) and ua[x + 1] <= ub[y + 1]):
            a1 = ra[(x + 1) % len(ia)]
            out.append(((a0, a1, b0), ((ua[x], va), (ua[x + 1], va), (ub[y], vb))))
            x += 1
        else:
            b1 = rb[(y + 1) % len(ib)]
            out.append(((a0, b1, b0), ((ua[x], va), (ub[y + 1], vb), (ub[y], vb))))
            y += 1
    return out


new_faces = []
for k in range(len(rings) - 1):
    for tri, uvs in stitch(rings[k], keep[k], vk[k], rings[k + 1], keep[k + 1], vk[k + 1]):
        f = bm.faces.new(tri)
        for lp, (uu, vv) in zip(f.loops, uvs):
            lp[uvl].uv = uvmap(uu, vv)
        new_faces.append(f)
last, il = rings[-1], keep[-1]
ul = [u[i] for i in il] + [1.0]
for x in range(len(il)):
    f = bm.faces.new((last[x], last[(x + 1) % len(il)], thv))
    for lp, (uu, vv) in zip(f.loops, ((ul[x], vk[-1]), (ul[x + 1], vk[-1]), ((ul[x] + ul[x + 1]) / 2, 1.0))):
        lp[uvl].uv = uvmap(uu, vv)
    new_faces.append(f)
bm.normal_update()
# winding: cavity normals point into the mouth (toward the axis)
inward = 0
for f in new_faces:
    c = f.calc_center_median()
    axp = o + a * ((c - o).dot(a))
    inward += 1 if f.normal.dot(axp - c) > 0 else -1
flipped = inward < 0
if flipped:
    for f in new_faces:
        f.normal_flip()
for f in new_faces:
    f.smooth = True
rep['cavity'] = {'loop_verts': N, 'rings': len(rings), 'triangles': len(new_faces), 'flipped': flipped,
                 'throat': [round(x, 3) for x in Th], 'uv_rect': UV_RECT, 'u_corner_b': 0.5}
# consistency across the lip: each lip edge should run opposite in the skin face and the cavity face
bad = 0
for i in range(N):
    e = bm.edges.get((L[i], L[(i + 1) % N]))
    fs = list(e.link_faces)
    if len(fs) != 2:
        bad += 1; continue
    dirs_ = []
    for f in fs:
        vs = list(f.verts)
        k = vs.index(L[i])
        dirs_.append(vs[(k + 1) % len(vs)] == L[(i + 1) % N])
    bad += dirs_[0] == dirs_[1]
rep['cavity']['lip_winding_mismatch'] = bad

# ---------------------------------------------------------------- 9. teeth reseated
bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table(); bm.verts.index_update(); bm.faces.index_update()
gum_faces = [f for f in new_faces if any(v in set(rings[2]) or v in set(rings[1]) for v in f.verts)]
gbvh = BVHTree.FromPolygons([v.co for v in bm.verts], [[v.index for v in f.verts] for f in gum_faces])
moves = {}
for k in teeth_up + teeth_low:
    vs = [vmap[tuple(np.round(P0[i], 6))] for i in comps[k]]
    pts = np.array([v.co[:] for v in vs])
    ax0, tmin, tmax, _ = tooth_axis[k]
    ax = Vector(ax0)
    if k in teeth_low:
        ax = Ro @ ax
    cen = Vector(pts.mean(0))
    t = (pts - np.array(cen[:])) @ np.array(ax[:])
    length = float(t.max() - t.min())
    base = cen + ax * float(t.min())
    hit = gbvh.find_nearest(base)
    if hit[0] is None:
        continue
    q, nq = hit[0], hit[1]
    if nq.dot(ax) < 0:
        nq = -nq                     # the gum normal on the tooth's side
    den = ax.dot(nq)
    if abs(den) < 0.3:
        continue
    s = (-SINK * length - (base - q).dot(nq)) / den
    s = max(-0.04, min(0.04, s))
    for v in vs:
        v.co += ax * s
    moves[k] = round(s, 4)
rep['teeth_moves_m'] = {'max_abs': max(abs(x) for x in moves.values()) if moves else 0,
                        'mean_abs': round(float(np.mean([abs(x) for x in moves.values()])), 4) if moves else 0,
                        'moved': len(moves)}

# ---------------------------------------------------------------- 10. back and tail spines rooted
# rig_body.py made each spine rigid with one body vertex; where the skin under a spine's base spans two bones the
# spine left the back by 5 cm in Hit (detached_parts_audit.py). Every spine vertex now takes the weights of the body
# vertex nearest to it, so the spine bends with the skin it grows from.
bm.verts.ensure_lookup_table(); bm.verts.index_update()
from mathutils.kdtree import KDTree
skin_v = [v for v in bm.verts if v[pl] == 0 and v.co.y > HEAD_Y]
kd = KDTree(len(skin_v))
for j, v in enumerate(skin_v):
    kd.insert(v.co, j)
kd.balance()
spine_n = 0
for k, ids in enumerate(comps):
    c = P0[ids].mean(0)
    if c[1] <= -1.3 and c[2] <= 0.9:
        continue                      # teeth and eyes (head)
    for i in ids:
        v = vmap.get(tuple(np.round(P0[i], 6)))
        if v is None:
            continue
        src = skin_v[kd.find(v.co)[1]]
        for g in list(v[dl].keys()):
            del v[dl][g]
        for g, w in src[dl].items():
            v[dl][g] = w
    spine_n += 1
rep['spines_reweighted'] = spine_n

# ---------------------------------------------------------------- labels, write mesh, move Bone08
bm.verts.ensure_lookup_table(); bm.verts.index_update()
lab = np.zeros(len(bm.verts), int)
for v in mouth_verts:
    lab[v.index] = 1
for k in teeth_up:
    for i in comps[k]:
        lab[vmap[tuple(np.round(P0[i], 6))].index] = 2
for k in teeth_low:
    for i in comps[k]:
        lab[vmap[tuple(np.round(P0[i], 6))].index] = 3
for i in eye_ids:
    lab[vmap[tuple(np.round(P0[i], 6))].index] = 4
mparam_idx = {v.index: ik for v, ik in mparam.items()}
throat_idx = thv.index
bm.to_mesh(me)
bm.free()
me.update()
if 'mlab' in me.attributes:
    me.attributes.remove(me.attributes['mlab'])
att = me.attributes.new('mlab', 'INT', 'POINT')
att.data.foreach_set('value', lab)
# cavity paint parameters, readable through any later UV layout (dump_uv3d.py DUMP_GROUPS): u around the lip loop
# as cos/sin (it wraps at corner A), v lip -> throat; compose_sea.py paints the lining from them per texel
for name in ('MouthCos', 'MouthSin', 'MouthV'):
    if name in ob.vertex_groups:
        ob.vertex_groups.remove(ob.vertex_groups[name])
gcos, gsin, gv = (ob.vertex_groups.new(name=n) for n in ('MouthCos', 'MouthSin', 'MouthV'))
for vi, (i, k) in mparam_idx.items():
    ang = 2 * math.pi * u[i]
    gcos.add([vi], 0.5 + 0.5 * math.cos(ang), 'REPLACE')
    gsin.add([vi], 0.5 + 0.5 * math.sin(ang), 'REPLACE')
    gv.add([vi], float(vk[k]), 'REPLACE')
for g, w in ((gcos, 0.5), (gsin, 0.5), (gv, 1.0)):
    g.add([throat_idx], w, 'REPLACE')
for name, k in (('Mouth', 1), ('Eye', 4)):
    if name in ob.vertex_groups:
        ob.vertex_groups.remove(ob.vertex_groups[name])
    g = ob.vertex_groups.new(name=name)
    g.add([int(i) for i in np.nonzero(lab == k)[0]], 1.0, 'REPLACE')
bpy.context.view_layer.objects.active = rig
for o_ in bpy.data.objects:
    o_.select_set(o_ == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Bone08']
eb.use_connect = False
d = eb.tail - eb.head
eb.head = Vector((eb.head.x, py, pz))
eb.tail = eb.head + d
bpy.ops.object.mode_set(mode='OBJECT')
rep['faces'] = {'before': old_faces, 'after': len(me.polygons)}
rep['triangles_after'] = sum(len(p.vertices) - 2 for p in me.polygons)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('MOUTH ' + json.dumps({k: rep[k] for k in ('interior_faces', 'holes', 'gape_bind_deg', 'prerotation_open_deg',
                                                  'pivot', 'teeth', 'teeth_moves_m', 'triangles_after')}))
