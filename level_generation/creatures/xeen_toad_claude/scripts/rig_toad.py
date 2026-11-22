"""Giant Toad rig: a skeleton on joints read from mesh slices (scripts/slices.py; numbers in this file), Blender
automatic (heat) weights, then fixes: eye domes and the brow gland piece rigid on Head; a Throat bone for the throat
pulse with a smooth geometric weight under the jaw; a Tongue chain (its own mesh, built here, rigid per segment) hidden
inside the mouth at rest by animation (Tongue1 scale). Forward -Y, up +Z, character left +X.
Reads work/clean_v1.blend, writes work/rig_v1.blend."""
import bpy, os, sys, math, bmesh
import numpy as np
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
mesh = bpy.data.objects['Toad']
V = Vector
J = {
    'Body': (V((0, 0.55, 0.30)), V((0, 0.05, 0.38))),
    'Chest': (V((0, 0.05, 0.38)), V((0, -0.42, 0.50))),
    'Head': (V((0, -0.42, 0.50)), V((0, -0.95, 0.62))),
    'Throat': (V((0, -0.50, 0.40)), V((0, -0.82, 0.44))),
}
LEGS = {
    'L': {'front': [V((0.24, -0.33, 0.44)), V((0.50, -0.14, 0.27)), V((0.38, -0.55, 0.08)), V((0.25, -0.90, 0.04))],
          'hind': [V((0.18, 0.62, 0.30)), V((0.66, 0.02, 0.29)), V((0.40, 0.72, 0.10)), V((0.72, 0.0, 0.05)),
                   V((0.80, -0.28, 0.03))]},
    'R': {'front': [V((-0.26, -0.33, 0.44)), V((-0.50, -0.14, 0.26)), V((-0.44, -0.55, 0.07)), V((-0.46, -0.82, 0.04))],
          'hind': [V((-0.18, 0.62, 0.30)), V((-0.64, 0.02, 0.28)), V((-0.40, 0.72, 0.10)), V((-0.75, 0.0, 0.05)),
                   V((-0.82, -0.25, 0.03))]},
}
TONGUE = [V((0, -0.72, 0.58)), V((0, -0.92, 0.585)), V((0, -1.12, 0.59)), V((0, -1.32, 0.595)), V((0, -1.50, 0.60))]

arm = bpy.data.armatures.new('Toad_Rig'); rig = bpy.data.objects.new('Toad_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, h, t, parent=None, connect=False, roll=V((0, 0, 1))):
    b = eb.new(name); b.head = h; b.tail = t; b.align_roll(roll)
    if parent: b.parent = eb[parent]; b.use_connect = connect
    return b


bone('Body', *J['Body'])
bone('Chest', *J['Chest'], parent='Body', connect=True)
bone('Head', *J['Head'], parent='Chest', connect=True)
bone('Throat', *J['Throat'], parent='Head')
for s, d in LEGS.items():
    f = d['front']; h = d['hind']
    bone(f'UpperArm_{s}', f[0], f[1], 'Chest', roll=V((0, -1, 0)))
    bone(f'ForeArm_{s}', f[1], f[2], f'UpperArm_{s}', True, roll=V((0, -1, 0)))
    bone(f'Hand_{s}', f[2], f[3], f'ForeArm_{s}', True)
    bone(f'Thigh_{s}', h[0], h[1], 'Body', roll=V((0, 0, 1)))
    bone(f'Shin_{s}', h[1], h[2], f'Thigh_{s}', True, roll=V((0, 0, 1)))
    bone(f'Foot_{s}', h[2], h[3], f'Shin_{s}', True)
    bone(f'Toes_{s}', h[3], h[4], f'Foot_{s}', True)
for i in range(4):
    bone(f'Tongue{i + 1}', TONGUE[i], TONGUE[i + 1], 'Head' if i == 0 else f'Tongue{i}', i > 0)
bpy.ops.object.mode_set(mode='OBJECT')

# tongue bones must not take part in the body's heat weights
for i in range(4):
    arm.bones[f'Tongue{i + 1}'].use_deform = False
for o in bpy.data.objects: o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for i in range(4):
    arm.bones[f'Tongue{i + 1}'].use_deform = True

# ---- weight fixes
d = np.load(os.path.join(HERE, 'work', 'pieces.npz')); lab = d['label']
co = np.array([v.co[:] for v in mesh.data.vertices])
assert len(co) == len(lab)
groups = {g.name: g for g in mesh.vertex_groups}


def set_rigid(indices, name):
    for g in mesh.vertex_groups:
        g.remove(list(map(int, indices)))
    groups[name].add(list(map(int, indices)), 1.0, 'REPLACE')


set_rigid(np.where(np.isin(lab, (5, 6, 9)))[0], 'Head')        # eye domes, brow gland strip
# throat: smooth ellipsoid falloff under the jaw, blended into whatever is there
c = np.array([0.0, -0.66, 0.40]); r = np.array([0.30, 0.26, 0.13])
q = (((co - c) / r) ** 2).sum(1)
w = np.clip(1.0 - q, 0, 1) ** 1.5 * (lab == 0) * (co[:, 2] < 0.50)
idx = np.where(w > 0.01)[0]
for i in idx:
    v = mesh.data.vertices[int(i)]
    for ge in v.groups:
        ge.weight *= (1 - w[i])
    groups['Throat'].add([int(i)], float(w[i]), 'REPLACE')

# ---- tongue mesh: a tapered tube with a bulb tip, its own object joined later at export
bm = bmesh.new()
segs, rings = 10, 24
L = (TONGUE[-1] - TONGUE[0]).length
verts = []
for k in range(rings + 1):
    t = k / rings
    rad = 0.10 * (1 - 0.2 * t) + (0.08 * math.sin(math.pi * min(1, (t - 0.75) / 0.25)) if t > 0.75 else 0)
    if k == rings: rad = 0.0
    y = TONGUE[0].y + (TONGUE[-1].y - TONGUE[0].y) * t
    z = TONGUE[0].z + (TONGUE[-1].z - TONGUE[0].z) * t
    ring = []
    for j in range(segs):
        a = 2 * math.pi * j / segs
        ring.append(bm.verts.new((rad * math.cos(a) * 1.25, y, z + rad * math.sin(a) * 0.7)))
    verts.append(ring)
for k in range(rings):
    for j in range(segs):
        a, b = verts[k][j], verts[k][(j + 1) % segs]; c2, d2 = verts[k + 1][(j + 1) % segs], verts[k + 1][j]
        bm.faces.new((a, d2, c2, b))
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6)
bm.faces.new(verts[0][::-1]) if len(set(verts[0])) == segs else None
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
me = bpy.data.meshes.new('Tongue'); bm.to_mesh(me)
tongue = bpy.data.objects.new('Tongue', me); bpy.context.scene.collection.objects.link(tongue)
for p in me.polygons: p.use_smooth = True
tongue.parent = rig
mod = tongue.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
tg = [tongue.vertex_groups.new(name=f'Tongue{i + 1}') for i in range(4)]
for v in me.vertices:
    t = (v.co.y - TONGUE[0].y) / (TONGUE[-1].y - TONGUE[0].y)
    f = min(3.999, max(0.0, t * 4)); i = int(f); u = f - i
    tg[i].add([v.index], 1 - u if i < 3 else 1.0, 'REPLACE')
    if i < 3 and u > 0: tg[i + 1].add([v.index], u, 'REPLACE')

empty = [v.index for v in mesh.data.vertices if not any(g.weight > 1e-4 for g in v.groups)]
print('RIGGED bones', len(arm.bones), 'unweighted', len(empty), 'throat verts', len(idx), 'tongue verts', len(me.vertices))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
