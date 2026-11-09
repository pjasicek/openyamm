"""Step 1 (geometry only): clean the Meshy Smart Topology mesh before rigging.

- delete floating fragments and the hidden mouth-interior strip (no jaw animation)
- hair: remove the two ribbon tails, lay the floating front edge onto the skin (no shelf), add nape volume
- add a nape ponytail braid (tie + lobed tail) and a thin headband circlet, fitted by ray casts
- reduce triangles only where they do not show: shoes, legs hidden under the skirt, skin hidden under hair/
  clothing, flat torso back. Face, hands, sleeves and skirt pleats are protected.
Output: work/step1_v1.blend (separate named parts) + review renders.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common, load_smart

parts = {k: v[0] for k, v in load_smart.load(os.path.join(common.PROJECT, 'meshy/smart_topology_v1/model_urls_glb.glb')).items()}
for name in ('Junk', 'MouthInner'):
    for o in [o for o in bpy.data.objects if o.name.startswith(name)]:
        bpy.data.objects.remove(o, do_unlink=True)
parts = {k: bpy.data.objects[k] for k in ('Body', 'Skirt', 'Hair', 'LegLeft', 'LegRight', 'EyeLeft', 'EyeRight', 'Belt', 'Buckle')}


def tris(o):
    return sum(len(p.vertices) - 2 for p in o.data.polygons)


before = {k: tris(o) for k, o in parts.items()}


def tree_of(objs):
    verts, polys = [], []
    for o in objs:
        base = len(verts)
        verts += [o.matrix_world @ v.co for v in o.data.vertices]
        polys += [tuple(base + i for i in p.vertices) for p in o.data.polygons]
    return BVHTree.FromPolygons(verts, polys)


body_tree = tree_of([parts['Body']])

# ------------------------------------------------------------------ hair
hair = parts['Hair']
bm = bmesh.new(); bm.from_mesh(hair.data)
bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < 1.368
                            or (v.co.z < 1.398 and v.co.y > 0.03 and abs(v.co.x) < 0.058)], context='VERTS')
bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
bm.verts.ensure_lookup_table()
# The face-side free edge is the long boundary loop that reaches the forehead; the nape cut is the other one.
front = [v for v in bm.verts if v.is_boundary and (v.co.z > 1.40 or v.co.y < 0.03)]
nape_edges = [e for e in bm.edges if e.is_boundary and all(v.co.z < 1.41 and v.co.y >= 0.03 for v in e.verts)]
filled = bmesh.ops.holes_fill(bm, edges=nape_edges, sides=0)['faces']
filled = bmesh.ops.triangulate(bm, faces=filled)['faces']
centre_guess = Vector((0.0, 0.0, 1.46))
for f in filled:  # keep the patch facing outward like its neighbours
    f.normal_update()
    if f.normal.dot(f.calc_center_median() - centre_guess) < 0:
        f.normal_flip()
bm.verts.ensure_lookup_table()
# Graph distance (rings) from the front edge.
ring = {v.index: 0 for v in front}
frontier = list(front)
for depth in range(1, 4):
    nxt = []
    for v in frontier:
        for e in v.link_edges:
            w = e.other_vert(v)
            if w.index not in ring:
                ring[w.index] = depth; nxt.append(w)
    frontier = nxt
# Lay the edge onto the skin (1.5 mm proud) and blend the next rings; then relax the edge so it is a smooth curve.
pull = {0: 1.0, 1: 0.6, 2: 0.3, 3: 0.1}
for v in bm.verts:
    if v.index in ring:
        hit = body_tree.find_nearest(v.co)
        target = hit[0] + hit[1] * 0.0015
        v.co = v.co.lerp(target, pull[ring[v.index]])
for _ in range(4):
    bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if ring.get(v.index, 9) <= 1], factor=0.5,
                          use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for v in bm.verts:
        if ring.get(v.index, 9) == 0:
            hit = body_tree.find_nearest(v.co); v.co = hit[0] + hit[1] * 0.0015
# Gathered volume at the back of the head (reference: fuller hair toward the nape tie).
bm.normal_update()
for v in bm.verts:
    if v.co.y > 0.0 and 1.37 < v.co.z < 1.50 and v.index not in ring:
        t = math.sin(math.pi * (v.co.z - 1.37) / 0.13) * min(1.0, v.co.y / 0.05)
        v.co += v.normal * 0.007 * t
# Gather the back-bottom hair toward the nape tie (reference: hair drawn into a low ponytail, no bob edge).
for v in bm.verts:
    if v.co.y > 0.0 and v.co.z < 1.46 and v.index not in ring:
        t = min(1.0, (1.46 - v.co.z) / 0.07) ** 1.5 * min(1.0, v.co.y / 0.04)
        v.co.x *= 1.0 - 0.45 * t
        v.co.z += 0.010 * t * min(1.0, abs(v.co.x) / 0.04)
for _ in range(2):
    bmesh.ops.smooth_vert(bm, verts=[v for v in bm.verts if v.co.y > 0.0 and v.co.z < 1.45 and v.index not in ring],
                          factor=0.4, use_axis_x=True, use_axis_y=True, use_axis_z=True)
bm.to_mesh(hair.data); bm.free(); hair.data.update()
hair_tree = tree_of([hair])

hc = np.array([tuple(v.co) for v in hair.data.vertices])
head_centre = Vector((float((hc[:, 0].max() + hc[:, 0].min()) / 2), float((hc[:, 1].max() + hc[:, 1].min()) / 2), 1.47))


def make_mesh(name, rings, closed=True, cap_start=False, cap_end=False):
    n = len(rings[0]); verts = [tuple(v) for r in rings for v in r]; faces = []
    for r in range(len(rings) - 1):
        for s in range(n if closed else n - 1):
            a = r * n + s; b = r * n + (s + 1) % n
            faces.append((a, b, b + n, a + n))
    if cap_start:
        verts.append(tuple(sum(rings[0], Vector()) / n)); c = len(verts) - 1
        faces += [(c, (s + 1) % n, s) for s in range(n)]
    if cap_end:
        verts.append(tuple(sum(rings[-1], Vector()) / n)); c = len(verts) - 1; base = (len(rings) - 1) * n
        faces += [(c, base + s, base + (s + 1) % n) for s in range(n)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, [], faces); me.update()
    o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
    for p in me.polygons:
        p.use_smooth = True
    return o


def back_surface_y(z, x=0.0):
    hit = None
    for tree in (hair_tree, body_tree):
        h = tree.ray_cast(Vector((x, 0.5, z)), Vector((0, -1, 0)), 1.0)
        if h[0] is not None and (hit is None or h[0].y > hit):
            hit = h[0].y
    return hit


# ------------------------------------------------------------------ braid (low ponytail with tie, lobed tail)
z_tie, z_end = 1.392, 1.245
SEG, N = 10, 18
path = []
for k in range(N):
    t = k / (N - 1)
    z = z_tie + 0.012 - (z_tie + 0.012 - z_end) * t
    surf = back_surface_y(z) or 0.08
    radius_guess = 0.024 * (1 - t) + 0.014 * t
    clearance = -0.012 if k < 2 else radius_guess + 0.004  # root sinks into the hair mass
    path.append(Vector((0.0, surf + clearance, z)))
for _ in range(3):  # smooth the centre line
    path = [path[0]] + [(path[i - 1] + path[i] * 2 + path[i + 1]) / 4 for i in range(1, N - 1)] + [path[-1]]
rings = []
for k, p in enumerate(path):
    if k <= 1:
        r = 0.027
    elif k == 2:
        r = 0.017                                   # tie
    else:
        u = (k - 3) / (N - 4)
        r = 0.024 - 0.005 * u                        # plump tail
        tip = N - 1 - k
        if tip < 3:
            r *= (0.25, 0.62, 0.86)[tip]             # rounded end
    tangent = (path[min(k + 1, N - 1)] - path[max(k - 1, 0)]).normalized()
    a = tangent.cross(Vector((1, 0, 0))).normalized(); b = tangent.cross(a).normalized()
    twist = k * 0.25
    side = 0.0
    rings.append([p + a * 0 + Vector((side, 0, 0)) + (b * math.cos(2 * math.pi * s / SEG + twist) * 1.08 + a * math.sin(2 * math.pi * s / SEG + twist)) * r
                  for s in range(SEG)])
braid = make_mesh('Braid', rings, cap_end=True)
braid['path'] = [tuple(p) for p in path]

# ------------------------------------------------------------------ headband circlet on the hair
BAND_SEG = 36
head_tree = tree_of([hair, parts['Body']])
band_rows = []
radii = []
for s in range(BAND_SEG):
    phi = 2 * math.pi * s / BAND_SEG
    d = Vector((math.sin(phi), -math.cos(phi), 0.0))
    z = 1.516 + 0.020 * (1 - math.cos(phi)) / 2     # on the front hairline, slightly higher at the back
    origin = Vector((head_centre.x, head_centre.y, z))
    h = head_tree.ray_cast(origin + d * 0.3, -d, 0.3)
    radii.append((0.3 - h[3]) if h[0] is not None else 0.09)
radii = np.convolve(np.r_[radii[-2:], radii, radii[:2]], np.ones(5) / 5, mode='valid')
for dz, dr in ((-0.0028, 0.0), (-0.0028, 0.0026), (0.0028, 0.0026), (0.0028, 0.0)):
    row = []
    for s in range(BAND_SEG):
        phi = 2 * math.pi * s / BAND_SEG
        z = 1.516 + 0.020 * (1 - math.cos(phi)) / 2 + dz
        row.append(Vector((head_centre.x, head_centre.y, z)) + Vector((math.sin(phi), -math.cos(phi), 0)) * (radii[s] + 0.001 + dr))
    band_rows.append(row)
headband = make_mesh('Headband', band_rows + [band_rows[0]], closed=True)

# ------------------------------------------------------------------ triangle reduction where it does not show
cover_tree = tree_of([parts['Skirt'], hair, parts['Belt']])


def decimate(obj, weight_fn, ratio):
    g = obj.vertex_groups.new(name='decimate_weight')
    obj.data.update()
    for v in obj.data.vertices:
        g.add([v.index], float(weight_fn(v)), 'REPLACE')
    m = obj.modifiers.new('Decimate', 'DECIMATE')
    m.ratio = ratio; m.vertex_group = g.name; m.use_collapse_triangulate = True
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=m.name)
    obj.vertex_groups.remove(obj.vertex_groups[g.name])


def covered(v, reach=0.05):
    h = cover_tree.ray_cast(v.co + v.normal * 1e-4, v.normal, reach)
    return h[0] is not None


for side in ('LegLeft', 'LegRight'):
    leg = parts[side]
    bm = bmesh.new(); bm.from_mesh(leg.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z > 0.50], context='VERTS')  # knees are never visible
    bm.to_mesh(leg.data); bm.free()
    decimate(leg, lambda v: 0.25 if 0.10 < v.co.z < 0.24 else 1.0, 0.32)

face_y = -0.02


def body_weight(v):
    c = v.co
    if c.z > 1.33:
        if covered(v, 0.04):
            return 1.0                       # skull under hair
        return 0.0 if c.y < face_y else 0.35  # face protected, neck/nape lighter
    if abs(c.x) > 0.30 and c.z < 1.02:
        return 0.0                           # hands
    if covered(v):
        return 1.0                           # hips under skirt / waist under belt
    if c.y > 0.02 and 0.98 < c.z < 1.30 and abs(c.x) < 0.14:
        return 0.75                          # flat torso back
    return 0.2


decimate(parts['Body'], body_weight, 0.74)

after = {k: tris(o) for k, o in list(parts.items()) + [('Braid', braid), ('Headband', headband)]}
report = {'before': before, 'after': after, 'total_before': 15261, 'total_after': sum(after.values()),
          'removed': ['3 floating fragments', 'mouth interior strip', 'hair ribbon tails', 'legs above 0.50 m']}
json.dump(report, open(os.path.join(common.WORK, 'step1_report.json'), 'w'), indent=1)
print('STEP1', json.dumps(report))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))

scene = bpy.context.scene
common.workbench_clay(scene)
common.render_views(os.path.join(common.REVIEW, 'step1'), 0.8, 1.72, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 900))
common.render_views(os.path.join(common.REVIEW, 'step1_head'), 1.42, 0.40, views=('front', 'three_quarter', 'left', 'back'), resolution=(600, 600))
