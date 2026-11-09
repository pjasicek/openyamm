"""Fit the Meshy Smart Topology mouse to the MM9 MOUSE.abc bind pose and clean it.

Args: <mm9 source blend> <meshy glb> <out blend> <report json>

1. Largest component only: Meshy's whisker strands (16 small pieces) are dropped (slivers; MM9 has none).
2. Similarity: uniform scale so snout tip -> tail base matches MM9 (snout tip -> Bone01 pivot), centred in x, paws on
   the floor (z = 0), snout tip on MM9's.
3. Symmetry: MM9's body is mirror-symmetric (the tail chain is not). The Meshy body is mirrored from its better
   half (the creature's right, -X: the side the three-quarter master shows) about x = 0 (bisect + mirror + weld).
4. Tail: Meshy's tail is cut behind the rump and replaced by our own tube that starts from the cut loop (same vertex
   count, so it is one manifold surface) and follows a smooth curve through the MM9 tail joints (Bone01, Bone02,
   Bone03, MM9 tail tip) lying on the floor, tapering to a fine tip.
5. Eyes: Meshy modelled only a shallow pit. Two black bead spheres (piece 1, radius 0.072 H; H = paw-to-back height)
   are seated in the pits, 62 % of the radius below the surface.
Attributes: 'piece' (0 body, 1 eye), 'part' (0 body, 1 tail tube, 2 eye), 'tail_t' (0..1 along the tail, -1 off it).
"""
import bpy, bmesh, sys, json, math
import numpy as np
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

argv = sys.argv[sys.argv.index('--') + 1:]
SRC, MESHY, OUT, REP = argv
CUT_Y = 0.045         # Meshy units: on the rump, where the Meshy tail is still centred (it curls to -x behind)
TAIL_BASE_Y = 0.08    # Meshy units: where the tail leaves the rump (mapped onto MM9's Bone01 pivot)
TAIL_R = 0.0024       # model units: tail radius past the rump
TAIL_TIP_R = 0.0007   # model units (m)
EYE_BACK, EYE_UP, EYE_R = 0.347, 0.457, 0.072
EYE_Y, EYE_Z = -0.1022, 0.0232   # model units, the Meshy eye pit
EYE_SINK = 0.62   # share of the radius below the head surface
report = {}

bpy.ops.wm.open_mainfile(filepath=SRC)
sc = bpy.context.scene
arm = bpy.data.objects['MM9_Rig']
mm9 = next(o for o in bpy.data.objects if o.type == 'MESH')
A = np.array([tuple(mm9.matrix_world @ v.co) for v in mm9.data.vertices])
J = {b.name: Vector(b.head_local) for b in arm.data.bones}
mm9_snout = A[:, 1].min()
mm9_tip = Vector(A[np.argmax(A[:, 1])])
report['mm9'] = {'snout_y': float(mm9_snout), 'tail_tip': list(mm9_tip), 'height': float(A[:, 2].max())}

before = set(bpy.data.objects)
bpy.ops.import_scene.gltf(filepath=MESHY)
new = [o for o in bpy.data.objects if o not in before]
src = next(o for o in new if o.type == 'MESH')
bm = bmesh.new()
bm.from_mesh(src.data)
bm.transform(src.matrix_world)
for o in new:
    bpy.data.objects.remove(o)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)


def components(bm):
    bm.verts.ensure_lookup_table()
    seen = set(); comps = []
    for v in bm.verts:
        if v.index in seen:
            continue
        st = [v]; seen.add(v.index); c = []
        while st:
            x = st.pop(); c.append(x)
            for e in x.link_edges:
                y = e.other_vert(x)
                if y.index not in seen:
                    seen.add(y.index); st.append(y)
        comps.append(c)
    comps.sort(key=len, reverse=True)
    return comps


comps = components(bm)
report['meshy_components'] = [len(c) for c in comps]
bmesh.ops.delete(bm, geom=[v for c in comps[1:] for v in c], context='VERTS')
B = np.array([tuple(v.co) for v in bm.verts])
snout_y = B[:, 1].min()
zmin = B[:, 2].min()
# body centre in x: mean of the per-slice x mid-points over the trunk
trunk = B[(B[:, 1] > -0.3) & (B[:, 1] < 0.0)]
cx = float(np.mean([(trunk[(trunk[:, 1] >= y) & (trunk[:, 1] < y + 0.02), 0].min()
                     + trunk[(trunk[:, 1] >= y) & (trunk[:, 1] < y + 0.02), 0].max()) / 2
                    for y in np.arange(-0.3, 0.0, 0.02)]))
s = (J['Bone01'].y - mm9_snout) / (TAIL_BASE_Y - snout_y)
report['scale'] = s
report['centre_x_meshy'] = cx
for v in bm.verts:
    v.co = Vector(((v.co.x - cx) * s, mm9_snout + (v.co.y - snout_y) * s, (v.co.z - zmin) * s))
cut_y = mm9_snout + (CUT_Y - snout_y) * s

# ---- tail cut: everything behind cut_y goes (the rump ends before it; the hind feet are well in front)
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                       plane_co=(0, cut_y, 0), plane_no=(0, 1, 0), clear_outer=True)
# ---- symmetry: keep the creature's right (-X) and mirror it
bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], dist=1e-7,
                       plane_co=(0, 0, 0), plane_no=(1, 0, 0), clear_outer=True)
for v in bm.verts:
    if abs(v.co.x) < 1e-6:
        v.co.x = 0.0
half = bm.verts[:] + bm.edges[:] + bm.faces[:]
mir = bmesh.ops.mirror(bm, geom=half, matrix=Matrix(), merge_dist=1e-6, axis='X')
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
comps = components(bm)
report['after_mirror_components'] = [len(c) for c in comps]
bmesh.ops.delete(bm, geom=[v for c in comps[1:] for v in c], context='VERTS')

# ---- the cut loop at the tail base
bm.edges.ensure_lookup_table()
bnd = [e for e in bm.edges if e.is_boundary]
report['boundary_edges_total'] = len(bnd)
bnd = [e for e in bnd if all(abs(v.co.y - cut_y) < 1e-5 for v in e.verts)]
loop_v = {v for e in bnd for v in e.verts}
adj = {v: [e.other_vert(v) for e in bnd if v in e.verts] for v in loop_v}
start = min(loop_v, key=lambda v: v.co.z)
order = [start]
seen_v = {start}
for _ in range(len(loop_v)):
    nxt = [n for n in adj[order[-1]] if n not in seen_v]
    if not nxt:
        break
    order.append(nxt[0]); seen_v.add(nxt[0])
report['tail_loop'] = {'boundary_verts': len(loop_v), 'ordered': len(order),
                       'y_span': [min(v.co.y for v in order), max(v.co.y for v in order)]}
assert len(order) == len(loop_v), 'tail cut must leave one simple loop'
L = np.array([tuple(v.co) for v in order])
c0 = L.mean(0)
r0 = float(np.linalg.norm((L - c0)[:, [0, 2]], axis=1).mean())
# angular order around +Y, starting at the bottom, counter-clockwise seen from behind
ang = np.arctan2(L[:, 2] - c0[2], L[:, 0] - c0[0])
if np.sum(np.diff(np.unwrap(ang))) < 0:
    order = order[::-1]
    L = L[::-1]
    ang = ang[::-1]
N = len(order)
report['tail_loop'].update({'centre': c0.tolist(), 'radius': r0, 'N': N})

# ---- tail curve: cut centre -> MM9 Bone02 -> Bone03 -> MM9 tip (Catmull-Rom, lying on the floor)
ctrl = [Vector(c0), Vector((0.0, c0[1] + 0.011, c0[2] * 0.62)), Vector((0.0, c0[1] + 0.024, TAIL_R + 0.0008)),
        J['Bone02'], J['Bone03'], mm9_tip]
ctrl = [Vector(p) for p in ctrl]


def catmull(pts, n):
    P = [pts[0] * 2 - pts[1]] + pts + [pts[-1] * 2 - pts[-2]]
    out = []
    for i in range(1, len(P) - 2):
        for k in range(n):
            t = k / n
            p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
            out.append(0.5 * (2 * p1 + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    out.append(P[-2])
    return out


dense = catmull(ctrl, 60)
seg = [0.0] + [float((dense[i + 1] - dense[i]).length) for i in range(len(dense) - 1)]
cum = np.cumsum(seg)
total = float(cum[-1])
STEP = 0.0028
n_rings = max(8, int(total / STEP))
report['tail_length'] = total


def at(d):
    i = min(int(np.searchsorted(cum, d)), len(dense) - 1)
    i = max(i, 1)
    a = (d - cum[i - 1]) / max(cum[i] - cum[i - 1], 1e-9)
    p = dense[i - 1].lerp(dense[i], min(max(a, 0), 1))
    tg = (dense[i] - dense[i - 1]).normalized()
    return p, tg


rings = [order]
prev_ring = order
up = Vector((0, 0, 1))
for k in range(1, n_rings + 1):
    t = k / n_rings
    p, tg = at(t * total)
    r = TAIL_R + (TAIL_TIP_R - TAIL_R) * (t ** 0.9) + (r0 - TAIL_R) * math.exp(-t / 0.05)
    # lie on the floor: the centre never lower than the radius (plus 0.3 mm)
    p = Vector((p.x, p.y, max(p.z, r + 0.0003) if t > 0.15 else p.z))
    side = tg.cross(up).normalized()
    nup = side.cross(tg).normalized()
    # the first rings morph from the cut loop's own shape (around its centre) to a circle
    blend = min(1.0, t / 0.12)
    ring = []
    for j in range(N):
        a = ang[j]
        circ = p + (side * math.cos(a) + nup * math.sin(a)) * r
        own = Vector(L[j]) - Vector(c0)
        own_pt = p + (side * own.x + nup * own.z + tg * own.y) * (r / r0)
        q = own_pt.lerp(circ, blend)
        v = bm.verts.new(q)
        ring.append(v)
    for j in range(N):
        a0, a1 = prev_ring[j], prev_ring[(j + 1) % N]
        b0, b1 = ring[j], ring[(j + 1) % N]
        try:
            bm.faces.new((a0, a1, b1, b0))
        except ValueError:
            pass
    rings.append(ring)
    prev_ring = ring
tipv = bm.verts.new(at(total)[0] + at(total)[1] * TAIL_TIP_R)
for j in range(N):
    bm.faces.new((prev_ring[j], prev_ring[(j + 1) % N], tipv))
# Meshy left small holes in the skin (pinholes behind the eyes, at the toes): fill them
bm.edges.ensure_lookup_table()
holes = [e for e in bm.edges if e.is_boundary]
report['holes_boundary_edges'] = len(holes)
bmesh.ops.holes_fill(bm, edges=holes, sides=64)
# holes with a pinched rim (a vertex on two boundary loops, or a non-manifold edge) do not fill: drop the faces
# around them and fill the opened hole, up to four rings out
for _ in range(4):
    bad_v = {v for e in bm.edges if e.is_boundary or len(e.link_faces) > 2 for v in e.verts}
    if not bad_v:
        break
    bmesh.ops.delete(bm, geom=list({f for v in bad_v for f in v.link_faces}), context='FACES')
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.holes_fill(bm, edges=[e for e in bm.edges if e.is_boundary], sides=128)
bmesh.ops.triangulate(bm, faces=bm.faces)
# faces stacked on another face's vertices (Meshy folds) make the last non-manifold edges: keep one of each
dup, keys = [], set()
bm.verts.index_update()
for f in bm.faces:
    k = frozenset(v.index for v in f.verts)
    if k in keys:
        dup.append(f)
    keys.add(k)
bmesh.ops.delete(bm, geom=dup, context='FACES_ONLY')
report['duplicate_faces'] = len(dup)
bm.normal_update()
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
report['boundary_edges_after'] = sum(1 for e in bm.edges if e.is_boundary)
report['nonmanifold_edges'] = sum(1 for e in bm.edges if len(e.link_faces) > 2)
# smooth the mirror seam (a V crease where Meshy's surface met x = 0 at an angle) and the rump/tail junction
c0v = Vector(c0)
seam = [v for v in bm.verts if abs(v.co.x) < 0.0025 and v.co.y < c0v.y - 0.002 and v.co.z > 0.004]
junction = [v for v in bm.verts if (v.co - c0v).length < 0.009]
for _ in range(8):
    bmesh.ops.smooth_vert(bm, verts=seam, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
for _ in range(10):
    bmesh.ops.smooth_vert(bm, verts=junction, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
report['smoothed'] = {'seam': len(seam), 'junction': len(junction)}
tail_index = {}
for k, ring in enumerate(rings):
    for v in ring:
        tail_index[v] = k / n_rings
tail_index[tipv] = 1.0
report['tail_rings'] = n_rings

# ---- eyes
bm.verts.ensure_lookup_table()
P = np.array([tuple(v.co) for v in bm.verts])
H = float(np.percentile(P[(P[:, 1] > -0.06) & (P[:, 1] < -0.02), 2], 99.5))   # back height (no ears)
snout = P[:, 1].min()
# the Meshy head has an eye pit where the masters put the eye (3/4 of the way from the ear's front edge to the snout
# tip, as in 04_right.png): measured on the fitted mesh (right view), the sphere is seated in it
eye_y = EYE_Y
eye_z = EYE_Z
eye_r = EYE_R * H
# Meshy's whisker roots and eye spot left a rough, noisy muzzle: smooth the face in front of the ears
face = [v for v in bm.verts if v.co.y < eye_y + 0.006 and v.co.z < eye_z + 0.006 and v.co.z > 0.004]
for _ in range(6):
    bmesh.ops.smooth_vert(bm, verts=face, factor=0.35, use_axis_x=True, use_axis_y=True, use_axis_z=True)
report['smoothed']['face'] = len(face)
tree = BVHTree.FromBMesh(bm)
hit = tree.ray_cast(Vector((-0.2, eye_y, eye_z)), Vector((1, 0, 0)))
report['eye'] = {'H': H, 'y': eye_y, 'z': eye_z, 'r': eye_r, 'surface_x': hit[0].x if hit[0] else None}
assert hit[0] is not None
nrm = hit[1].normalized()
centre_r = hit[0] - nrm * (eye_r * EYE_SINK)
eye_faces = []
for sgn in (1, -1):
    c = Vector((centre_r.x * sgn, centre_r.y, centre_r.z))
    ret = bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=eye_r,
                                    matrix=Matrix.Translation(c))
    eye_faces += [f for f in {f for v in ret['verts'] for f in v.link_faces}]
bmesh.ops.triangulate(bm, faces=eye_faces)
eye_set = {v for f in eye_faces for v in f.verts}

me = bpy.data.meshes.new('Body')
bm.verts.ensure_lookup_table()
idx_piece = [1 if v in eye_set else 0 for v in bm.verts]
idx_part = [2 if v in eye_set else (1 if tail_index.get(v, 0) > 0 else 0)
            for v in bm.verts]
idx_t = [tail_index.get(v, -1.0) if v not in eye_set else -1.0 for v in bm.verts]
bm.to_mesh(me)
for name, vals, kind in (('piece', idx_piece, 'INT'), ('part', idx_part, 'INT'), ('tail_t', idx_t, 'FLOAT')):
    at_ = me.attributes.new(name, kind, 'POINT')
    for i, x in enumerate(vals):
        at_.data[i].value = x
for p in me.polygons:
    p.use_smooth = True
body = bpy.data.objects.new('Body', me)
sc.collection.objects.link(body)
P = np.array([tuple(v.co) for v in me.vertices])
report['bounds'] = [P.min(0).tolist(), P.max(0).tolist()]
report['tris'] = sum(len(p.vertices) - 2 for p in me.polygons)
report['verts'] = len(me.vertices)
# symmetry check: mean distance of mirrored body vertices to the nearest body vertex
from mathutils.kdtree import KDTree
kd = KDTree(len(P)); [kd.insert(Vector(p), i) for i, p in enumerate(P)]; kd.balance()
body_ids = [i for i in range(len(P)) if idx_part[i] == 0]
d = [kd.find(Vector((-P[i, 0], P[i, 1], P[i, 2])))[2] for i in body_ids]
report['symmetry_body_max_mm'] = 1000 * max(d)
bpy.ops.wm.save_as_mainfile(filepath=OUT)
json.dump(report, open(REP, 'w'), indent=1)
print('FIT ' + json.dumps(report))
