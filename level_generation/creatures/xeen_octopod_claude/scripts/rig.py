"""Rig the octopod (work/clean_v1.blend + work/rig_v1.json from joints.py) -> work/rig_v1.blend.
Bones (forward -Y, z 0 = the waterline):
  Root (origin, the waterline; Death sinks it) > Body (hub at the head base: bob and tilt of the whole creature)
    > Head (the dome, eyes, brow and beard above the web)
      > Socket_Siphon (non-deform, at the beard: the ink spray's glow)
    > Arm<k>_1..8 for the eight tentacles k = 0..7 (azimuth 45k degrees from the front, + toward +X = the creature's
      left), joints along each traced centreline; every bone's local X is its tentacle's plane normal
  FoamRoot (unparented, at the origin: the foam ring stays on the water whatever the body does).
Weights from rig_v1.json (tentacle chains by arc position with hat blends, web eased into Body/Head, suckers rigid on
their body point, eyes on Head). Vertex groups by bone name; armature modifier; 0 unweighted vertices required."""
import bpy, os, sys, json, math
from mathutils import Vector, Matrix
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'clean_v1.blend'))
RJ = json.load(open(os.path.join(HERE, 'work', 'rig_v1.json')))
mesh = bpy.data.objects['Octopod']
arm_data = bpy.data.armatures.new('Octopod_Rig')
rig = bpy.data.objects.new('Octopod_Rig', arm_data)
bpy.context.scene.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones


def bone(name, head, tail, parent=None, deform=True, xaxis=None):
    b = eb.new(name); b.head = Vector(head); b.tail = Vector(tail); b.use_deform = deform
    if parent:
        b.parent = eb[parent]; b.use_connect = False
    if xaxis is not None:
        y = (b.tail - b.head).normalized()
        x = Vector(xaxis); x = (x - y * x.dot(y)).normalized()
        z = x.cross(y)
        b.align_roll(z)
    return b


bone('Root', (0, 0, 0), (0, 0, 0.12))
bone('Body', (0, 0, 0.05), (0, 0, 0.18), 'Root')
bone('Head', (0, 0, 0.18), (0, 0, 0.47), 'Body')
# the beard's front, a little above the water: the ink spray leaves here
co = [v.co for v in mesh.data.vertices]
front = min((c for c in co if abs(c.x) < 0.03 and 0.03 < c.z < 0.12 and c.y < 0 and math.hypot(c.x, c.y) < 0.4),
            key=lambda c: c.y)
sock = Vector((0, front.y - 0.02, front.z))
bone('Socket_Siphon', sock, sock + Vector((0, -0.04, 0)), 'Head', deform=False)
for A in RJ['arms']:
    k = A['k']; th = math.radians(A['azimuth_deg'])
    n = Vector((math.cos(th), math.sin(th), 0))
    J = A['joints']
    for i in range(RJ['n_seg']):
        bone(f'Arm{k}_{i + 1}', J[i], J[i + 1], 'Body' if i == 0 else f'Arm{k}_{i}', xaxis=n)
bone('FoamRoot', (0, 0, 0), (0, 0.1, 0))
bpy.ops.object.mode_set(mode='OBJECT')
print('SOCKET siphon', [round(x, 3) for x in sock])

mesh.vertex_groups.clear()
groups = {}
for v, ws in enumerate(RJ['weights']):
    for name, w in ws:
        g = groups.get(name) or mesh.vertex_groups.new(name=name); groups[name] = g
        g.add([v], w, 'REPLACE')
for name in RJ['bones']:
    if name not in groups:
        groups[name] = mesh.vertex_groups.new(name=name)
mesh.vertex_groups.new(name='FoamRoot')
mesh.parent = rig
mod = mesh.modifiers.new('Armature', 'ARMATURE'); mod.object = rig
unw = sum(1 for v in mesh.data.vertices if not v.groups)
print('RIG bones', len(arm_data.bones), 'groups', len(mesh.vertex_groups), 'unweighted', unw)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
print('SAVED rig_v1.blend')
