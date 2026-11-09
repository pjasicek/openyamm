"""Symmetrize the Sea Monster's head: the right half (x < CX) in front of YCUT is replaced by the mirror image of the
left half, teeth and eyeball included (2026-10-30 review: shards at the right eye and threads across the right mouth
corner). Runs on the UV'd body before mouth_rebuild.py; UVs and weights are copied from the mirrored faces, so the
retexture stays valid (the right half of the head shows the left half's texels).

Args: <uv blend> <out blend> <report json>

Why: Meshy's right side of the head (the far side in the three-quarter master) has a fan of long thread triangles from
the eye socket down to the lower jaw, a crumpled socket without an eyeball, and three upper teeth instead of ten.

1. CX = middle of the head skin's lateral extent; the main body is cut by the planes y = YCUT (whole cross-section)
   and x = CX (head region only).
2. Head region = faces of the main body component in front of YCUT reachable from the snout.
3. Right faces deleted, left faces mirrored (reversed winding, copied UVs and weights; side bones swapped).
4. Seam at y = YCUT on the right: the mirrored patch is morphed onto the original right cross-section (displacement
   faded over BLEND metres), both seam polylines are merged (vertices within EPS welded, the rest split into the other
   side's edges), affected faces triangulated.
5. Pieces (teeth, eyeball) in the head region: right ones deleted, left ones mirrored; pieces within MID of the
   midplane stay as they are.
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector

argv = sys.argv[sys.argv.index('--') + 1:]
IN, OUT, REP = argv[:3]
YCUT = -1.38
BLEND = 0.15
EPS = 0.015
SNAP = 0.012
MID = 0.035
SNOUT = Vector((0.03, -1.85, 0.7))
PAIRS = [('Bone10', 'Bone21'), ('Bone11', 'Bone22'), ('Bone12', 'Bone23'), ('Bone13', 'Bone24'),
         ('Bone15', 'Bone26'), ('Bone16', 'Bone27'), ('Bone17', 'Bone28'), ('Bone18', 'Bone29'),
         ('Bone19', 'Bone30'), ('Bone35', 'Bone37')]

bpy.ops.wm.open_mainfile(filepath=IN)
ob = bpy.data.objects['Body']
me = ob.data
gi = {g.name: g.index for g in ob.vertex_groups}
for a, b in PAIRS:
    for nm in (a, b):
        if nm not in gi:
            gi[nm] = ob.vertex_groups.new(name=nm).index
MIRROR = {}
for a, b in PAIRS:
    MIRROR[gi[a]], MIRROR[gi[b]] = gi[b], gi[a]
bm = bmesh.new()
bm.from_mesh(me)
pl = bm.verts.layers.int['piece']
dl = bm.verts.layers.deform.active
uvl = bm.loops.layers.uv.active
rep = {}


def components(faces_ok):
    comp, out = {}, []
    for f in bm.faces:
        if f in comp or not faces_ok(f):
            continue
        st, ids = [f], [f]
        comp[f] = len(out)
        while st:
            x = st.pop()
            for e in x.edges:
                for g in e.link_faces:
                    if g not in comp and faces_ok(g):
                        comp[g] = len(out); st.append(g); ids.append(g)
        out.append(ids)
    return out


def body(f):
    return all(v[pl] == 0 for v in f.verts)


comps0 = components(body)
main = set(max(comps0, key=len))
# loose body pieces in the head (Meshy's thread webs across both mouth corners, joined to the skin only by vertices)
def centre(c):
    return sum((g.calc_center_median() for g in c), Vector()) / len(c)


loose = [f for c in comps0 if c is not None and not (set(c) & main) and len(c) < 1000
         and centre(c).y < YCUT and abs(centre(c).x) < 0.4 for f in c]
rep['loose_head_faces_removed'] = len(loose)
bmesh.ops.delete(bm, geom=loose, context='FACES')
skin = np.array([v.co[:] for f in main for v in f.verts if v.co.y < -1.45 and v.co.z > 0.2])
CX = float((np.percentile(skin[:, 0], 99.5) + np.percentile(skin[:, 0], 0.5)) / 2)
rep['cx'] = round(CX, 4)

# 1. cut the cross-section at YCUT (main body faces only, near the head)
# vertices within SNAP of a cutting plane go onto it first, so the cuts leave no sliver triangles
for v in {v for f in main for v in f.verts}:
    if abs(v.co.y - YCUT) < SNAP and abs(v.co.x - CX) < 0.45:
        v.co.y = YCUT
cross = [f for f in main if min(v.co.y for v in f.verts) < YCUT < max(v.co.y for v in f.verts)
         and all(abs(v.co.x - CX) < 0.45 for v in f.verts)]
geom = list({e for f in cross for e in f.edges}) + cross + list({v for f in cross for v in f.verts})
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, YCUT, 0), plane_no=(0, 1, 0), dist=1e-5)


def head_region():
    main_ = set(max(components(body), key=len))
    seed = min((f for f in main_ if f.calc_center_median().y < YCUT),
               key=lambda f: (f.calc_center_median() - SNOUT).length)
    reg, st = {seed}, [seed]
    while st:
        f = st.pop()
        for e in f.edges:
            for g in e.link_faces:
                if g not in reg and g in main_ and g.calc_center_median().y < YCUT:
                    reg.add(g); st.append(g)
    return reg


reg = head_region()
xs = [v.co.x for f in reg for v in f.verts]
rep['region_faces'], rep['region_x'] = len(reg), [round(min(xs), 3), round(max(xs), 3)]
for v in {v for f in reg for v in f.verts}:
    if abs(v.co.x - CX) < SNAP:
        v.co.x = CX
geom = list({e for f in reg for e in f.edges}) + list(reg) + list({v for f in reg for v in f.verts})
bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(CX, 0, 0), plane_no=(1, 0, 0), dist=1e-5)
reg = head_region()
right = [f for f in reg if f.calc_center_median().x < CX]
left = [f for f in reg if f.calc_center_median().x >= CX]
rep['right_faces_removed'], rep['left_faces_mirrored'] = len(right), len(left)


def on_mid(v):
    return abs(v.co.x - CX) < 1e-5


def mirror_vert(v, cache):
    if on_mid(v):
        return v
    if v in cache:
        return cache[v]
    w = bm.verts.new((2 * CX - v.co.x, v.co.y, v.co.z), v)
    dv = dict(v[dl].items())
    w[dl].clear()
    for g, wt in dv.items():
        w[dl][MIRROR.get(g, g)] = wt
    cache[v] = w
    return w


def mirror_faces(faces, cache):
    data = [(list(f.verts), [lp[uvl].uv.copy() for lp in f.loops], f.smooth, f.material_index) for f in faces]
    new = []
    for vs, uvs, smooth, mat in data:
        if all(on_mid(v) for v in vs):
            continue                  # lies in the mirror plane
        nvs = [mirror_vert(v, cache) for v in reversed(vs)]
        if bm.faces.get(nvs) is not None or len(set(nvs)) < 3:
            continue
        g = bm.faces.new(nvs)
        for lp, uv in zip(g.loops, reversed(uvs)):
            lp[uvl].uv = uv
        g.smooth, g.material_index = smooth, mat
        new.append(g)
    return new


# seam polyline on the original right side, before deleting: boundary between right region faces and faces behind
right_set = set(right)
bmesh.ops.delete(bm, geom=right, context='FACES_ONLY')
bmesh.ops.delete(bm, geom=[e for e in bm.edges if not e.link_faces], context='EDGES')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
cache = {}
patch = mirror_faces(left, cache)
patch_set = set(patch)
patch_verts = set(cache.values())


def seam_chain(pred_face):
    """Boundary edges on the plane y = YCUT, x < CX, whose single face satisfies pred_face; ordered top -> bottom."""
    es = [e for e in bm.edges if len(e.link_faces) == 1 and pred_face(e.link_faces[0]) and
          all(abs(v.co.y - YCUT) < 1e-4 and v.co.x < CX + 1e-5 for v in e.verts)]
    nb = {}
    for e in es:
        a, b = e.verts
        nb.setdefault(a, []).append(b); nb.setdefault(b, []).append(a)
    ends = [v for v, l in nb.items() if len(l) == 1]
    if len(ends) != 2:
        raise SystemExit(f'seam chain: {len(ends)} ends, {len(es)} edges')
    start = max(ends, key=lambda v: v.co.z)
    chain, prev = [start], None
    while True:
        nx = [w for w in nb[chain[-1]] if w is not prev]
        if not nx:
            break
        prev = chain[-1]
        chain.append(nx[0])
    return chain


Pr = seam_chain(lambda f: f not in patch_set)
Pm = seam_chain(lambda f: f in patch_set)
rep['seam'] = {'right': len(Pr), 'mirrored': len(Pm), 'ends_shared': Pr[0] is Pm[0] and Pr[-1] is Pm[-1]}


def project(p, chain):
    """Closest point on a polyline: (point, arc parameter, segment index, fraction)."""
    best = None
    s0 = 0.0
    for i in range(len(chain) - 1):
        a, b = chain[i].co, chain[i + 1].co
        ab = b - a
        L = ab.length
        t = max(0.0, min(1.0, (p - a).dot(ab) / max(L * L, 1e-12)))
        q = a + ab * t
        d = (p - q).length
        if best is None or d < best[0]:
            best = (d, q, s0 + t * L, i, t)
        s0 += L
    return best[1:]


# 4a. morph the mirrored patch onto the right cross-section
disp = {}
for m in Pm[1:-1]:
    q = project(m.co, Pr)[0]
    disp[m] = q - m.co
mvs = list(disp)
rep['seam']['max_morph'] = round(max((d.length for d in disp.values()), default=0), 4)
for v in patch_verts:
    if v in disp:
        v.co += disp[v]
        continue
    w = 1 - min(1.0, max(0.0, (YCUT - v.co.y) / BLEND))
    if w <= 0 or not mvs:
        continue
    w = w * w * (3 - 2 * w)
    near = min(mvs, key=lambda m: (Vector((m.co.x - v.co.x, 0, m.co.z - v.co.z))).length)
    v.co += disp[near] * w


# 4b. merge the two seam polylines
def arc(chain):
    s = [0.0]
    for i in range(len(chain) - 1):
        s.append(s[-1] + (chain[i + 1].co - chain[i].co).length)
    return s


weld = {}
sr = arc(Pr)
splits = 0
for m in Pm[1:-1]:
    q, s, i, t = project(m.co, Pr)
    j = min(range(len(Pr)), key=lambda k: abs(sr[k] - s))
    if abs(sr[j] - s) < EPS:
        weld[m] = Pr[j]
weld_targets = set(weld.values())
# Pr vertices without a partner: split the mirrored edge under them
for r in Pr[1:-1]:
    if r in weld_targets:
        continue
    q, s, i, t = project(r.co, Pm)
    a, b = Pm[i], Pm[i + 1]
    e = bm.edges.get((a, b))
    if e is None or t <= 1e-3 or t >= 1 - 1e-3:
        continue
    ne, nv = bmesh.utils.edge_split(e, a, t)
    weld[nv] = r
    Pm.insert(i + 1, nv)
    splits += 1
# remaining mirrored vertices not welded: split the right edge under them
sr = arc(Pr)
for m in list(Pm[1:-1]):
    if m in weld:
        continue
    q, s, i, t = project(m.co, Pr)
    a, b = Pr[i], Pr[i + 1]
    e = bm.edges.get((a, b))
    if e is None:
        continue
    ne, nv = bmesh.utils.edge_split(e, a, t)
    nv.co = m.co.copy()
    weld[m] = nv
    Pr.insert(i + 1, nv)
    splits += 1
bmesh.ops.weld_verts(bm, targetmap=weld)
rep['seam']['welded'], rep['seam']['splits'] = len(weld), splits
ngons = [f for f in bm.faces if len(f.verts) > 3]
bmesh.ops.triangulate(bm, faces=ngons)
rep['seam']['triangulated'] = len(ngons)

# 5. pieces
pieces = components(lambda f: all(v[pl] == 2 for v in f.verts))
mir, dele = 0, 0
for comp in pieces:
    c = sum((f.calc_center_median() for f in comp), Vector()) / len(comp)
    if c.y > YCUT or c.z > 0.9:
        continue
    if c.x < CX - MID:
        bmesh.ops.delete(bm, geom=comp, context='FACES')
        dele += 1
    elif c.x > CX + MID:
        mirror_faces(comp, {})
        mir += 1
rep['pieces'] = {'deleted_right': dele, 'mirrored_left': mir}
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_edges], context='VERTS')
bmesh.ops.dissolve_degenerate(bm, dist=1e-4, edges=bm.edges[:])
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])


def aspect(f):
    vs = [v.co for v in f.verts]
    L = max((vs[i] - vs[i - 1]).length for i in range(3))
    return L * L / max(2 * f.calc_area(), 1e-12)


def on_seam(v):
    return abs(v.co.x - CX) < 1e-4 or abs(v.co.y - YCUT) < 1e-4


collapsed = 0
for _ in range(4):
    bad = [f for f in bm.faces if len(f.verts) == 3 and all(v[pl] == 0 for v in f.verts) and
           any(on_seam(v) for v in f.verts) and f.calc_center_median().y < YCUT + 0.1 and aspect(f) > 12]
    edges = list({min(f.edges, key=lambda e: e.calc_length()) for f in bad})
    if not edges:
        break
    bmesh.ops.collapse(bm, edges=edges, uvs=True)
    collapsed += len(edges)
holes = [e for e in bm.edges if e.is_boundary and all(v[pl] == 0 and v.co.y < YCUT + 0.05 for v in e.verts)]
filled = bmesh.ops.holes_fill(bm, edges=holes, sides=12)['faces']
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
for f in filled:
    f.smooth = True
rep['cleanup'] = {'seam_slivers_collapsed': collapsed, 'holes_filled': len(filled)}
bm.normal_update()
bm.to_mesh(me)
bm.free()
me.update()
# check: boundary edges and non-manifold edges in the head
me.calc_loop_triangles()
from collections import Counter
cnt = Counter()
for p in me.polygons:
    vs = p.vertices
    for i in range(len(vs)):
        a, b = vs[i], vs[(i + 1) % len(vs)]
        cnt[(min(a, b), max(a, b))] += 1
head = lambda e: me.vertices[e[0]].co.y < YCUT + 0.05
import numpy as np
rep['check_components'] = None
rep['check'] = {'boundary_edges_head': sum(1 for e, c in cnt.items() if c == 1 and head(e)),
                'nonmanifold_edges_head': sum(1 for e, c in cnt.items() if c > 2 and head(e)),
                'triangles': len(me.loop_triangles)}
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(rep, open(REP, 'w'), indent=1)
print('SYM ' + json.dumps(rep))
