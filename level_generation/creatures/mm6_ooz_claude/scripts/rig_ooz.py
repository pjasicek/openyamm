"""Ooze rig: work/ooz_raw.blend -> work/rig_v1.blend (mesh 'Ooze', armature 'Ooze_Rig').

- Reduction: the never-seen underside to 15 %, the rest to 50 % (6.6k -> ~3k triangles; a smooth blob).
- Pseudopod: a tapered tube with a round tip (native attack: a pod rises from the middle, arches and strikes),
  built along +Z from just inside the blob's top; it is hidden at rest (PodRoot scaled to ~0) and grows in Attack.
- Bones: Root (floor, non-deforming) -> Body (non-deforming; whole-body squash/slide) -> Lump_C (centre) and
  Lump_0..7 on an ellipse at 55 % of the outline, every lump's head on the floor so its scale and rise never lift the
  underside; Body -> PodRoot -> Pod1..Pod6 along the tube (0.62 m, lumpy; native pod ~2.1x the blob height).
- Weights: the blob takes automatic (heat) weights from the lump bones only, the tube from the pod chain only; the two
  are joined into one mesh (one draw). Faces carry a 'part' attribute: 0 blob, 1 pod."""
import bpy, bmesh, sys, os, math
import numpy as np
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common

bpy.ops.wm.open_mainfile(filepath=os.path.join(common.WORK, 'ooz_raw.blend'))
blob = bpy.data.objects['Ooze']
me = blob.data


def decimate_selected(obj, pred, ratio):
    for o in bpy.data.objects:
        o.select_set(o == obj)
    bpy.context.view_layer.objects.active = obj
    flags = [pred(p) for p in obj.data.polygons]
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    bpy.ops.mesh.select_all(action='DESELECT')         # imported meshes come with every vertex selected
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


before = len(me.polygons)
decimate_selected(blob, lambda p: p.center.z < 0.02 and p.normal.z < -0.5, 0.15)
decimate_selected(blob, lambda p: not (p.center.z < 0.02 and p.normal.z < -0.5), 0.5)
for p in me.polygons:
    p.use_smooth = True
co = np.array([tuple(v.co) for v in me.vertices])
rx, ry, top = co[:, 0].max(), co[:, 1].max(), co[:, 2].max()
print('REDUCED', before, '->', len(me.polygons), 'half extents', round(rx, 3), round(ry, 3), 'top', round(top, 3))

# pseudopod tube (along +Z from POD_BASE)
POD_BASE = Vector((0.0, -0.04, 0.06))
POD_LEN, R0, R1, SIDES, RINGS = 0.62, 0.09, 0.07, 12, 24       # native: ~2.1x the blob height, ~22 % of its width
bm = bmesh.new()
rings = []
for i in range(RINGS + 1):
    t = i / RINGS
    r = R0 + (R1 - R0) * t
    r *= 1 + 0.12 * math.sin(t * math.pi * 7 + 0.6) * (t < 0.88)   # lumpy, as in the native pod
    if t > 0.88:                                        # round the tip
        r *= math.sqrt(max(1 - ((t - 0.88) / 0.12) ** 2, 0.04))
    rings.append([bm.verts.new(POD_BASE + Vector((r * math.cos(2 * math.pi * k / SIDES),
                                                   r * math.sin(2 * math.pi * k / SIDES), POD_LEN * t)))
                  for k in range(SIDES)])
for a, b in zip(rings, rings[1:]):
    for k in range(SIDES):
        bm.faces.new((a[k], a[(k + 1) % SIDES], b[(k + 1) % SIDES], b[k]))
tip = bm.verts.new(POD_BASE + Vector((0, 0, POD_LEN + 0.004)))
for k in range(SIDES):
    bm.faces.new((rings[-1][k], rings[-1][(k + 1) % SIDES], tip))
base = bm.verts.new(POD_BASE - Vector((0, 0, 0.004)))
for k in range(SIDES):
    bm.faces.new((rings[0][(k + 1) % SIDES], rings[0][k], base))
bmesh.ops.triangulate(bm, faces=bm.faces)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
pme = bpy.data.meshes.new('Pod')
bm.to_mesh(pme)
bm.free()
for p in pme.polygons:
    p.use_smooth = True
pod = bpy.data.objects.new('Pod', pme)
bpy.context.scene.collection.objects.link(pod)

# armature
arm_data = bpy.data.armatures.new('Ooze_Rig')
arm = bpy.data.objects.new('Ooze_Rig', arm_data)
bpy.context.scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
for o in bpy.data.objects:
    o.select_set(o == arm)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, deform=True):
    b = eb.new(name)
    b.head, b.tail = Vector(head), Vector(tail)
    b.parent = eb[parent] if parent else None
    b.use_deform = deform
    return b


bone('Root', (0, 0, 0), (0, 0, 0.08), deform=False)
bone('Body', (0, 0, 0), (0, 0, top * 0.9), 'Root', deform=False)
bone('Lump_C', (0, 0, 0), (0, 0, top), 'Body')
LUMPS = []
for i in range(8):
    a = 2 * math.pi * i / 8
    x, y = rx * 0.55 * math.sin(a), -ry * 0.55 * math.cos(a)   # Lump_0 at the front (-Y), clockwise from above
    bone(f'Lump_{i}', (x, y, 0), (x, y, top * 0.7), 'Body')
    LUMPS.append((f'Lump_{i}', a))
bone('PodRoot', tuple(POD_BASE), tuple(POD_BASE + Vector((0, 0, 0.04))), 'Body', deform=False)
prev = 'PodRoot'
NPOD = 6
seg = (POD_LEN - 0.04) / NPOD
for i in range(NPOD):
    z0 = 0.04 + seg * i
    bone(f'Pod{i + 1}', tuple(POD_BASE + Vector((0, 0, z0))), tuple(POD_BASE + Vector((0, 0, z0 + seg))), prev)
    eb[f'Pod{i + 1}'].use_connect = i > 0
    prev = f'Pod{i + 1}'
bpy.ops.object.mode_set(mode='OBJECT')


def auto_weights(obj, deform_names):
    for b in arm_data.bones:
        b.use_deform = b.name in deform_names
    for o in bpy.data.objects:
        o.select_set(o in (obj, arm))
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.parent_set(type='ARMATURE_AUTO')
    loose = [v.index for v in obj.data.vertices if not v.groups]
    if loose:                                            # detached droplets: weights of the nearest weighted vertex
        from mathutils.kdtree import KDTree
        kd = KDTree(len(obj.data.vertices))
        for v in obj.data.vertices:
            if v.groups:
                kd.insert(v.co, v.index)
        kd.balance()
        names = {g.index: g.name for g in obj.vertex_groups}
        for i in loose:
            _, j, _ = kd.find(obj.data.vertices[i].co)
            for g in obj.data.vertices[j].groups:
                obj.vertex_groups[names[g.group]].add([i], g.weight, 'REPLACE')
    unweighted = sum(1 for v in obj.data.vertices if not v.groups)
    print('WEIGHTS', obj.name, 'loose copied', len(loose), 'unweighted', unweighted)
    return unweighted


lump_names = {'Lump_C'} | {n for n, _ in LUMPS}
pod_names = {f'Pod{i + 1}' for i in range(NPOD)}
assert auto_weights(blob, lump_names) == 0
assert auto_weights(pod, pod_names) == 0
for b in arm_data.bones:
    b.use_deform = b.name in lump_names | pod_names
for o, k in ((blob, 0), (pod, 1)):
    a = o.data.attributes.new('part', 'INT', 'FACE')
    a.data.foreach_set('value', [k] * len(o.data.polygons))
for o in bpy.data.objects:
    o.select_set(o in (blob, pod))
bpy.context.view_layer.objects.active = blob
bpy.ops.object.join()
mods = [m for m in blob.modifiers if m.type == 'ARMATURE']
for m in mods[1:]:
    blob.modifiers.remove(m)
bpy.context.scene['ooz_dims'] = {'rx': float(rx), 'ry': float(ry), 'top': float(top), 'pod_len': POD_LEN,
                                 'pod_base': list(POD_BASE)}
print('RIG tris', sum(len(p.vertices) - 2 for p in blob.data.polygons), 'bones', len(arm_data.bones))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(common.WORK, 'rig_v1.blend'))
