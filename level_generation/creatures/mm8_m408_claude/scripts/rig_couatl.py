"""Fit the Couatl's body curve and anatomy-owned wing weights to the measured Meshy parts."""
import json
from pathlib import Path

import bpy
import bmesh
import numpy as np
from mathutils import Vector

P = Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P / 'work/import_v1.blend'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for obj in list(bpy.data.objects):
    if obj != mesh:
        bpy.data.objects.remove(obj, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
mesh.name = mesh.data.name = 'Couatl'
raw = np.array([tuple(v.co) for v in mesh.data.vertices])
parts = json.loads((P / 'work/components.json').read_text())['vertices']
labels = np.zeros(len(raw), dtype=int)
for part, indices in enumerate(parts):
    labels[indices] = part
# Add bend support only to the sparse body/neck junction, preserving the feather and skull topology.
bm = bmesh.new()
bm.from_mesh(mesh.data)
layer = bm.verts.layers.int.new('anatomy_part')
bm.verts.ensure_lookup_table()
for v in bm.verts:
    v[layer] = int(labels[v.index])
# Meshy extended the small crown spike into a neck-length sheet absent from the native head.
crest_faces = [f for f in bm.faces if all(v[layer] == 6 for v in f.verts)]
crest_geom = list(set(crest_faces + [e for f in crest_faces for e in f.edges] + [v for f in crest_faces for v in f.verts]))
cut = bmesh.ops.bisect_plane(bm, geom=crest_geom, dist=1e-6, plane_co=Vector((0,0,0.12)),
                           plane_no=Vector((0,0,1)), clear_inner=True)
cap_edges = [e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
if cap_edges:
    bmesh.ops.holes_fill(bm, edges=cap_edges, sides=0)
for v in bm.verts:
    if v[layer] == 6 and v.co.z > 0.14:
        v.co.z = 0.14 + (v.co.z-0.14)*0.6
edges = [e for e in bm.edges if all(v[layer] == 0 and -0.39 < v.co.y < 0.06 and v.co.z < 0.025 for v in e.verts)]
bmesh.ops.subdivide_edges(bm, edges=edges, cuts=1, smooth=0.3, use_grid_fill=True)
bm.to_mesh(mesh.data)
bm.free()
raw = np.array([tuple(v.co) for v in mesh.data.vertices])
labels = np.array([x.value for x in mesh.data.attributes['anatomy_part'].data])
parts = [np.flatnonzero(labels == part).tolist() for part in range(34)]
main = raw[parts[0]]

# The body turns sideways near the tail; switch slice axes there instead of averaging across the bend.
points = []
for x in np.linspace(-0.43, -0.08, 8):
    section = main[(abs(main[:, 0] - x) < 0.025) & (main[:, 1] > 0.22) & (main[:, 2] < -0.22)]
    assert len(section) >= 3, ('tail slice', x)
    points.append([x, (section[:, 1].min() + section[:, 1].max()) / 2,
                   (section[:, 2].min() + section[:, 2].max()) / 2])
for y in np.linspace(0.27, -0.24, 12):
    section = main[(abs(main[:, 1] - y) < 0.025) & (main[:, 2] < -0.18)]
    assert len(section) >= 3, ('body slice', y)
    points.append([(section[:, 0].min() + section[:, 0].max()) / 2, y,
                   (section[:, 2].min() + section[:, 2].max()) / 2])
for z in np.linspace(-0.22, 0.055, 9):
    section = main[(abs(main[:, 2] - z) < 0.018) & (main[:, 1] < -0.23) & (main[:, 1] > -0.38)]
    assert len(section) >= 3, ('neck slice', z)
    points.append([(section[:, 0].min() + section[:, 0].max()) / 2,
                   (section[:, 1].min() + section[:, 1].max()) / 2, z])
curve = np.array(points)
for _ in range(2):
    curve[1:-1] = 0.5 * curve[1:-1] + 0.25 * (curve[:-2] + curve[2:])
arc = np.r_[0, np.cumsum(np.linalg.norm(np.diff(curve, axis=0), axis=1))]
sample = np.linspace(0, arc[-1], 28)
joints = np.array([np.interp(sample, arc, curve[:, axis]) for axis in range(3)]).T
joints = np.vstack([joints, [0.111, -0.489, 0.078]])
root = int(np.argmin(np.linalg.norm(joints[:-1] - [0.114, -0.235, -0.265], axis=1)))
nseg = len(joints) - 1
lengths = np.linalg.norm(np.diff(joints, axis=0), axis=1)
cumulative = np.r_[0, np.cumsum(lengths)]
best_dist = np.full(len(raw), np.inf)
body_arc = np.zeros(len(raw))
closest = np.zeros_like(raw)
for i, (a, b) in enumerate(zip(joints[:-1], joints[1:])):
    delta = b - a
    t = np.clip((raw - a) @ delta / (delta @ delta), 0, 1)
    point = a + t[:, None] * delta
    distance = np.linalg.norm(raw - point, axis=1)
    take = distance < best_dist
    best_dist[take] = distance[take]
    body_arc[take] = cumulative[i] + t[take] * lengths[i]
    closest[take] = point[take]

# Keep the head and feather geometry; reduce only the measured oversized snake cross-section.
slim = (labels == 0) & (raw[:, 2] < 0.04)
amount = 0.72 + 0.28 * np.clip((raw[:, 2] + 0.025) / 0.065, 0, 1)
raw[slim] = closest[slim] + (raw[slim] - closest[slim]) * amount[slim, None]
offset = np.array([0.111, -0.235, raw[:, 2].min()])
scale = 1 / (raw[:, 2].max() - offset[2])
co = (raw - offset) * scale
joints = (joints - offset) * scale
for v, xyz in zip(mesh.data.vertices, co):
    v.co = xyz
for face in mesh.data.polygons:
    face.use_smooth = True
attribute = mesh.data.attributes['anatomy_part']
for value, part in zip(attribute.data, labels):
    value.value = int(part)

def point(xyz):
    return Vector((np.array(xyz) - offset) * scale)

def name(i):
    if i == nseg - 1:
        return 'Head'
    if i == root:
        return 'Root'
    return f'Tail_{root-i:02}' if i < root else f'Neck_{i-root:02}'

arm = bpy.data.armatures.new('Couatl_Rig')
rig = bpy.data.objects.new('Couatl_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
bones = {}
for i in range(nseg):
    bone = arm.edit_bones.new(name(i))
    a, b = Vector(joints[i]), Vector(joints[i + 1])
    bone.head, bone.tail = (b, a) if i < root else (a, b)
    bone.align_roll(Vector((1, 0, 0)))
    bones[i] = bone
for i in range(nseg):
    if i < root:
        bones[i].parent = bones[i + 1]
    elif i > root:
        bones[i].parent = bones[i - 1]

wing_parent = min(range(root, nseg - 1), key=lambda i: abs(joints[i + 1, 2] - point([0.111, -0.28, 0.0]).z))
extra = {}
for side, sign in [('L', 1), ('R', -1)]:
    chain = [point([0.111 + sign * x, y, z]) for x, y, z in
             [(0.025, -0.28, 0.0), (0.13, -0.267, 0.012), (0.25, -0.238, -0.01),
              (0.365, -0.23, -0.145)]]
    previous = bones[wing_parent]
    for i, label in enumerate(('WingRoot', 'WingMid', 'WingFan')):
        key = f'{label}_{side}'
        bone = arm.edit_bones.new(key)
        bone.head, bone.tail = chain[i], chain[i + 1]
        bone.parent = previous
        bone.align_roll(Vector((0, 0, 1)))
        extra[key] = [list(chain[i]), list(chain[i + 1])]
        previous = bone
crest = arm.edit_bones.new('Crest')
crest.head, crest.tail = point([0.111, -0.315, 0.12]), point([0.111, -0.26, 0.30])
crest.parent = bones[nseg - 1]
crest.align_roll(Vector((1, 0, 0)))
jaw = arm.edit_bones.new('Jaw')
jaw.head, jaw.tail = point([0.111, -0.389, 0.073]), point([0.111, -0.485, 0.055])
jaw.parent = bones[nseg - 1]
jaw.align_roll(Vector((1, 0, 0)))
bpy.ops.object.mode_set(mode='OBJECT')
groups = {bone.name: mesh.vertex_groups.new(name=bone.name) for bone in rig.data.bones}
mid = (cumulative[:-1] + cumulative[1:]) / 2

def blend_arc(s):
    i = int(np.clip(np.searchsorted(mid, s) - 1, 0, nseg - 2))
    t = float(np.clip((s - mid[i]) / (mid[i + 1] - mid[i]), 0, 1))
    return {name(i): 1 - t, name(i + 1): t}

wing_parts = {1, 2, 3, 11, 12, 13, 14, 15, 16, 17, 19, 20, 21, 22, 23, 24, 25, 26, 27, 30, 31}
rigid_parts = {4, 5, 6, 7, 8, 9, 10, 29, 32, 33}
rigid_weights = {}
for part in wing_parts:
    coords = raw[parts[part]]
    top = coords[coords[:, 2] > np.percentile(coords[:, 2], 85)].mean(0)
    side = 'L' if top[0] > 0.111 else 'R'
    x = abs(top[0] - 0.111)
    bone = 'WingRoot' if x < 0.13 else ('WingMid' if x < 0.24 else 'WingFan')
    rigid_weights[part] = {f'{bone}_{side}': 1.0}

for i, xyz in enumerate(raw):
    part = labels[i]
    if part in (4, 5, 7, 8):
        weights = {'Crest': 1.0}
    elif part in rigid_parts:
        weights = {'Head': 1.0}
    elif part in wing_parts:
        if part in (1, 2, 3):
            x = abs(xyz[0] - 0.111)
            side = 'L' if xyz[0] > 0.111 else 'R'
            t = float(np.clip((x - 0.11) / 0.09, 0, 1))
            weights = {f'WingRoot_{side}': 1-t, f'WingMid_{side}': t}
        else:
            weights = rigid_weights[part]
    elif part in (18, 28):
        weights = {name(0): 1.0}
    else:
        weights = blend_arc(body_arc[i])
        if xyz[1] < -0.38 and xyz[2] > 0.025:
            mouth_height = 0.074 - 0.05 * (xyz[1] + 0.43)
            lower = float(np.clip((mouth_height - xyz[2]) / 0.009, 0, 1))
            lower *= float(np.clip((-0.385 - xyz[1]) / 0.025, 0, 1))
            weights = {'Head': 1-lower, 'Jaw': lower}
    assert abs(sum(weights.values()) - 1) < 1e-6
    for group, weight in weights.items():
        if weight > 1e-6:
            groups[group].add([i], weight, 'REPLACE')
# Ground radii follow the actual nearest core samples, excluding wings/head ornaments.
radius = []
for i, joint in enumerate(joints):
    near = co[(labels == 0) & (abs(body_arc - cumulative[min(i, nseg)]) < 0.04)]
    radius.append(float(max(0.008, joint[2] - near[:, 2].min())) if len(near) else 0.02)
# Open the closed Meshy mouth at its measured lip line; retain a solid palate and lower jaw.
bm = bmesh.new()
bm.from_mesh(mesh.data)
part_layer = bm.verts.layers.int['anatomy_part']
face_layer = bm.faces.layers.int.new('mouth_interior')
def original(v):
    return np.array(v.co) / scale + offset
head_faces = [f for f in bm.faces if any(original(v)[1] < -0.375 and original(v)[2] > 0.02 for v in f.verts)]
geom = list(set(head_faces + [e for f in head_faces for e in f.edges] + [v for f in head_faces for v in f.verts]))
bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=point([0.111,-0.43,0.074]),
                      plane_no=Vector((0,0.05,1)).normalized())
head_faces = [f for f in bm.faces if any(original(v)[1] < -0.375 and original(v)[2] > 0.02 for v in f.verts)]
geom = list(set(head_faces + [e for f in head_faces for e in f.edges] + [v for f in head_faces for v in f.verts]))
bmesh.ops.bisect_plane(bm, geom=geom, dist=1e-6, plane_co=point([0.111,-0.385,0.074]),
                      plane_no=Vector((0,1,0)))
lower = []
for f in bm.faces:
    c = original(f.verts[0]) * 0
    for v in f.verts:
        c += original(v) / len(f.verts)
    if all(v[part_layer] == 0 for v in f.verts) and c[1] < -0.385 and c[2] > 0.025:
        if c[2] < 0.074 - 0.05*(c[1]+0.43) - 1e-6:
            lower.append(f)
assert len(lower)>10, ('jaw faces',len(lower))
lower_set = set(lower)
boundary = {e for f in lower for e in f.edges if any(n not in lower_set for n in e.link_faces)}
old_boundary = {e for e in bm.edges if e.is_boundary}
bmesh.ops.split_edges(bm, edges=list(boundary))
for f in lower:
    for v in f.verts:
        v[part_layer] = 34
new_boundary = [e for e in bm.edges if e.is_boundary and e not in old_boundary]
filled = bmesh.ops.holes_fill(bm, edges=new_boundary, sides=0)['faces']
# The new mouth surfaces are retained for a dark interior material during texture composition.
for f in filled:
    f[face_layer] = 1
bmesh.ops.triangulate(bm, faces=filled)
deform = bm.verts.layers.deform.verify()
for v in bm.verts:
    if v[part_layer] == 34:
        v[deform].clear()
        v[deform][groups['Jaw'].index] = 1.0
bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
bm.to_mesh(mesh.data)
bm.free()
co = np.array([tuple(v.co) for v in mesh.data.vertices])
labels = np.array([x.value for x in mesh.data.attributes['anatomy_part'].data])
print('MOUTH',len(lower),'lower jaw faces;',len(filled),'interior faces')
mesh.parent = rig
modifier = mesh.modifiers.new('Armature', 'ARMATURE')
modifier.object = rig
assert all(v.groups and len(v.groups) <= 4 for v in mesh.data.vertices), [(v.index, len(v.groups)) for v in mesh.data.vertices if not v.groups or len(v.groups)>4]
for v in mesh.data.vertices:
    assert abs(sum(g.weight for g in v.groups) - 1) < 1e-5
rig.show_in_front = True
for bone in rig.pose.bones:
    bone.rotation_mode = 'QUATERNION'

record = dict(joints=joints.tolist(), radius=radius, root=root, names=[name(i) for i in range(nseg)],
              extra=extra, source_offset=offset.tolist(), source_scale=scale, wing_parent=name(wing_parent),
              vertices=len(co), triangles=len(mesh.data.loop_triangles), max_influences=max(len(v.groups) for v in mesh.data.vertices))
(P / 'work/rig.json').write_text(json.dumps(record, indent=2) + '\n')
np.savez(P / 'work/rig_geometry.npz', coordinates=co, labels=labels)
bpy.ops.wm.save_as_mainfile(filepath=str(P / 'work/rig_v3.blend'))
print('RIG', len(rig.data.bones), 'bones;', len(co), 'weighted vertices; root', root)
