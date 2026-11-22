"""Mole rig: joints read from the clean mesh (dump_mesh.py numbers: arm leaves the chest at y -0.3, wrist about
(0.44, -0.41, 0.20), knuckles (0.50, -0.49, 0.17), claw tips (0.48, -0.58, 0.06); hind toe claws at x 0.32-0.42,
y 0.23-0.33), Blender automatic (heat) weights on the trunk and limbs, then fixes:
- each hand (everything beyond the wrist plane on |x| > 0.24 below z 0.30) is wholly on Hand/Claws (Claws ramps in
  over the knuckles, so all five claws curl together and never take a head or forearm weight);
- eyes rigid on Head, hind toe claws rigid on HindFoot, the tail on Tail1..4 by arc position.
Forward -Y, up +Z, character left +X. Reads work/clean_v2.blend, writes work/rig_v1.blend."""
import bpy, os, math
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
mesh = bpy.data.objects['Mole']
V = Vector
TAIL = [V((0, 0.46, 0.24)), V((0, 0.62, 0.245)), V((0, 0.78, 0.31)), V((0, 0.87, 0.46)), V((0, 0.875, 0.635))]
ARM = [V((0.18, -0.30, 0.31)), V((0.37, -0.30, 0.25)), V((0.44, -0.41, 0.20)), V((0.50, -0.49, 0.17)),
       V((0.48, -0.60, 0.07))]
HIND = [V((0.18, 0.32, 0.25)), V((0.33, 0.31, 0.12)), V((0.37, 0.25, 0.055))]
arm = bpy.data.armatures.new('Mole_Rig'); rig = bpy.data.objects.new('Mole_Rig', arm)
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


bone('Body', V((0, 0.40, 0.30)), V((0, 0.10, 0.34)))
bone('Spine', V((0, 0.10, 0.34)), V((0, -0.20, 0.36)), 'Body', True)
bone('Chest', V((0, -0.20, 0.36)), V((0, -0.40, 0.36)), 'Spine', True)
bone('Head', V((0, -0.40, 0.36)), V((0, -0.56, 0.33)), 'Chest', True)
bone('Snout', V((0, -0.56, 0.29)), V((0, -0.73, 0.22)), 'Head')
for i in range(4):
    bone(f'Tail{i + 1}', TAIL[i], TAIL[i + 1], 'Body' if i == 0 else f'Tail{i}', i > 0, roll=V((1, 0, 0)))
for s, sg in (('L', 1), ('R', -1)):
    a = [mx(p, sg) for p in ARM]; h = [mx(p, sg) for p in HIND]
    bone(f'UpperArm_{s}', a[0], a[1], 'Chest')
    bone(f'ForeArm_{s}', a[1], a[2], f'UpperArm_{s}', True)
    bone(f'Hand_{s}', a[2], a[3], f'ForeArm_{s}', True)
    bone(f'Claws_{s}', a[3], a[4], f'Hand_{s}', True)
    bone(f'Thigh_{s}', h[0], h[1], 'Body')
    bone(f'HindFoot_{s}', h[1], h[2], f'Thigh_{s}', True)
bpy.ops.object.mode_set(mode='OBJECT')

NOHEAT = [f'Tail{i + 1}' for i in range(4)] + ['Claws_L', 'Claws_R']
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


def set_weights(i, wd):
    v = me.vertices[int(i)]
    for g in list(v.groups):
        mesh.vertex_groups[g.group].remove([int(i)])
    for n, w in wd.items():
        if w > 1e-4:
            groups[n].add([int(i)], float(w), 'REPLACE')


def ss(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)


# eyes, hind claws
for i in np.where(part == 1)[0]:
    set_weights(i, {'Head': 1.0})
for i in np.where(part == 2)[0]:
    set_weights(i, {'HindFoot_L' if co[i, 0] > 0 else 'HindFoot_R': 1.0})
# tail by arc position along the bone chain
P = np.array([p[:] for p in TAIL])
for i in np.where(part == 3)[0]:
    best = None
    for k in range(4):
        a, b = P[k], P[k + 1]; d = b - a
        t = np.clip(np.dot(co[i] - a, d) / np.dot(d, d), 0, 1)
        dist = np.linalg.norm(a + t * d - co[i])
        if best is None or dist < best[0]:
            best = (dist, k, t)
    _, k, t = best
    w = {f'Tail{k + 1}': 1.0}
    if t < 0.3 and k > 0:
        u = 0.5 + t / 0.6; w = {f'Tail{k + 1}': u, f'Tail{k}': 1 - u}
    elif t > 0.7 and k < 3:
        u = 0.5 + (1 - t) / 0.6; w = {f'Tail{k + 1}': u, f'Tail{k + 2}': 1 - u}
    set_weights(i, w)
# hands: beyond the wrist plane -> Hand/Claws only; blended into the heat weights over 4 cm at the wrist
nhand = 0
for s, sg in (('L', 1), ('R', -1)):
    a = [np.array(mx(p, sg)[:]) for p in ARM]
    fdir = (a[2] - a[1]) / np.linalg.norm(a[2] - a[1])
    hdir = (a[4] - a[2]) / np.linalg.norm(a[4] - a[2])
    for i in np.where(part == 0)[0]:
        c = co[i]
        if sg * c[0] < 0.24 or c[2] > 0.30:
            continue
        wr = np.dot(c - a[2], fdir)                    # past the wrist along the forearm
        if wr < -0.02:
            continue
        blend = float(ss((wr + 0.02) / 0.04))
        kn = np.dot(c - a[3], hdir)                     # past the knuckles toward the claw tips
        cw = float(ss((kn + 0.01) / 0.05))
        rigid = {f'Hand_{s}': 1 - cw, f'Claws_{s}': cw}
        old = {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[int(i)].groups}
        tot = sum(old.values()) or 1.0
        new = {n: w / tot * (1 - blend) for n, w in old.items()}
        for n, w in rigid.items():
            new[n] = new.get(n, 0) + w * blend
        set_weights(i, new)
        nhand += 1
empty = [v.index for v in me.vertices if not any(g.weight > 1e-4 for g in v.groups)]
print('RIGGED bones', len(arm.bones), 'unweighted', len(empty), 'hand verts', nhand)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
