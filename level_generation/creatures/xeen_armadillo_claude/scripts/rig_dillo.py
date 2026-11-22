"""Armadillo rig. Forward -Y, up +Z, character left +X. Joints read from the clean mesh (dump_raw.py slices of
clean_v2 and the zoom views): front feet planted at (+-0.23, -0.89) with the claw tips at y -1.0, hind feet at
(+-0.29, -0.20) with the toes at y -0.28 and the heel at -0.06; the tail centreline at z 0.16 (y 0.15) falling to
0.135 at the ball (centre and radius from work/parts.json).

Bones: `Body` (root at the hips) > `Spine` > `Chest` > `Neck` > `Head` > `Tongue`; `Tail1..8` from Body; `TailBall`
> `Spikes` at the end of the tail; per side `UpperArm` > `ForeArm` > `Hand` (from Chest) and `Thigh` > `Shin` >
`HindFoot` (from Body). Weights: Blender heat weights on the trunk, head and limbs, then
- each foot below the wrist/ankle (within 0.14 m of the foot centre, z < 0.05, blended to the heat weights by z 0.09)
  wholly on Hand / HindFoot, so the claws move as one;
- the tail by arc position along Tail1..8 (linear blend between neighbouring bones), its ball rigid on TailBall;
- spikes (part 2) rigid on Spikes, the tongue (part 3) rigid on Tongue, the face caps (part 1) rigid on Head.
Reads work/clean_v2.blend, writes work/rig_v1.blend."""
import bpy, os, math, json
import numpy as np
from mathutils import Vector
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v2.blend'))
mesh = bpy.data.objects['Dillo']
parts = json.load(open(os.path.join(HERE, 'work', 'parts.json')))
V = Vector
BC = V(parts['ball_centre']); BR = parts['ball_radius']
ROOT_T = V(parts['tongue_root']); DIR_T = V(parts['tongue_dir'])
SPINE = [V((0, -0.04, 0.27)), V((0, -0.36, 0.30)), V((0, -0.68, 0.28)), V((0, -0.86, 0.24)), V((0, -0.97, 0.22)),
         V((0, -1.12, 0.19))]
TAIL_Y = np.linspace(0.06, BC.y - BR * 0.95, 9)
TAIL = [V((0, y, 0.20 + (0.135 - 0.20) * min(1.0, (y - 0.06) / 0.5))) for y in TAIL_Y]
ARM = [V((0.16, -0.72, 0.26)), V((0.24, -0.79, 0.17)), V((0.235, -0.86, 0.055)), V((0.235, -1.0, 0.015))]
LEG = [V((0.17, -0.07, 0.24)), V((0.25, -0.13, 0.15)), V((0.27, -0.09, 0.055)), V((0.29, -0.27, 0.015))]
FOOT_C = {'front': V((0.232, -0.89, 0.0)), 'hind': V((0.288, -0.19, 0.0))}

arm = bpy.data.armatures.new('Dillo_Rig'); rig = bpy.data.objects.new('Dillo_Rig', arm)
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


bone('Body', SPINE[0], SPINE[1])
bone('Spine', SPINE[1], SPINE[2], 'Body', True)
bone('Chest', SPINE[2], SPINE[3], 'Spine', True)
bone('Neck', SPINE[3], SPINE[4], 'Chest', True)
bone('Head', SPINE[4], SPINE[5], 'Neck', True)
bone('Tongue', ROOT_T, ROOT_T + DIR_T * parts['tongue_length'], 'Head')
for i in range(8):
    bone(f'Tail{i + 1}', TAIL[i], TAIL[i + 1], 'Body' if i == 0 else f'Tail{i}', i > 0, roll=V((1, 0, 0)))
bone('TailBall', TAIL[8], BC + V((0, BR * 1.2, 0)), 'Tail8', True, roll=V((1, 0, 0)))
bone('Spikes', BC, BC + V((0, BR, 0)), 'TailBall', roll=V((1, 0, 0)))
for s, sg in (('L', 1), ('R', -1)):
    a = [mx(p, sg) for p in ARM]; h = [mx(p, sg) for p in LEG]
    bone(f'UpperArm_{s}', a[0], a[1], 'Chest')
    bone(f'ForeArm_{s}', a[1], a[2], f'UpperArm_{s}', True)
    bone(f'Hand_{s}', a[2], a[3], f'ForeArm_{s}', True)
    bone(f'Thigh_{s}', h[0], h[1], 'Body')
    bone(f'Shin_{s}', h[1], h[2], f'Thigh_{s}', True)
    bone(f'HindFoot_{s}', h[2], h[3], f'Shin_{s}', True)
bpy.ops.object.mode_set(mode='OBJECT')

NOHEAT = [f'Tail{i + 1}' for i in range(8)] + ['TailBall', 'Spikes', 'Tongue']
for n in NOHEAT:
    arm.bones[n].use_deform = False
for o in bpy.data.objects: o.select_set(o in (mesh, rig))
bpy.context.view_layer.objects.active = rig
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
for n in NOHEAT:
    arm.bones[n].use_deform = True
groups = {g.name: g for g in mesh.vertex_groups}
for n in [b.name for b in arm.bones]:
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


# the shell rides the spine: limb weights only within a capsule around each leg (0.07 m full, gone at 0.13 m);
# elsewhere the heat weights restricted to the trunk bones (Body, Spine, Chest, Neck, Head)
TRUNK = ('Body', 'Spine', 'Chest', 'Neck', 'Head')
LIMBS = {}
for s, sg in (('L', 1), ('R', -1)):
    LIMBS[s] = [(np.array(mx(a, sg)[:]), np.array(mx(b, sg)[:])) for a, b in zip(ARM[:-1], ARM[1:])] + \
               [(np.array(mx(a, sg)[:]), np.array(mx(b, sg)[:])) for a, b in zip(LEG[:-1], LEG[1:])]


def seg_dist(c, a, b):
    d = b - a; t = np.clip(np.dot(c - a, d) / np.dot(d, d), 0, 1)
    return np.linalg.norm(a + t * d - c)


nshell = 0
for i in np.where(part == 0)[0]:
    c = co[i]
    old = {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[int(i)].groups}
    if not any(n not in TRUNK for n in old):
        continue
    dmin = min(seg_dist(c, a, b) for s in LIMBS for a, b in LIMBS[s])
    f = float(1 - ss((dmin - 0.07) / 0.06))
    trunk = {n: w for n, w in old.items() if n in TRUNK}
    if not trunk:
        y = c[1]; trunk = {'Spine' if y < -0.36 else 'Body': 1.0}
    tt = sum(trunk.values()); to = sum(old.values()) or 1.0
    new = {n: w / tt * (1 - f) for n, w in trunk.items()}
    for n, w in old.items():
        new[n] = new.get(n, 0) + w / to * f
    set_weights(i, new); nshell += 1
print('SHELL limb weights limited on', nshell, 'vertices')
for i in np.where(part == 1)[0]:
    set_weights(i, {'Head': 1.0})
for i in np.where(part == 2)[0]:
    set_weights(i, {'Spikes': 1.0})
for i in np.where(part == 3)[0]:
    set_weights(i, {'Tongue': 1.0})
# tail and ball by arc position; the tail region starts behind the rump plates (y > TAIL_Y[0] + 0.05)
P = np.array([p[:] for p in TAIL])
ntail = 0
for i in np.where(part == 0)[0]:
    c = co[i]
    if c[1] < TAIL_Y[0] + 0.03:
        continue
    if np.linalg.norm(c - np.array(BC[:])) < BR * 1.15 or c[1] > BC.y:
        set_weights(i, {'TailBall': 1.0}); ntail += 1
        continue
    best = None
    for k in range(8):
        a, b = P[k], P[k + 1]; d = b - a
        t = np.clip(np.dot(c - a, d) / np.dot(d, d), 0, 1)
        dist = np.linalg.norm(a + t * d - c)
        if best is None or dist < best[0]:
            best = (dist, k, t)
    _, k, t = best
    # blend into the joint ahead / behind
    if t < 0.5:
        w = {f'Tail{k + 1}': 0.5 + t, (f'Tail{k}' if k > 0 else 'Body'): 0.5 - t}
    else:
        w = {f'Tail{k + 1}': 1.5 - t, (f'Tail{k + 2}' if k < 7 else 'TailBall'): t - 0.5}
    set_weights(i, w); ntail += 1
# feet: below the wrist / ankle, wholly on Hand / HindFoot
nfoot = 0
for s, sg in (('L', 1), ('R', -1)):
    for kind, bn in (('front', f'Hand_{s}'), ('hind', f'HindFoot_{s}')):
        fc = np.array(mx(FOOT_C[kind], sg)[:])
        for i in np.where(part == 0)[0]:
            c = co[i]
            if sg * c[0] < 0.10 or np.linalg.norm((c - fc)[:2]) > 0.15 or c[2] > 0.09:
                continue
            blend = float(1 - ss((c[2] - 0.05) / 0.04))
            old = {mesh.vertex_groups[g.group].name: g.weight for g in me.vertices[int(i)].groups}
            tot = sum(old.values()) or 1.0
            new = {n: w / tot * (1 - blend) for n, w in old.items()}
            new[bn] = new.get(bn, 0) + blend
            set_weights(i, new); nfoot += 1
empty = [v.index for v in me.vertices if not any(g.weight > 1e-4 for g in v.groups)]
print('RIGGED bones', len(arm.bones), 'unweighted', len(empty), 'tail verts', ntail, 'foot verts', nfoot)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
