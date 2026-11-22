"""Sabertooth rig. Joints read from the clean mesh (work/mesh_v2.npz slices; review/zlegs_side.png, zhead_side.png
grid views): forward -Y, up +Z, character left +X.
  Body (root at the hips) > Spine > Chest > Neck > Head > Jaw; Tail1..8 (from Body) on the procedural tail's
  centreline; per side Scapula > UpperArm > ForeArm > FrontPaw (from Chest; the scapula rolls the shoulder in the
  walk, as big cats' shoulder blades do) and Thigh > Shin > Hock > HindPaw (from Body; digitigrade hind leg).
Blender heat weights on the body (Jaw and tail bones excluded), then:
  - jaw: body vertices below the mouth line (corner y -0.987 z 0.967, front y -1.10 z 0.942) and ahead of the hinge
    (y -0.93) move to Jaw, blended over 1.2 cm across the line and 4 cm at the hinge; the mouth cavity splits with them;
  - eyes and fangs rigid on Head; claws rigid on the nearest paw bone; the tail by arc position on Tail1..8.
Reads work/clean_v2.blend, writes work/rig_v1.blend."""
import bpy, os
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
mesh = bpy.data.objects['Saber']
V = Vector
TAIL = [V(p) for p in ((0, 0.40, 0.90), (0, 0.52, 0.91), (0, 0.66, 0.84), (0, 0.78, 0.68), (0, 0.86, 0.50),
                       (0, 0.93, 0.33), (0, 1.01, 0.22), (0, 1.11, 0.20), (0, 1.21, 0.27))]
FRONT = [V((0.10, -0.50, 0.95)), V((0.15, -0.70, 0.72)), V((0.15, -0.50, 0.52)), V((0.15, -0.61, 0.10)),
         V((0.16, -0.75, 0.03))]
HIND = [V((0.17, 0.30, 0.80)), V((0.21, 0.16, 0.52)), V((0.25, 0.41, 0.37)), V((0.27, 0.31, 0.08)),
        V((0.28, 0.19, 0.03))]
arm = bpy.data.armatures.new('Saber_Rig'); rig = bpy.data.objects.new('Saber_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, h, t, parent=None, connect=False, roll=V((0, 0, 1))):
    b = eb.new(name); b.head = h; b.tail = t; b.align_roll(roll)
    if parent: b.parent = eb[parent]; b.use_connect = connect
    return b


def mx(v, s):
    return V((v.x * s, v.y, v.z))


bone('Body', V((0, 0.30, 0.84)), V((0, 0.05, 0.86)))
bone('Spine', V((0, 0.05, 0.86)), V((0, -0.30, 0.86)), 'Body', True)
bone('Chest', V((0, -0.30, 0.86)), V((0, -0.62, 0.90)), 'Spine', True)
bone('Neck', V((0, -0.62, 0.90)), V((0, -0.83, 1.04)), 'Chest', True)
bone('Head', V((0, -0.83, 1.04)), V((0, -1.13, 1.02)), 'Neck', True)
bone('Jaw', V((0, -0.93, 0.975)), V((0, -1.09, 0.925)), 'Head')
for i in range(8):
    bone(f'Tail{i + 1}', TAIL[i], TAIL[i + 1], 'Body' if i == 0 else f'Tail{i}', i > 0, roll=V((1, 0, 0)))
for s, sg in (('L', 1), ('R', -1)):
    f = [mx(p, sg) for p in FRONT]; h = [mx(p, sg) for p in HIND]
    bone(f'Scapula_{s}', f[0], f[1], 'Chest')
    bone(f'UpperArm_{s}', f[1], f[2], f'Scapula_{s}', True)
    bone(f'ForeArm_{s}', f[2], f[3], f'UpperArm_{s}', True)
    bone(f'FrontPaw_{s}', f[3], f[4], f'ForeArm_{s}', True)
    bone(f'Thigh_{s}', h[0], h[1], 'Body')
    bone(f'Shin_{s}', h[1], h[2], f'Thigh_{s}', True)
    bone(f'Hock_{s}', h[2], h[3], f'Shin_{s}', True)
    bone(f'HindPaw_{s}', h[3], h[4], f'Hock_{s}', True)
bpy.ops.object.mode_set(mode='OBJECT')

NOHEAT = [f'Tail{i + 1}' for i in range(8)] + ['Jaw']
for n in NOHEAT:
    arm.bones[n].use_deform = False
for o in bpy.data.objects: o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for n in NOHEAT:
    arm.bones[n].use_deform = True
groups = {g.name: g for g in mesh.vertex_groups}
for n in NOHEAT:
    if n not in groups:
        groups[n] = mesh.vertex_groups.new(name=n)
me = mesh.data
co = np.array([v.co[:] for v in me.vertices])
part = np.zeros(len(co), int)
for p in me.polygons:
    for v in p.vertices: part[v] = me.attributes['part'].data[p.index].value


def get_w(i):
    return {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[int(i)].groups if g.weight > 1e-5}


def set_weights(i, wd):
    v = me.vertices[int(i)]
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([int(i)])
    tot = sum(wd.values()) or 1.0
    for n, w in wd.items():
        if w / tot > 1e-4:
            groups[n].add([int(i)], float(w / tot), 'REPLACE')


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


for i in np.where((part == 1) | (part == 2))[0]:
    set_weights(i, {'Head': 1.0})
for i in np.where(part == 3)[0]:
    c = co[i]; s = 'L' if c[0] > 0 else 'R'
    set_weights(i, {f'FrontPaw_{s}' if c[1] < -0.2 else f'HindPaw_{s}': 1.0})
P = np.array([p[:] for p in TAIL])
for i in np.where(part == 4)[0]:
    best = None
    for k in range(8):
        a, b = P[k], P[k + 1]; d = b - a
        t = np.clip(np.dot(co[i] - a, d) / np.dot(d, d), 0, 1)
        dist = np.linalg.norm(a + t * d - co[i])
        if best is None or dist < best[0]:
            best = (dist, k, t)
    _, k, t = best
    w = {f'Tail{k + 1}': 1.0}
    if t < 0.3 and k > 0:
        u = 0.5 + t / 0.6; w = {f'Tail{k + 1}': u, f'Tail{k}': 1 - u}
    elif t > 0.7 and k < 7:
        u = 0.5 + (1 - t) / 0.6; w = {f'Tail{k + 1}': u, f'Tail{k + 2}': 1 - u}
    set_weights(i, w)
# the head itself: everything ahead of the skull base belongs to Head (heat weights spread Chest/Neck into the face)
njaw = 0
for i in np.where(part == 0)[0]:
    c = co[i]
    if c[1] > -0.80 or c[2] < 0.80:
        continue
    head_k = float(ss((-0.80 - c[1]) / 0.10))
    old = get_w(i); tot = sum(old.values()) or 1.0
    w = {n: x / tot * (1 - head_k) for n, x in old.items()}
    w['Head'] = w.get('Head', 0.0) + head_k
    zm = 0.967 + 0.221 * (c[1] + 0.987)                 # mouth line
    jaw_k = float(ss((zm - c[2]) / 0.012 + 0.5)) * float(ss((-0.93 - c[1]) / 0.04 + 0.5)) * float(ss((c[2] - 0.84) / 0.03))
    if jaw_k > 0:
        hw = w.get('Head', 0.0)
        w['Head'] = hw * (1 - jaw_k); w['Jaw'] = hw * jaw_k
        njaw += 1
    set_weights(i, w)
empty = [v.index for v in me.vertices if not any(g.weight > 1e-4 for g in v.groups)]
print('RIGGED bones', len(arm.bones), 'unweighted', len(empty), 'jaw verts', njaw)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
