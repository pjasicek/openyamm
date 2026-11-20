"""Right-hand grip and cutlass.

Grip: a handle cylinder along the knuckle line in front of the right palm. Each finger chain curls about one flex
axis (planar curl through its knuckle); its three angles come from a grid search that keeps every phalanx axis at
the handle radius plus the finger half-thickness and wraps the chain round the handle without entering it. The thumb
(Thumb1 swings across the palm, Thumb2/3 flex) closes over the outside of the handle. The solved pose bone
rotations (rest-relative quaternions) go to scene['ske_grip'] so every clip can key the same fist.

Sword: built in the rest frame on a 'Sword' bone (child of RightHand) at the handle centre, blade toward
-Y (forward from the thumb side of the fist), flat of the blade in the YZ plane, edge down (toward the fingers),
back curving up toward the tip like the native profile (skesta2: 0.68 m overall, 0.54 m blade, guard ~0.12 m).
Its faces get part id 999 and material 'Sword' (swatch UVs are assigned with the atlas).
Args: -- <rig blend> <out blend>"""
import bpy, sys, os, math, json
import numpy as np
from mathutils import Vector, Matrix, Quaternion
src, out = sys.argv[sys.argv.index('--') + 1:]
bpy.ops.wm.open_mainfile(filepath=os.path.abspath(src))
rig = bpy.data.objects['Skeleton_Rig']; body = bpy.data.objects['Skeleton']
B = lambda n: rig.pose.bones['mixamorig:' + n]
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
W = rig.matrix_world


def head(n):
    return np.array(W @ B(n).head)


def tail(n):
    return np.array(W @ B(n).tail)


S = 'Right'
FING = ('Index', 'Middle', 'Ring', 'Pinky')
knuck = np.mean([head(f'{S}Hand{f}1') for f in FING], axis=0)
d0 = np.mean([tail(f'{S}Hand{f}1') - head(f'{S}Hand{f}1') for f in FING], axis=0); d0 /= np.linalg.norm(d0)
line = head(f'{S}HandPinky1') - head(f'{S}HandIndex1')       # knuckle line, index -> pinky
line -= d0 * line.dot(d0); line /= np.linalg.norm(line)
# palm normal: the side the relaxed fingers already curl toward
tipdir = np.mean([tail(f'{S}Hand{f}3') - head(f'{S}Hand{f}1') for f in FING], axis=0)
n = tipdir - d0 * tipdir.dot(d0) - line * tipdir.dot(line); n /= np.linalg.norm(n)
R_GRIP, FINGER_R = 0.0135, 0.0085
C = knuck + d0 * 0.012 + n * 0.020                           # handle axis point; axis along `line`
print('GRIP centre', np.round(C, 3), 'axis', np.round(line, 3), 'palm normal', np.round(n, 3), 'finger dir', np.round(d0, 3))


def rot(axis, ang):
    return np.array(Matrix.Rotation(ang, 3, Vector(axis)))


def radial(p):
    v = p - C
    return float(np.linalg.norm(v - line * v.dot(line)))


def fk(joints, axis, angs):
    p = [j.copy() for j in joints]
    for i, a in enumerate(angs):
        R = rot(axis, a)
        for k in range(i + 1, len(p)):
            p[k] = p[i] + R @ (p[k] - p[i])
    return p


def chain_cost(p):
    cost = 0.0
    want = R_GRIP + FINGER_R
    for a, b in zip(p[:-1], p[1:]):
        for t in np.linspace(0.15, 1.0, 6):
            q = a + (b - a) * t
            r = radial(q)
            cost += (r - want) ** 2 + (200 * (want - r - 0.002) ** 2 if r < want - 0.002 else 0)
    return cost


solution = {}
for f in FING:
    joints = [head(f'{S}Hand{f}{i}') for i in (1, 2, 3)] + [tail(f'{S}Hand{f}3')]
    fdir = joints[1] - joints[0]
    axis = np.cross(fdir, n); axis /= np.linalg.norm(axis)        # +angle curls toward the palm
    if np.dot(rot(axis, 0.3) @ fdir, n) < np.dot(fdir, n):
        axis = -axis
    best = (1e9, None)
    grid = np.radians(np.arange(0, 121, 4))
    for a1 in grid:
        for a2 in grid:
            for a3 in grid[::2]:
                c = chain_cost(fk(joints, axis, (a1, a2, a3)))
                if c < best[0]:
                    best = (c, (a1, a2, a3))
    a = best[1]
    p = fk(joints, axis, a)
    print('FINGER', f, 'deg', np.round(np.degrees(a), 0), 'radial cm', [round(float(radial(x)) * 100, 1) for x in p[1:]])
    solution[f] = (axis, a)

# thumb: Thumb1 swings about the finger direction (across the palm) then all three flex toward the palm
tj = [head(f'{S}HandThumb{i}') for i in (1, 2, 3)] + [tail(f'{S}HandThumb3')]
best = (1e9, None)
for sw in np.radians(np.arange(-40, 61, 5)):
    Rs = rot(d0, sw)
    pj = [tj[0]] + [tj[0] + Rs @ (x - tj[0]) for x in tj[1:]]
    fdir = pj[1] - pj[0]
    ax = np.cross(fdir, n); ax /= np.linalg.norm(ax)
    for a1 in np.radians(np.arange(0, 61, 5)):
        for a2 in np.radians(np.arange(0, 81, 5)):
            for a3 in np.radians(np.arange(0, 81, 10)):
                p = fk(pj, ax, (a1, a2, a3))
                c = chain_cost(p[1:]) + 4 * float(np.linalg.norm(p[-1] - (C + n * (R_GRIP + FINGER_R) - d0 * 0.004))) ** 2
                if c < best[0]:
                    best = (c, (sw, ax, (a1, a2, a3)))
sw, tax, ta = best[1]
print('THUMB swing', round(math.degrees(sw)), 'flex', np.round(np.degrees(ta), 0))


def turn(bone, axis, ang):
    pb = B(bone)
    bpy.context.view_layer.update()
    m = W @ pb.matrix
    h = m.translation.copy()
    w = Matrix.Translation(h) @ Matrix.Rotation(ang, 4, Vector(axis)) @ Matrix.Translation(-h) @ m
    pb.matrix = W.inverted() @ w
    bpy.context.view_layer.update()


for f, (axis, a) in solution.items():
    for i in (1, 2, 3):
        turn(f'{S}Hand{f}{i}', axis, a[i - 1])     # the axis is fixed in world (planar curl from the rest pose)
turn(f'{S}HandThumb1', d0, sw)
for i in (1, 2, 3):
    turn(f'{S}HandThumb{i}', tax, ta[i - 1])
grip = {pb.name: list(pb.rotation_quaternion) for pb in rig.pose.bones
        if pb.name.startswith('mixamorig:RightHand') and pb.name != 'mixamorig:RightHand'}
for pb in rig.pose.bones:
    if pb.name in grip:
        pb.rotation_mode = 'QUATERNION'
bpy.context.scene['ske_grip'] = json.dumps(grip)

# penetration of the posed finger pieces into the handle
deps = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(deps).to_mesh()
co = np.array([tuple(body.matrix_world @ v.co) for v in ev.vertices])
body.evaluated_get(deps).to_mesh_clear()
v = co - C; along = v @ line; rad = np.linalg.norm(v - np.outer(along, line), axis=1)
inside = (rad < R_GRIP - 0.001) & (np.abs(along) < 0.06)
print('GRIP penetration verts', int(inside.sum()), 'min radial cm', round(float(rad[np.abs(along) < 0.06].min()) * 100, 2))

# ---------------------------------------------------------------- Sword bone and mesh (rest frame)
fwd = -line if line[1] > 0 else line          # blade exits the thumb (front, -Y) side of the fist
guard_c = C + fwd * 0.058
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones.new('Sword')
eb.head = Vector(C); eb.tail = Vector(C + fwd * 0.12)
eb.parent = rig.data.edit_bones['mixamorig:RightHand']
eb.align_roll(Vector((0, 0, 1)))
bpy.ops.object.mode_set(mode='OBJECT')

up = np.array([0.0, 0.0, 1.0]); up = up - fwd * up.dot(fwd); up /= np.linalg.norm(up)   # spine side
flat = np.cross(fwd, up)                                                               # blade normal
verts, faces, cls = [], [], []


def P(a, e, f, base=guard_c):
    return tuple(base + fwd * a + up * e + flat * f)


def add(ps):
    verts.extend(ps); return len(verts) - len(ps)


def quad(a, b, c, d, k):
    faces.append((a, b, c, d)); cls.append(k)


def tri(a, b, c, k):
    faces.append((a, b, c)); cls.append(k)


L = 0.54
ts = [0.0, 0.1, 0.22, 0.36, 0.5, 0.62, 0.74, 0.84, 0.92]


def prof(t):
    """centre offset (up), half-width toward the edge (down), back width, half thickness"""
    rise = 0.028 * t ** 2.2                                  # back curves up toward the tip
    w_edge = 0.022 + 0.014 * t                             # cutlass: wider toward the tip
    w_back = 0.007
    if t > 0.8:
        u = (t - 0.8) / 0.2
        w_edge *= 1 - u ** 1.2; w_back *= 1 - u ** 2.5
    return rise, w_edge, w_back, 0.0035 - 0.002 * t


rings = []
for t in ts:
    c, we, wb, th = prof(t)
    a = 0.006 + L * t
    rings.append(add([P(a, c - we, 0), P(a, c - we * 0.35, th), P(a, c + wb, th * 0.7), P(a, c + wb, -th * 0.7),
                      P(a, c - we * 0.35, -th)]))
tc, *_ = prof(1.0)
tip = add([P(0.006 + L, tc + 0.004, 0)])
EK = {0: 'edge', 1: 'blade', 2: 'blade', 3: 'blade', 4: 'edge'}
for r0, r1 in zip(rings[:-1], rings[1:]):
    for k in range(5):
        quad(r0 + k, r1 + k, r1 + (k + 1) % 5, r0 + (k + 1) % 5, EK[k])
for k in range(5):
    tri(rings[-1] + k, tip, rings[-1] + (k + 1) % 5, EK[k])
faces.append(tuple(rings[0] + k for k in range(5))[::-1]); cls.append('blade')


def tube(points, radius, k, sides=6):
    idx = []
    for i, p in enumerate(points):
        p = np.array(p)
        d = np.array(points[min(i + 1, len(points) - 1)]) - np.array(points[max(i - 1, 0)]); d /= np.linalg.norm(d)
        u = flat - d * flat.dot(d); u /= np.linalg.norm(u); w = np.cross(d, u)
        r = radius[i] if isinstance(radius, (list, tuple)) else radius
        idx.append(add([tuple(p + (u * math.cos(2 * math.pi * s / sides) + w * math.sin(2 * math.pi * s / sides)) * r)
                        for s in range(sides)]))
    for a0, a1 in zip(idx[:-1], idx[1:]):
        for s in range(sides):
            quad(a0 + s, a1 + s, a1 + (s + 1) % sides, a0 + (s + 1) % sides, k)
    faces.append(tuple(idx[0] + s for s in range(sides))[::-1]); cls.append(k)
    faces.append(tuple(idx[-1] + s for s in range(sides))); cls.append(k)


# crossguard in the blade plane (native profile: a vertical bar), knob ends; grip through the fist; pommel knob
tube([P(0, e, 0) for e in (-0.052, -0.040, 0.0, 0.040, 0.052)], [0.0085, 0.0055, 0.0065, 0.0055, 0.0085], 'brass')
grip_len = 0.058 + 0.050
tube([P(-a, 0, 0) for a in (0.004, 0.03, 0.06, 0.085, grip_len)], [0.0125, 0.0135, 0.0135, 0.0135, 0.0125], 'grip', 8)
tube([P(-grip_len - a, 0, 0) for a in (0.0, 0.008, 0.018, 0.026)], [0.011, 0.016, 0.015, 0.006], 'brass', 8)

me = bpy.data.meshes.new('SwordMesh')
me.from_pydata([tuple(v) for v in verts], [], faces)
me.update()
so = bpy.data.objects.new('SwordTmp', me)
bpy.context.scene.collection.objects.link(so)
CLS = ['blade', 'edge', 'brass', 'grip']
me.attributes.new('sword_class', 'INT', 'FACE').data.foreach_set('value', [CLS.index(k) for k in cls])
me.attributes.new('piece', 'INT', 'POINT').data.foreach_set('value', [999] * len(verts))
g = so.vertex_groups.new(name='Sword'); g.add(list(range(len(verts))), 1.0, 'REPLACE')
for p, k in zip(me.polygons, cls):
    p.use_smooth = k != 'brass'
smat = bpy.data.materials.get('Sword') or bpy.data.materials.new('Sword')
smat.diffuse_color = (0.62, 0.36, 0.2, 1)
so.data.materials.append(bpy.data.materials['Bone'])
so.data.materials.append(smat)
for p in me.polygons:
    p.material_index = 1
print('SWORD tris', sum(len(f) - 2 for f in faces))
# join into the body at the rest pose (the armature modifier deforms both by the same weights)
for pb in rig.pose.bones:
    pb.matrix_basis = Matrix()
bpy.context.view_layer.update()
for o in bpy.data.objects:
    o.select_set(o in (body, so))
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
bpy.context.scene['ske_sword'] = json.dumps({'grip': [float(x) for x in C], 'axis': [float(x) for x in fwd],
                                             'up': [float(x) for x in up], 'flat': [float(x) for x in flat],
                                             'radius': R_GRIP})
# show the grip on the rest so the save previews it
for name, q in grip.items():
    rig.pose.bones[name].rotation_quaternion = Quaternion(q)
bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(out))
