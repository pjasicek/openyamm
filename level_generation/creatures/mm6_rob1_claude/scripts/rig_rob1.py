"""Patrol Unit rig from work/clean_v1.blend. Saves work/rig_v1.blend. Forward -Y, up +Z, robot's left +X.

A rigid hard-surface robot: every part is bound 100 % to one bone (face attribute 'part' from clean_rob1.py).
  Root        floor point under the sphere; carries the hover height and the travel lean
  Body        sphere centre; whole-robot tilt and spin
  CapTop/CapBottom  upper/lower half of the core sphere (split at the equator, inside the belt); apart only in Death
  RingTop/RingBottom  the two bronze rings
  Eye         sphere centre, aimed at the lens; the lens slides around the belt (scan) by yaw
  Sensor      base of the sensor post on top of the sphere; the sensor head turns and tilts with it
Sockets (empties): Socket_Eye on the lens (engine eye glow), Socket_Lens at the sensor nozzle (shot origin)."""
import bpy, os
import numpy as np
from mathutils import Vector, Matrix

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
mesh = bpy.data.objects['Robot']
me = mesh.data
part = np.array([d.value for d in me.attributes['part'].data])
co = np.array([tuple(v.co) for v in me.vertices])
vpart = np.full(len(co), -1)
for p in me.polygons:
    for v in p.vertices:
        vpart[v] = part[p.index]
core = co[vpart == 0]
centre = Vector((0.0, 0.0, float(core[:, 2].min() + core[:, 2].max()) / 2))
sensor = co[vpart == 4]
post = sensor[sensor[:, 2] < core[:, 2].max() + 0.04]
post_base = Vector((float(np.median(post[:, 0])), float(np.median(post[:, 1])), float(core[:, 2].max()) - 0.01))
nozzle = sensor[sensor[:, 1] < sensor[:, 1].min() + 0.004]
lens_point = Vector(nozzle.mean(0)) + Vector((0, -0.005, 0))
eye = co[vpart == 3]
eye_front = Vector(eye[eye[:, 1] < eye[:, 1].min() + 0.004].mean(0))

arm = bpy.data.armatures.new('Robot_Rig')
rig = bpy.data.objects.new('Robot_Rig', arm)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = arm.edit_bones


def bone(name, head, tail, parent=None):
    b = eb.new(name); b.head = head; b.tail = tail; b.parent = parent
    b.align_roll(Vector((0, -1, 0)) if abs((tail - head).normalized().z) > 0.9 else Vector((0, 0, 1)))
    return b


up = Vector((0, 0, 0.15))
root = bone('Root', Vector((0, 0, 0)), up)
body = bone('Body', centre, centre + up, root)
bone('CapTop', centre + Vector((0, 0, 0.05)), centre + Vector((0, 0, 0.25)), body)
bone('CapBottom', centre - Vector((0, 0, 0.05)), centre - Vector((0, 0, 0.25)), body)
bone('RingTop', centre + Vector((0, 0, 0.10)), centre + Vector((0, 0, 0.30)), body)
bone('RingBottom', centre - Vector((0, 0, 0.10)), centre - Vector((0, 0, 0.30)), body)
bone('Eye', centre, Vector((0, eye_front.y, centre.z)), body)
bone('Sensor', post_base, post_base + Vector((0, 0, 0.12)), body)
bpy.ops.object.mode_set(mode='OBJECT')

groups = {b.name: mesh.vertex_groups.new(name=b.name) for b in arm.bones if b.name not in ('Root', 'Body')}
for i, (p, c) in enumerate(zip(vpart, co)):
    name = {1: 'RingTop', 2: 'RingBottom', 3: 'Eye', 4: 'Sensor'}.get(int(p))
    if name is None:
        name = 'CapTop' if c[2] >= centre.z else 'CapBottom'
    groups[name].add([i], 1.0, 'REPLACE')
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
mesh.parent = rig

for name, bone_name, at in (('Socket_Eye', 'Eye', eye_front + Vector((0, -0.004, 0))),
                            ('Socket_Lens', 'Sensor', lens_point)):
    sock = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(sock)
    sock.parent = rig; sock.parent_type = 'BONE'; sock.parent_bone = bone_name
    sock.matrix_world = Matrix.Translation(at); sock.empty_display_size = 0.02
print('RIGGED bones', len(arm.bones), 'unweighted', sum(1 for v in me.vertices if not v.groups),
      'centre', tuple(round(x, 3) for x in centre), 'post', tuple(round(x, 3) for x in post_base),
      'lens', tuple(round(x, 3) for x in lens_point), 'eye', tuple(round(x, 3) for x in eye_front))
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
