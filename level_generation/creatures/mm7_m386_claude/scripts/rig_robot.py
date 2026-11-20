"""Robot rig in Blender from work/rig_plan.json and work/weights.npz (rig_plan.py): import the Smart Topology
mesh, ground it (lowest point z = 0), build the bones (shifted by the same amount), assign the planned weights.
Forward -Y, up +Z, character left +X. Saves work/rig_v1.blend."""
import bpy, os, json
import numpy as np
from mathutils import Vector
P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=os.path.join(P, 'meshy/smart_topology_v1/model_urls_glb.glb'))
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
for o in list(bpy.data.objects):
    if o is not mesh: bpy.data.objects.remove(o, do_unlink=True)
mesh.parent = None
bpy.context.view_layer.objects.active = mesh; mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
co = np.array([tuple(v.co) for v in mesh.data.vertices]); Z0 = co[:, 2].min()
raw = np.load(os.path.join(P, 'work/raw_st1.npz'))['co']
assert len(raw) == len(co) and np.abs(raw - co).max() < 1e-5
mesh.location.z -= Z0; bpy.ops.object.transform_apply(location=True)
mesh.name = mesh.data.name = 'Robot'; mesh.data.materials.clear()
for p in mesh.data.polygons: p.use_smooth = True
plan = json.load(open(os.path.join(P, 'work/rig_plan.json')))
shift = Vector((0, 0, -Z0))
arm = bpy.data.armatures.new('Robot_Rig'); rig = bpy.data.objects.new('Robot_Rig', arm)
bpy.context.scene.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects: o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
for name, parent, h, t in plan['bones']:
    b = arm.edit_bones.new(name); b.head = Vector(h) + shift; b.tail = Vector(t) + shift
    b.align_roll(Vector((0, 0, 1)) if abs((b.tail - b.head).normalized().z) < 0.9 else Vector((0, -1, 0)))
    if parent:
        b.parent = arm.edit_bones[parent]
        b.use_connect = (Vector(arm.edit_bones[parent].tail) - b.head).length < 1e-6
SOCKETS = {'Socket_Eye': ('Head', (0.05, -0.385, 0.105)), 'Socket_Muzzle': ('Gun', (0.0, -0.262, -0.136))}
for sname, (parent, pos) in SOCKETS.items():
    s = arm.edit_bones.new(sname); s.head = Vector(pos) + shift; s.tail = s.head + Vector((0, -0.02, 0))
    s.parent = arm.edit_bones[parent]; s.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')
d = np.load(os.path.join(P, 'work/weights.npz')); W, names = d['W'], [str(n) for n in d['names']]
for j, n in enumerate(names):
    g = mesh.vertex_groups.new(name=n)
    for v in np.nonzero(W[:, j] > 1e-5)[0]:
        g.add([int(v)], float(W[v, j]), 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig; mesh.parent = rig
print('RIGGED', len(arm.bones), 'Z0', round(Z0, 4))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(P, 'work/rig_v1.blend'))
