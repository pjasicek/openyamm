"""Texture step: UV atlas for the Smart-Topology-based Peasant (final_v2.blend), rest pose.

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
groups = {g.index: g.name for g in mesh.vertex_groups}


def region_of_vertex(v):
    best, w = '', 0.0
    for g in v.groups:
        if g.weight > w:
            best, w = groups[g.group], g.weight
    n = best.replace('mixamorig:', '').replace('ForeArmTwist1', 'ForeArm').replace('ForeArmTwist2', 'ForeArm')
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
    for side in ('Left', 'Right'):
        if n.startswith(side) and n[len(side):] in ('UpLeg', 'Leg'):
            return 'Leg' + side
        if n.startswith(side) and n[len(side):] in ('Foot', 'ToeBase'):
            return 'Foot' + side
    return 'Torso'


vregion = [region_of_vertex(v) for v in me.vertices]
bones = {b.name.replace('mixamorig:', ''): b for b in rig.data.bones}


def axis_frame(region):
    """Axis origin/direction and the 'hidden side' reference direction for tube seams."""
    if region in ('Torso', 'Head', 'Hair', 'Skirt', 'Tunic'):
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
        if region == 'Foot' + side:
            b = bones[side + 'Foot']
            return b.head_local, Vector((0, -1, 0)), Vector((0, 0, -1))          # seam along the sole
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
    p = PARTS[part[f.index]]
    if p == 'Legs':
        return 'LegLeft' if f.calc_center_median().x > 0 else 'LegRight'
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
    small = {P[n] for n in ('EyeLeft', 'EyeRight', 'Belt', 'Buckle', 'Braid', 'Headband', 'Knife', 'Spikes', 'Teeth', 'Hoops', 'Sword', 'Armor', 'Leather') if n in P}
    for f in bm.faces:
        f.select = part[f.index] not in small
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.unwrap(method='ANGLE_BASED', margin=0.0)
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select = part[f.index] in small
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.smart_project(angle_limit=math.radians(70), island_margin=0.0, scale_to_bounds=False)

    # 4. densities: equalise per region, then bias
    bm = bmesh.from_edit_mesh(me); bm.faces.ensure_lookup_table(); uv = bm.loops.layers.uv.active


    def uv_area(f):
        pts = [l[uv].uv for l in f.loops]
        return abs(sum(pts[i].x * pts[(i + 1) % len(pts)].y - pts[(i + 1) % len(pts)].x * pts[i].y
                       for i in range(len(pts)))) / 2


    BIAS = {'Head': 2.4, 'Spikes': 0.5, 'Hoops': 0.6, 'Sword': 0.7, 'Armor': 0.9, 'LeftHand': 1.4, 'RightHand': 1.4,
            **{f'{sd}Hand{f}{k}': 1.4 for sd in ('Left', 'Right') for f in ('Thumb', 'Index', 'Middle', 'Ring', 'Pinky') for k in (1, 2, 3)}, 'Skirt': 0.7, 'LegLeft': 1.0, 'LegRight': 1.0, 'Tunic': 0.85,
            'Hair': 1.1, 'Knife': 0.6}
    by_region = {}
    for f in bm.faces:
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
        f.select = True
    bmesh.update_edit_mesh(me)
    bpy.ops.uv.select_all(action='SELECT')
    bpy.ops.uv.pack_islands(rotate=True, margin=0.003, shape_method='CONCAVE')
    bpy.ops.object.mode_set(mode='OBJECT')
    seams = sum(1 for e in me.edges if e.use_seam)
    # Overlap gate: rasterise triangle ids at 1024^2; any texel claimed by two non-adjacent triangles is a fold.
    me.calc_loop_triangles(); uvl = me.uv_layers.active.data; R = 1024
    owner = np.full((R, R), -1, dtype=np.int64); overlap_tris = set()
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
bpy.ops.wm.save_mainfile()
