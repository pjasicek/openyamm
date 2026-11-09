"""Glassback rig: six-legged skeleton from the leg axes measured on the mesh (leg_axes.py -> work/leg_axes.json, grid
views), Blender automatic (heat) weights, the eyeballs bound rigidly to Head. work/body.blend -> work/rig_v1.blend.
Forward -Y, up +Z, creature left +X.

Bones: Spine1 (root, hips -> mid), Spine2 (mid -> shoulders), Spine3 (shoulders -> neck), Neck1, Head, Tail1..3;
per leg <L><side> (F front on Spine3, M middle on Spine2, H hind on Spine1): Upper_<L><s>, Lower_<L><s>, Foot_<L><s>."""
import bpy, os, sys, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C

bpy.ops.wm.open_mainfile(filepath=C.path('work/body.blend'))
mesh = bpy.data.objects[C.MESH]
axes = json.load(open(C.path('work/leg_axes.json')))


def at(leg, z):
    rows = np.array(axes[leg])
    return Vector((float(np.interp(z, rows[:, 0], rows[:, 1])), float(np.interp(z, rows[:, 0], rows[:, 2])), z))


V = Vector
CHAINS = {
    'Spine': (None, [V((0, 0.60, 0.76)), V((0, 0.10, 0.80)), V((0, -0.40, 0.82)), V((0, -0.90, 0.80))]),
    'Neck': ('Spine3', [V((0, -0.90, 0.80)), V((0, -1.10, 0.76))]),
    'Head': ('Neck1', [V((0, -1.10, 0.76)), V((0, -1.45, 0.62))]),
    'Tail': ('Spine1', [V((0, 0.60, 0.76)), V((0, 0.95, 0.69)), V((0, 1.20, 0.64)), V((0, 1.43, 0.60))]),
}
NAMES = {'Spine': ['Spine1', 'Spine2', 'Spine3'], 'Neck': ['Neck1'], 'Head': ['Head'],
         'Tail': ['Tail1', 'Tail2', 'Tail3']}
PARENT = {'F': 'Spine3', 'M': 'Spine2', 'H': 'Spine1'}
LEGS = {}
for leg in ('FL', 'FR', 'ML', 'MR', 'HL', 'HR'):
    kind, side = leg[0], leg[1]
    top = at(leg, 0.425)
    knee = at(leg, 0.30)
    ankle = at(leg, 0.12)
    # upper joint inside the body, continuing the leg axis above the belly toward the midline
    d = (top - knee).normalized()
    hip = top + d * 0.17
    hip.x *= 0.8
    hip.z = 0.72                    # the leg's pivot high in the body: room to swing (rest hip-ankle 93 % of reach)
    # a slight rest bend gives the IK its direction: elbows of the front and middle legs back, hind knees forward
    knee = knee + V((0, 0.035 if kind in 'FM' else -0.035, 0))
    toe = V((ankle.x * 1.04, ankle.y - 0.16, 0.03))
    LEGS[leg] = (hip, knee, ankle, toe)
    CHAINS['Leg' + leg] = (PARENT[kind], [hip, knee, ankle, toe])
    NAMES['Leg' + leg] = [f'Upper_{leg}', f'Lower_{leg}', f'Foot_{leg}']
    print('LEG', leg, [tuple(round(c, 3) for c in p) for p in (hip, knee, ankle, toe)])

arm = bpy.data.armatures.new(C.RIG)
rig = bpy.data.objects.new(C.RIG, arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones
for key in ['Spine', 'Neck', 'Head', 'Tail'] + ['Leg' + l for l in ('FL', 'FR', 'ML', 'MR', 'HL', 'HR')]:
    parent, pts = CHAINS[key]
    prev = eb[parent] if parent else None
    for i, name in enumerate(NAMES[key]):
        b = eb.new(name)
        b.head = pts[i]
        b.tail = pts[i + 1]
        b.align_roll(V((0, 0, 1)) if not key.startswith('Leg') else V((0, -1, 0)))
        b.parent = prev
        b.use_connect = prev is not None and i > 0
        prev = b
bpy.ops.object.mode_set(mode='OBJECT')
for o in bpy.data.objects:
    o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')

# eyeballs and any other loose piece: rigid on the dominant bone of the nearest main-body vertex
import bmesh
bm = bmesh.new(); bm.from_mesh(mesh.data); bm.verts.ensure_lookup_table()
seen = set(); islands = []
for v in bm.verts:
    if v.index in seen:
        continue
    stack = [v]; isl = []; seen.add(v.index)
    while stack:
        a = stack.pop(); isl.append(a.index)
        for e in a.link_edges:
            b = e.other_vert(a)
            if b.index not in seen:
                seen.add(b.index); stack.append(b)
    islands.append(isl)
islands.sort(key=len, reverse=True)
main = islands[0]
co = np.array([tuple(v.co) for v in mesh.data.vertices])
from mathutils import kdtree
tree = kdtree.KDTree(len(main))
for k, i in enumerate(main):
    tree.insert(co[i], k)
tree.balance()
groups = {g.index: g.name for g in mesh.vertex_groups}
for isl in islands[1:]:
    centre = co[isl].mean(0)
    _, j, _ = tree.find(centre)
    src = mesh.data.vertices[main[j]]
    w = {groups[g.group]: g.weight for g in src.groups}
    for g in mesh.vertex_groups:
        g.remove(isl)
    for name, value in w.items():
        mesh.vertex_groups[name].add(isl, value, 'REPLACE')
    print('RIGID piece', len(isl), 'verts ->', max(w, key=w.get))
empty = [v.index for v in mesh.data.vertices if not v.groups]
print('RIGGED bones', len(arm.bones), 'unweighted', len(empty))
bpy.ops.wm.save_as_mainfile(filepath=C.path('work/rig_v1.blend'))
