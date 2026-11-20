"""Ooze rig: work/ooze_raw.blend -> work/rig_v1.blend (mesh 'Ooze', armature 'Ooze_Rig').

Anatomy (README, "Anatomy decisions"): a blob with no limbs. Squash and stretch come from lump bones whose heads lie
on the floor, so scaling or sliding them never lifts or sinks the underside (mm6_ooz_claude route).
- Reduction: the never-seen underside to 15 %, the rest to reach about BLOB_TRIS triangles (a smooth blob; the
  wormy ridges live in the normal map).
- Pseudopod (native attack m298ab..af: a thin lumpy stalk with a big onion/diamond-shaped knob rises from the middle
  to about 3.7x the blob height, curls back, then strikes forward): a lathe tube with the knob at its end, built
  along +Z from inside the blob's middle. It stands fully grown in the bind pose and is hidden (PodRoot scale 0.02
  inside the blob) in every clip except Attack and Cast.
- Globules (native death m298dc..de and corpse m298xa: the blob bursts into many round globs that rain down and lie
  scattered around): GLOBS low-poly spheres, each rigid on its own bone, resting in the bind pose at their corpse
  places on the floor around the blob. Hidden (scale 0.001 inside the blob) except in Death, Dead and Fidget (two
  of them are the fidget's bubbles).
- Bones: Root (floor, non-deforming) -> Body (non-deforming) -> Lump_C + Lump_0..7 on an ellipse at 55 % of the
  outline (Lump_0 front -Y, clockwise from above), Body -> PodRoot (non-deforming) -> Pod1..Pod5 -> Knob
  (-> Socket_Spit, non-deforming, top of the knob), Root -> Glob_00..Glob_NN.
- Weights: blob = automatic (heat) weights over the lump bones; pod = linear blend along the chain by height; each
  glob 100 % its bone. One mesh, one draw; face attribute 'part': 0 blob, 1 pod, 2 globs.
Args: none"""
import bpy, bmesh, sys, os, math, json
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

BLOB_TRIS = 3400
bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'ooze_raw.blend'))
blob = bpy.data.objects['Ooze']
me = blob.data
DEPTH = 0.92                                            # Meshy's plan is square; native side length / front width
for v in me.vertices:                                   # = 164 / 178
    v.co.y *= DEPTH


def decimate_selected(obj, pred, ratio):
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    flags = [pred(p) for p in obj.data.polygons]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')
    bm = bmesh.from_edit_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    for f in bm.faces:
        f.select_set(flags[f.index])
    bm.select_flush_mode()
    bmesh.update_edit_mesh(obj.data)
    bpy.ops.mesh.decimate(ratio=ratio)
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.mesh.select_all(action='DESELECT')
    bpy.ops.object.mode_set(mode='OBJECT')


under = lambda p: p.center.z < 0.02 and p.normal.z < -0.5
before = sum(len(p.vertices) - 2 for p in me.polygons)
n_under = sum(len(p.vertices) - 2 for p in me.polygons if under(p))
decimate_selected(blob, under, 0.15)
n_top = sum(len(p.vertices) - 2 for p in me.polygons if not under(p))
target_top = BLOB_TRIS - int(n_under * 0.15)
if n_top > target_top:
    decimate_selected(blob, lambda p: not under(p), target_top / n_top)
for v in me.vertices:                                   # decimation leaves underside vertices slightly below 0
    v.co.z = max(v.co.z, 0.0)
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
rx, ry, top = float(np.abs(co[:, 0]).max()), float(np.abs(co[:, 1]).max()), float(co[:, 2].max())
# the dome's height near the middle (the pod base sits under it)
mid = co[(np.abs(co[:, 0]) < 0.08) & (np.abs(co[:, 1]) < 0.08)]
mid_top = float(mid[:, 2].max()) if len(mid) else top
print('REDUCED', before, '->', sum(len(p.vertices) - 2 for p in me.polygons), 'half extents', round(rx, 3),
      round(ry, 3), 'top', round(top, 3), 'middle top', round(mid_top, 3))

# ---------------------------------------------------------------- pseudopod with knob (lathe along +Z)
POD_BASE = Vector((0.0, 0.0, 0.05))
STALK, KNOB_H, R_STALK0, R_STALK1, R_KNOB = 0.54, 0.26, 0.062, 0.05, 0.135
SIDES = 12
POD_LEN = STALK + KNOB_H


def pod_radius(z):
    if z <= STALK:
        t = z / STALK
        r = R_STALK0 + (R_STALK1 - R_STALK0) * t
        return r * (1 + 0.13 * math.sin(t * math.pi * 6 + 0.4))          # lumpy stalk, as in the native pod
    u = (z - STALK) / KNOB_H                              # knob: flares out fast, widest at 35 %, rounded point on top
    if u < 0.35:
        k = math.sin(u / 0.35 * math.pi / 2)
        return R_STALK1 + (R_KNOB - R_STALK1) * k ** 0.8
    w = (u - 0.35) / 0.65
    return max(R_KNOB * math.sqrt(max(1 - w ** 1.6, 0.0)) * (1 - 0.25 * w), 0.004)


zs = list(np.linspace(0, STALK, 15)) + list(STALK + KNOB_H * np.array([0.08, 0.18, 0.28, 0.38, 0.5, 0.62, 0.74,
                                                                     0.85, 0.93, 0.98]))
bm = bmesh.new()
rings = []
for z in zs:
    r = pod_radius(z)
    rings.append([bm.verts.new(POD_BASE + Vector((r * math.cos(2 * math.pi * k / SIDES),
                                                   r * math.sin(2 * math.pi * k / SIDES), z))) for k in range(SIDES)])
for a, b in zip(rings, rings[1:]):
    for k in range(SIDES):
        bm.faces.new((a[k], a[(k + 1) % SIDES], b[(k + 1) % SIDES], b[k]))
tipv = bm.verts.new(POD_BASE + Vector((0, 0, POD_LEN)))
for k in range(SIDES):
    bm.faces.new((rings[-1][k], rings[-1][(k + 1) % SIDES], tipv))
basev = bm.verts.new(POD_BASE - Vector((0, 0, 0.004)))
for k in range(SIDES):
    bm.faces.new((rings[0][(k + 1) % SIDES], rings[0][k], basev))
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
pme = bpy.data.meshes.new('Pod')
bm.to_mesh(pme)
bm.free()
for p in pme.polygons:
    p.use_smooth = True
pod = bpy.data.objects.new('Pod', pme)
bpy.context.scene.collection.objects.link(pod)

# ---------------------------------------------------------------- globules at their corpse places (native m298xa)
rng = np.random.default_rng(298)
GLOBS = []
n_glob = 12
for k in range(n_glob):
    a = 2 * math.pi * (k + 0.35 * rng.random()) / n_glob
    rad = 0.045 + 0.05 * rng.random() if k % 3 else 0.085 + 0.025 * rng.random()
    d = (0.42 + 0.30 * rng.random())                     # scattered out to about 1.4x the blob's half width
    c = Vector((d * math.sin(a) * 1.15, -d * math.cos(a) * 0.95, rad * 0.62))
    GLOBS.append((f'Glob_{k:02d}', c, rad))
gm = bpy.data.meshes.new('Globs')
bm = bmesh.new()
for name, c, rad in GLOBS:
    res = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=rad)
    for v in res['verts']:
        v.co = Vector((v.co.x, v.co.y, v.co.z * 0.62)) + c   # lying globs are flattened drops
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(gm)
bm.free()
for p in gm.polygons:
    p.use_smooth = True
globs = bpy.data.objects.new('Globs', gm)
bpy.context.scene.collection.objects.link(globs)

# ---------------------------------------------------------------- armature
arm_data = bpy.data.armatures.new('Ooze_Rig')
arm = bpy.data.objects.new('Ooze_Rig', arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, deform=True, connect=False):
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    b.parent = eb[parent] if parent else None
    b.use_connect = connect
    b.use_deform = deform
    return b


bone('Root', (0, 0, 0), (0, 0, 0.08), deform=False)
bone('Body', (0, 0, 0), (0, 0, top * 0.9), 'Root', deform=False)
bone('Lump_C', (0, 0, 0), (0, 0, top), 'Body')
LUMPS = []
for i in range(8):
    a = 2 * math.pi * i / 8
    x, y = rx * 0.55 * math.sin(a), -ry * 0.55 * math.cos(a)
    bone(f'Lump_{i}', (x, y, 0), (x, y, top * 0.7), 'Body')
    LUMPS.append(f'Lump_{i}')
bone('PodRoot', tuple(POD_BASE), tuple(POD_BASE + Vector((0, 0, 0.03))), 'Body', deform=False)
NPOD = 5
seg = (STALK - 0.03) / NPOD
prev = 'PodRoot'
for i in range(NPOD):
    z0 = 0.03 + seg * i
    bone(f'Pod{i + 1}', tuple(POD_BASE + Vector((0, 0, z0))), tuple(POD_BASE + Vector((0, 0, z0 + seg))), prev,
         connect=i > 0)
    prev = f'Pod{i + 1}'
bone('Knob', tuple(POD_BASE + Vector((0, 0, STALK))), tuple(POD_BASE + Vector((0, 0, POD_LEN))), prev, connect=True)
bone('Socket_Spit', tuple(POD_BASE + Vector((0, 0, POD_LEN))), tuple(POD_BASE + Vector((0, 0, POD_LEN + 0.04))),
     'Knob', deform=False)
for name, c, rad in GLOBS:
    bone(name, tuple(c), tuple(c + Vector((0, 0, max(rad, 0.05)))), 'Root')
bpy.ops.object.mode_set(mode='OBJECT')

lump_names = ['Lump_C'] + LUMPS
pod_names = [f'Pod{i + 1}' for i in range(NPOD)] + ['Knob']
glob_names = [g[0] for g in GLOBS]

# blob: heat weights over the lumps only
for b in arm_data.bones:
    b.use_deform = b.name in lump_names
for o in bpy.data.objects:
    o.select_set(o in (blob, arm))
bpy.context.view_layer.objects.active = arm
bpy.ops.object.parent_set(type='ARMATURE_AUTO')
loose = [v.index for v in blob.data.vertices if not v.groups]
if loose:                                               # detached droplets: weights of the nearest weighted vertex
    from mathutils.kdtree import KDTree
    kd = KDTree(len(blob.data.vertices))
    for v in blob.data.vertices:
        if v.groups:
            kd.insert(v.co, v.index)
    kd.balance()
    names = {g.index: g.name for g in blob.vertex_groups}
    for i in loose:
        _, j, _ = kd.find(blob.data.vertices[i].co)
        for g in blob.data.vertices[j].groups:
            blob.vertex_groups[names[g.group]].add([i], g.weight, 'REPLACE')
print('WEIGHTS blob loose copied', len(loose), 'unweighted', sum(1 for v in blob.data.vertices if not v.groups))

# pod: linear blend between neighbouring segment centres by height; the knob is rigid above its neck
seg_mid = [0.03 + seg * (i + 0.5) for i in range(NPOD)]
for n in pod_names:
    pod.vertex_groups.new(name=n)
for v in pme.vertices:
    z = v.co.z - POD_BASE.z
    if z >= STALK - 0.01:
        w = {'Knob': 1.0} if z >= STALK + 0.03 else {'Knob': (z - STALK + 0.01) / 0.04, f'Pod{NPOD}': 1 - (z - STALK + 0.01) / 0.04}
    elif z <= seg_mid[0]:
        w = {'Pod1': 1.0}
    elif z >= seg_mid[-1]:
        w = {f'Pod{NPOD}': 1.0}
    else:
        i = int(np.searchsorted(seg_mid, z)) - 1
        f = (z - seg_mid[i]) / (seg_mid[i + 1] - seg_mid[i])
        w = {f'Pod{i + 1}': 1 - f, f'Pod{i + 2}': f}
    for n, x in w.items():
        if x > 1e-4:
            pod.vertex_groups[n].add([v.index], float(x), 'REPLACE')
# globs: rigid, each sphere's vertices to its own bone (nearest centre)
for n, _, _ in GLOBS:
    globs.vertex_groups.new(name=n)
cent = np.array([tuple(c) for _, c, _ in GLOBS])
for v in gm.vertices:
    k = int(np.argmin(((cent - np.array(tuple(v.co))) ** 2).sum(1)))
    globs.vertex_groups[GLOBS[k][0]].add([v.index], 1.0, 'REPLACE')

for b in arm_data.bones:
    b.use_deform = b.name in set(lump_names) | set(pod_names) | set(glob_names)
for o, k in ((blob, 0), (pod, 1), (globs, 2)):
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [k] * len(o.data.polygons))
for o in (pod, globs):
    o.parent = arm
    m = o.modifiers.new('Armature', 'ARMATURE')
    m.object = arm
for o in bpy.data.objects:
    o.select_set(o in (blob, pod, globs))
bpy.context.view_layer.objects.active = blob
bpy.ops.object.join()
mods = [m for m in blob.modifiers if m.type == 'ARMATURE']
for m in mods[1:]:
    blob.modifiers.remove(m)
dims = {'rx': rx, 'ry': ry, 'top': top, 'mid_top': mid_top, 'pod_len': POD_LEN, 'stalk': STALK,
        'pod_base': list(POD_BASE), 'globs': [[n, list(c), r] for n, c, r in GLOBS]}
bpy.context.scene['ooze_dims'] = json.dumps(dims)
json.dump(dims, open(os.path.join(common.WORK, 'dims.json'), 'w'), indent=1)
part = np.zeros(len(blob.data.polygons), int)
blob.data.attributes['part'].data.foreach_get('value', part)
tri = np.array([len(p.vertices) - 2 for p in blob.data.polygons])
print('RIG tris', int(tri.sum()), 'blob', int(tri[part == 0].sum()), 'pod', int(tri[part == 1].sum()), 'globs',
      int(tri[part == 2].sum()), 'bones', len(arm_data.bones),
      'unweighted', sum(1 for v in blob.data.vertices if not v.groups))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
