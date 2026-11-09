"""Fresh UVs for the 45 % female peasant (work/r45_master.blend), from mm6_pfem_claude/scripts/uv_atlas_v2.py.
Body set: that atlas without the head-set faces (face attribute `head`); head set: its own 0..1 layout with the face
skin at 1.8x the hair density (head_layout below). Gate: no triangle below 5 % of its set's median UV density
(the reduced mesh's carried UVs had slivers that render black in three.js).

Original notes:

Body regions come from the dominant skin bone (head, torso, upper arm, forearm, hand per side); region borders
are seams. Tubes get one extra seam on their hidden side (torso/head/legs/hair/skirt at the back, arms underneath).
Everything is unwrapped conformally, densities are equalised per region then biased (face up, hidden parts down),
and packed into one 0..1 atlas. Small rigid parts use Smart UV Project.
"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

mesh = bpy.data.objects['Peasant']; rig = bpy.data.objects['Peasant_Rig']
rig.animation_data.action = None
for b in rig.pose.bones:
    b.matrix_basis.identity()
bpy.context.view_layer.update()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
P = {n: i for i, n in enumerate(PARTS)}
me = mesh.data
while me.uv_layers:
    me.uv_layers.remove(me.uv_layers[0])
me.uv_layers.new(name='UVMap')
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
headf = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['head'].data.foreach_get('value', headf)
groups = {g.index: g.name for g in mesh.vertex_groups}


def region_of_vertex(v):
    best, w = '', 0.0
    for g in v.groups:
        if g.weight > w:
            best, w = groups[g.group], g.weight
    n = best.replace('mixamorig:', '')
    # twist bones (twist_bones.py, added after the original UV pass) belong to their arm segment
    n = n.replace('ForeArmTwist1', 'ForeArm').replace('ForeArmTwist2', 'ForeArm').replace('ArmTwist', 'Arm')
    for side in ('Left', 'Right'):
        for finger in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky'):
            if n.startswith(side + 'Hand' + finger):
                return n                                  # one island per phalanx
        if n.startswith(side + 'Hand'):
            return side + 'Hand'
        if n == side + 'ForeArm':
            return side + 'ForeArm'
        if n == side + 'Arm':
            return side + 'Arm'
    if n == 'Head':
        return 'Head'
    return 'Torso'


vregion = [region_of_vertex(v) for v in me.vertices]
bones = {b.name.replace('mixamorig:', ''): b for b in rig.data.bones}


def axis_frame(region):
    """Axis origin/direction and the 'hidden side' reference direction for tube seams."""
    if region in ('Torso', 'Head', 'Hair', 'Skirt'):
        return Vector((0, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))      # seam at the back (+Y)
    for side in ('Left', 'Right'):
        if region.startswith(side) and region[len(side):] in ('Arm', 'ForeArm'):
            b = bones[region]
            return b.head_local, (b.tail_local - b.head_local).normalized(), Vector((0, 0, -1))  # underside
        if region.startswith(side + 'Hand') and region != side + 'Hand':
            f1 = f3 = bones[region]
            hand = bones[side + 'Hand'].head_local
            across = (bones[side + 'HandIndex1'].head_local - bones[side + 'HandPinky1'].head_local).normalized()
            fdir = (bones[side + 'HandMiddle1'].head_local - hand).normalized()
            palm = -across.cross(fdir).normalized() if side == 'Right' else across.cross(fdir).normalized()
            return f1.head_local, (f3.tail_local - f1.head_local).normalized(), palm   # seam on the palm side
        if region in ('LegLeft', 'LegRight'):
            return Vector((0.1 if region == 'LegLeft' else -0.1, 0, 0)), Vector((0, 0, 1)), Vector((0, 1, 0))
    return None


bpy.context.view_layer.objects.active = mesh
for o in bpy.data.objects:
    o.select_set(o == mesh)
bpy.ops.object.mode_set(mode='EDIT')
bm = bmesh.from_edit_mesh(me)
bm.faces.ensure_lookup_table(); bm.edges.ensure_lookup_table(); bm.verts.ensure_lookup_table()
for e in bm.edges:
    e.seam = False


def face_region(f):
    if headf[f.index]:
        return 'HeadSet'
    p = PARTS[part[f.index]]
    if p != 'Body':
        return p
    regs = [vregion[v.index] for v in f.verts]
    return max(set(regs), key=regs.count)


freg = [face_region(f) for f in bm.faces]
# 1. borders between regions/parts
for e in bm.edges:
    if len(e.link_faces) == 2 and freg[e.link_faces[0].index] != freg[e.link_faces[1].index]:
        e.seam = True
# 2. hidden-side seam inside each tube-like region
for region in set(freg):
    frame = axis_frame(region)
    if frame is None:
        continue
    origin, axis, ref = frame
    ref = (ref - axis * ref.dot(axis)).normalized()
    side_ref = axis.cross(ref).normalized()
    faces = [f for f in bm.faces if freg[f.index] == region]
    verts = {v for f in faces for v in f.verts}
    ang = {}
    for v in verts:
        d = v.co - origin; d -= axis * d.dot(axis)
        ang[v.index] = math.atan2(d.dot(side_ref), d.dot(ref))     # 0 = hidden side
    region_faces = set(f.index for f in faces)
    for f in faces:
        for e in f.edges:
            a, b = (ang[v.index] for v in e.verts)
            if abs(a) < math.pi / 2 and abs(b) < math.pi / 2 and a * b <= 0 and all(
                    lf.index in region_faces for lf in e.link_faces):
                e.seam = True
bmesh.update_edit_mesh(me)
bpy.ops.object.mode_set(mode='OBJECT')
edge_lookup = {e.key: e.index for e in me.edges}
for attempt in range(6):
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    small = {P[n] for n in ('EyeLeft', 'EyeRight', 'Belt', 'Buckle', 'Braid', 'Headband', 'Knife')}
    for f in bm.faces:                      # the head set is laid out by head_layout()
        f.hide_set(bool(headf[f.index]))
    for f in bm.faces:
        f.select = part[f.index] not in small and not headf[f.index]
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0)
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = part[f.index] in small and not headf[f.index]
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(60), island_margin=0.0, scale_to_bounds=False)

    # 3b. tubes whose hidden-side seam did not cut through on the reduced mesh fold up under angle-based unwrapping
    # (forearms, phalanges): a region with any face below 10 % of its median density is smart-projected instead.
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
    dens = {}
    for f in bm.faces:
        if headf[f.index] or f.calc_area() < 1e-10:
            continue
        pts = [l[uv].uv for l in f.loops]
        a2 = abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                     for i in range(len(pts)))) / 2
        dens.setdefault(freg[f.index], []).append(a2 / f.calc_area())
    folded = {r for r, v in dens.items() if min(v) < 0.1 * float(np.median(v))}
    for f in bm.faces:
        f.select = freg[f.index] in folded and not headf[f.index]
    bmesh.update_edit_mesh(me)
    if folded:
        bpy.ops.uv.smart_project(angle_limit=math.radians(80), island_margin=0.0, scale_to_bounds=False)
    print('REPROJECTED', sorted(folded))

    # 4. densities: equalise per region, then bias
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active


    def uv_area(f):
        pts = [l[uv].uv for l in f.loops]
        return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                       for i in range(len(pts)))) / 2


    BIAS = {'Head': 2.6, 'LeftHand': 1.4, 'RightHand': 1.4,
            **{f'{sd}Hand{f}{k}': 1.4 for sd in ('Left', 'Right') for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for k in (1, 2, 3)}, 'Skirt': 0.7, 'LegLeft': 0.5, 'LegRight': 0.5,
            'Hair': 1.1, 'Knife': 0.6}
    by_region = {}
    for f in bm.faces:
        if not headf[f.index]:
            by_region.setdefault(freg[f.index], []).append(f)
    for region, faces in by_region.items():
        a3 = sum(f.calc_area() for f in faces); a2 = sum(uv_area(f) for f in faces)
        if a2 <= 0:
            continue
        k = math.sqrt(a3 / a2) * BIAS.get(region, 1.0)
        loops = [l for f in faces for l in f.loops]
        c = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
        for l in loops:
            l[uv].uv = c + (l[uv].uv - c) * k
    bmesh.update_edit_mesh(me)
    for f in bm.faces:
        f.select = not headf[f.index]
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.003, shape_method='CONCAVE')
    bm = bmesh.from_edit_mesh(me)
    for f in bm.faces:
        f.hide_set(False)
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')
    seams = sum(1 for e in me.edges if e.use_seam)
    # Overlap gate: rasterise triangle ids at 1024^2; any texel claimed by two non-adjacent triangles is a fold.
    me.calc_loop_triangles(); uvl = me.uv_layers.active.data; R = 1024
    owner = np.full((R, R), -1, dtype=np.int64); overlap_tris = set()
    for ti, t in enumerate(me.loop_triangles):
        if headf[t.polygon_index]:
            continue
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
            overlap_tris.add(ti); overlap_tris.update(int(q) for q in np.unique(prev[prev >= 0]))
        owner[y0 + ys, x0 + xs] = ti
    print('OVERLAP_TRIS', len(overlap_tris))
    import collections
    lab = collections.Counter()
    for ti in overlap_tris:
        pi = me.loop_triangles[ti].polygon_index
        lab[PARTS[part[pi]] if PARTS[part[pi]] != 'Body' else 'Body:' + freg[pi]] += 1
    print('OVERLAP_WHERE', dict(lab))
    if not overlap_tris:
        break
    # cut every folded triangle out along its edges and try again
    bpy.ops.object.mode_set(mode='OBJECT')
    folded = {me.loop_triangles[ti].polygon_index for ti in overlap_tris}
    for pi in folded:
        for ek in me.polygons[pi].edge_keys:
            me.edges[edge_lookup[ek]].use_seam = True
print('UV', 'faces', len(me.polygons), 'seams', seams, 'regions', sorted(by_region))


def head_layout():
    """Head set: smart project (as claude_shared/head_texture_split.py), islands scaled by part before packing."""
    bpy.ops.object.mode_set(mode='EDIT')
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:                      # the body set is hidden: no operator below can move its UVs
        f.hide_set(not headf[f.index])
        f.select = bool(headf[f.index])
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(85), island_margin=0.002, area_weight=0.0, scale_to_bounds=False)
    # equal density across the head set before the per-part scale
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
    for pid in {int(part[f.index]) for f in bm.faces if headf[f.index]}:
        faces = [f for f in bm.faces if headf[f.index] and part[f.index] == pid]
        a3 = sum(f.calc_area() for f in faces)
        a2 = sum(abs(sum(l[uv].uv.x * l.link_loop_next[uv].uv.y - l.link_loop_next[uv].uv.x * l[uv].uv.y
                         for l in f.loops)) / 2 for f in faces)
        k = math.sqrt(a3 / max(a2, 1e-12))
        for f in faces:
            for l in f.loops:
                l[uv].uv = l[uv].uv * k
    bmesh.update_edit_mesh(me)
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active
    SCALE = {'Body': 1.8, 'Hair': 1.0, 'Braid': 0.75, 'Headband': 0.6}
    # islands: connected faces in UV space (shared UV corners) within the head set
    import collections
    key = lambda l: (l.vert.index, round(l[uv].uv.x, 6), round(l[uv].uv.y, 6))
    owner = {}
    for f in bm.faces:
        if headf[f.index]:
            for l in f.loops:
                owner.setdefault(key(l), []).append(f.index)
    parent = {}
    def find(a):
        while parent.setdefault(a, a) != a:
            parent[a] = parent[parent[a]]; a = parent[a]
        return a
    for faces in owner.values():
        for b in faces[1:]:
            parent[find(faces[0])] = find(b)
    islands = collections.defaultdict(list)
    for f in bm.faces:
        if headf[f.index]:
            islands[find(f.index)].append(f)
    for faces in islands.values():
        names = [PARTS[part[f.index]] for f in faces]
        k = SCALE.get(max(set(names), key=names.count), 1.0)
        loops = [l for f in faces for l in f.loops]
        c = sum((l[uv].uv for l in loops), Vector((0, 0))) / len(loops)
        for l in loops:
            l[uv].uv = c + (l[uv].uv - c) * k
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.003, shape_method='CONCAVE')
    bm = bmesh.from_edit_mesh(me)
    for f in bm.faces:
        f.hide_set(False)
    bmesh.update_edit_mesh(me)
    bpy.ops.object.mode_set(mode='OBJECT')
    print('HEAD_UV islands', len(islands))


head_layout()
# gate: UV density per triangle against its set's median
me.calc_loop_triangles(); uvl = me.uv_layers.active.data
dens = {0: [], 1: []}
for t in me.loop_triangles:
    p = np.array([tuple(uvl[li].uv) for li in t.loops]); x = np.array([tuple(me.vertices[v].co) for v in t.vertices])
    a2 = abs(np.cross(p[1] - p[0], p[2] - p[0])) / 2; a3 = np.linalg.norm(np.cross(x[1] - x[0], x[2] - x[0])) / 2
    if a3 > 1e-9:
        dens[int(headf[t.polygon_index])].append(a2 / a3)
for k, v in dens.items():
    v = np.array(v); m = np.median(v)
    print('UV_GATE', 'head' if k else 'body', 'tris', len(v), 'below 5 % of median', int((v < 0.05 * m).sum()),
          'below 20 %', int((v < 0.2 * m).sum()))
bpy.ops.wm.save_mainfile()
