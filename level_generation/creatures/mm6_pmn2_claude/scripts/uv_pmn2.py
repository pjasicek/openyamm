"""UV atlas for the unrigged pmn2 mesh (work/step1_v1.blend -> work/step1_uv.blend). No rig yet, so body regions
are geometric: torso (incl. hips under the skirt), upper arm, forearm (bracer) per side from the shoulder-wrist axis,
leg per side; skin/cloth never seen at rest (skull under hair, body under mantle/skirt) is split off into low-density
hidden regions. Region borders are seams; tubes get one more seam on their hidden side. Cloth/head/hair/body are
unwrapped angle-based; boots, fists, rope and pouches use Smart UV Project. Densities are equalised
per region then biased (face up, hidden/legs down); folded triangles are cut out and the unwrap repeated until the
1024^2 overlap raster is clean."""
import bpy, bmesh, sys, os, math, json, collections
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'step1_v1.blend'))
mesh = bpy.data.objects['Mage']; me = mesh.data
PARTS = json.loads(bpy.context.scene['pmn2_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')

SHOULDER = {1: Vector((0.19, 0.03, 1.21)), -1: Vector((-0.19, 0.03, 1.21))}
WRIST = {1: Vector((0.413, 0.0, 0.87)), -1: Vector((-0.413, 0.0, 0.87))}
CROTCH, BOOT_TOP, BRACER_T = 0.66, 0.40, 0.25          # boot rim and bracer top crease rings (measured)
METHOD = os.environ.get('UV_METHOD', 'MINIMUM_STRETCH')
SIDE = {1: 'L', -1: 'R'}                                   # character left = +X


def body_region(p):
    sx = 1 if p.x > 0 else -1
    s, w = SHOULDER[sx], WRIST[sx]
    d = w - s; L = d.length; d.normalize()
    t = (p - s).dot(d)
    if t > 0 and (p - s - d * t).length < 0.085 and p.x * sx > 0.15:
        return ('ForeArm' if t > BRACER_T else 'Arm') + SIDE[sx]
    if p.z < BOOT_TOP:
        return 'Boot' + SIDE[sx]
    if p.z < CROTCH:
        return 'Leg' + SIDE[sx]
    return 'Torso'


# straight edge loops on the bracer tops and boot rims, so those texture borders are clean seams
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table()
pl = bm.faces.layers.int.get('part')
for sx in (1, -1):
    s, w = SHOULDER[sx], WRIST[sx]; d = (w - s).normalized()
    near = lambda c: c.x * sx > 0.15 and 0.15 < (c - s).dot(d) < 0.35 and (c - s - d * (c - s).dot(d)).length < 0.085
    geom = [f for f in bm.faces if f[pl] == 0 and near(f.calc_center_median())]
    geom = geom + list({e for f in geom for e in f.edges}) + list({v for f in geom for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=s + d * BRACER_T, plane_no=d)
    geom = [f for f in bm.faces if f[pl] == 0 and f.calc_center_median().x * sx > 0.0 and 0.3 < f.calc_center_median().z < 0.5]
    geom = geom + list({e for f in geom for e in f.edges}) + list({v for f in geom for v in f.verts})
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=Vector((0, 0, BOOT_TOP)), plane_no=Vector((0, 0, 1)))
bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 3])
bm.to_mesh(me); bm.free()
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
bm = bmesh.new(); bm.from_mesh(me); bm.faces.ensure_lookup_table(); bm.verts.ensure_lookup_table()
COVERS = {'Body': ('Mantle', 'Skirt')}
trees = {}
for inner, outer in COVERS.items():
    fs = [f for f in bm.faces if PARTS[part[f.index]] in outer]
    vi = sorted({v.index for f in fs for v in f.verts}); remap = {v: i for i, v in enumerate(vi)}
    trees[inner] = BVHTree.FromPolygons([bm.verts[v].co.copy() for v in vi], [[remap[v.index] for v in f.verts] for f in fs])


def covered(f):
    """Face centre and every corner are under the covering shell along the normal (within 4 cm)."""
    t = trees.get(PARTS[part[f.index]])
    if t is None:
        return False
    pts = [(f.calc_center_median(), f.normal)] + [(v.co, v.normal) for v in f.verts]
    return all(t.ray_cast(p + n * 1e-4, n, 0.04)[0] is not None for p, n in pts)


breg = {f.index: body_region(f.calc_center_median()) for f in bm.faces if PARTS[part[f.index]] == 'Body'}
CUT = {'Arm', 'ForeArm', 'Boot', 'Leg'}                 # borders that run on the new loops stay as they are
for _ in range(3):
    nxt = dict(breg)
    for f in bm.faces:
        if f.index not in breg:
            continue
        nb = [breg[g.index] for e in f.edges for g in e.link_faces if g is not f and g.index in breg]
        top = max(set(nb), key=nb.count) if nb else breg[f.index]
        pair = {breg[f.index].rstrip('LR'), top.rstrip('LR')}
        if nb.count(top) * 2 > len(nb) and not pair <= CUT:
            nxt[f.index] = top
    breg = nxt


cov = [covered(f) for f in bm.faces]
for _ in range(3):                                      # majority filter: contiguous hidden patches, no speckle
    nxt = list(cov)
    for f in bm.faces:
        nb = [g for e in f.edges for g in e.link_faces if g is not f and part[g.index] == part[f.index]]
        if nb:
            k = sum(cov[g.index] for g in nb)
            nxt[f.index] = k * 2 > len(nb) or (k * 2 == len(nb) and cov[f.index])
    cov = nxt


def face_region(f):
    p = PARTS[part[f.index]]
    hidden = cov[f.index]
    if p == 'Head':                                     # face front at full density; skull, neck, ears lower
        c = f.calc_center_median()
        return 'Head' if c.y < -0.04 and c.z > 1.33 else 'HeadBack'
    if p != 'Body':
        return p
    r = breg[f.index]
    if hidden and not r.startswith(('Arm', 'ForeArm', 'Boot')):
        return 'BodyHidden'
    return r


freg = [face_region(f) for f in bm.faces]
bm.free()
SMART = {'HandRight': 75, 'HandLeft': 75, 'BootL': 66, 'BootR': 66, 'Rope': 70, 'RopeKnot': 70, 'RopeTailL': 70,
         'RopeTailR': 70, 'PouchRight': 70, 'PouchLeft': 70, 'EyeL': 70, 'EyeR': 70, 'BodyHidden': 66}
SMALL = set(SMART)


def axis_frame(region):
    """(origin, axis, hidden-side direction) for the extra seam in tube-like regions."""
    if region in ('Torso', 'HeadBack', 'Hair', 'Skirt'):
        return Vector((0, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))          # back
    for sx, sd in SIDE.items():
        if region in ('Arm' + sd, 'ForeArm' + sd):
            d = (WRIST[sx] - SHOULDER[sx]).normalized()
            return SHOULDER[sx], d, Vector((0, 0, -1))                          # underside
        if region == 'Leg' + sd:
            return Vector((sx * 0.1, 0, 0)), Vector((0, 0, 1)), Vector((-sx, 0.6, 0))   # inner back
    return None


bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
for e in bm.edges:
    e.seam = len(e.link_faces) == 2 and freg[e.link_faces[0].index] != freg[e.link_faces[1].index]
for region in set(freg) - SMALL:
    frame = axis_frame(region)
    if frame is None:
        continue
    origin, axis, ref = frame
    ref = (ref - axis * ref.dot(axis)).normalized(); side_ref = axis.cross(ref).normalized()
    faces = [f for f in bm.faces if freg[f.index] == region]; fset = {f.index for f in faces}
    ang = {}
    for f in faces:
        for v in f.verts:
            d = v.co - origin; d -= axis * d.dot(axis)
            ang[v.index] = math.atan2(d.dot(side_ref), d.dot(ref))             # 0 = hidden side
    for f in faces:
        for e in f.edges:
            a, b = (ang[v.index] for v in e.verts)
            if abs(a) < math.pi / 2 and abs(b) < math.pi / 2 and a * b <= 0 and all(lf.index in fset for lf in e.link_faces):
                e.seam = True
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
edge_lookup = {e.key: e.index for e in me.edges}
BIAS = {'Head': 2.4, 'EyeL': 2.4, 'EyeR': 2.4, 'HandRight': 1.4, 'HandLeft': 1.4, 'Hair': 1.1, 'Mantle': 1.0,
        'Skirt': 0.85, 'LegL': 0.7, 'LegR': 0.7, 'BootL': 0.7, 'BootR': 0.7, 'HeadBack': 0.9, 'BodyHidden': 0.35,
        'Rope': 0.8, 'RopeKnot': 0.8, 'RopeTailL': 0.8, 'RopeTailR': 0.8, 'PouchRight': 0.8, 'PouchLeft': 0.8}
for attempt in range(8):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = freg[f.index] not in SMALL
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method=METHOD, margin=0.0)
    for angle in sorted(set(SMART.values())):
        bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
        for f in bm.faces:
            f.select = SMART.get(freg[f.index]) == angle
        bmesh.update_edit_mesh(me)
        bpy.ops.uv.smart_project(angle_limit=math.radians(angle), island_margin=0.0, scale_to_bounds=False)
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active

    def uv_area(f):
        pts = [l[uv].uv for l in f.loops]
        return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                       for i in range(len(pts)))) / 2

    by_region = collections.defaultdict(list)
    for f in bm.faces:
        by_region[freg[f.index]].append(f)
    for region, faces in by_region.items():
        a3 = sum(f.calc_area() for f in faces); a2 = sum(uv_area(f) for f in faces)
        if a2 <= 0:
            continue
        k = math.sqrt(a3 / a2) * BIAS.get(region, 1.0)
        loops = [l for f in faces for l in f.loops]
        c = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
        for l in loops:
            l[uv].uv = c + (l[uv].uv - c) * k
    for f in bm.faces:
        f.select = True
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.004)
    bpy.ops.object.mode_set(mode='OBJECT')
    me.calc_loop_triangles(); uvl = me.uv_layers.active.data; R = 1024
    owner = np.full((R, R), -1, dtype=np.int64); overlap = set()
    for ti, t in enumerate(me.loop_triangles):
        p = np.array([tuple(uvl[li].uv) for li in t.loops]) * R
        x0, y0 = np.floor(p.min(0)).astype(int); x1, y1 = np.ceil(p.max(0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, R - 1), min(y1, R - 1)
        if x1 < x0 or y1 < y0:
            continue
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        a_, b_, c_ = p
        d = (b_[1] - c_[1]) * (a_[0] - c_[0]) + (c_[0] - b_[0]) * (a_[1] - c_[1])
        if abs(d) < 1e-12:
            continue
        w0 = ((b_[1] - c_[1]) * (gx - c_[0]) + (c_[0] - b_[0]) * (gy - c_[1])) / d
        w1 = ((c_[1] - a_[1]) * (gx - c_[0]) + (a_[0] - c_[0]) * (gy - c_[1])) / d
        inside = (w0 > 0.02) & (w1 > 0.02) & (1 - w0 - w1 > 0.02)
        ys, xs = np.nonzero(inside)
        prev = owner[y0 + ys, x0 + xs]
        if (prev >= 0).any():
            overlap.add(ti); overlap.update(int(q) for q in np.unique(prev[prev >= 0]))
        owner[y0 + ys, x0 + xs] = ti
    where = collections.Counter(freg[me.loop_triangles[ti].polygon_index] for ti in overlap)
    print('ATTEMPT', attempt, 'OVERLAP_TRIS', len(overlap), dict(where))
    if not overlap:
        break
    for pi in {me.loop_triangles[ti].polygon_index for ti in overlap}:
        for ek in me.polygons[pi].edge_keys:
            me.edges[edge_lookup[ek]].use_seam = True
reg_attr = me.attributes.new('uv_region', 'INT', 'FACE')
names = sorted(set(freg)); reg_attr.data.foreach_set('value', [names.index(r) for r in freg])
bpy.context.scene['pmn2_uv_regions'] = json.dumps(names)
print('UV regions', names, 'seams', sum(1 for e in me.edges if e.use_seam))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'step1_uv.blend'))
