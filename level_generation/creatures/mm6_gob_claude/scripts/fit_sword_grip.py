"""Seat the sword grip inside the closed right fist (after refit_hands.py).

Curls the right hand to the authoring grip (curl/thumb as used by the clips), fits a circle through each curled
finger's joints, and moves the sword's rest geometry + Sword bone rigidly so the grip axis runs through the finger
loop centres (blade out of the thumb/index side, cutting edge toward the knuckles). Updates scene['pfem_sword'].
Args: curl thumb [slant_deg]: slant tilts the blade toward the knuckles (diagonal hammer grip across the palm).
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import posing as P

args = sys.argv[sys.argv.index('--') + 1:]
curl, thumb = float(args[0]), float(args[1])
slant = math.radians(float(args[2])) if len(args) > 2 else 0.0
rig = bpy.data.objects['Peasant_Rig']; mesh = bpy.data.objects['Peasant']; me = mesh.data
if rig.animation_data:
    rig.animation_data.action = None
P.reset(rig)
P.curl_hand(rig, 'Right', curl, thumb=thumb)


def circle_centre(a, b, c):
    a, b, c = (np.array(x) for x in (a, b, c))
    ab, ac = b - a, c - a
    n = np.cross(ab, ac)
    centre = a + (np.cross(n, ab) * (ac @ ac) + np.cross(ac, n) * (ab @ ab)) / (2 * (n @ n))
    return centre, np.linalg.norm(centre - a)


centres = []
for name in ('Index', 'Middle', 'Ring'):
    j = [P.bone_world(rig, f'RightHand{name}{k}') for k in (1, 2, 3)] + [P.bone_world(rig, f'RightHand{name}3', tail=True)]
    c, r = circle_centre(j[1], j[2], j[3])
    centres.append(c)
    print('LOOP', name, np.round(c, 3), 'radius', round(r, 4))
centres = np.array(centres)
c = Vector(centres.mean(0))
b = Vector(centres[0] - centres[-1]).normalized()                 # ring -> index: blade exits on the thumb side
hand = P.pb(rig, 'RightHand')
hand_axis = (P.bone_world(rig, 'RightHandMiddle1') - P.bone_world(rig, 'RightHand')).normalized()
w = (hand_axis - b * hand_axis.dot(b)).normalized()             # cutting edge toward the knuckles
b, w = (b * math.cos(slant) + w * math.sin(slant)).normalized(), (w * math.cos(slant) - b * math.sin(slant)).normalized()
print('BLADE vs hand axis deg', round(math.degrees(b.angle(hand_axis)), 1))
prop = json.loads(bpy.context.scene['pfem_sword'])
g0 = Vector(prop['grip']); b0 = Vector(prop['blade_dir']).normalized()
PARTS = json.loads(bpy.context.scene['pfem_parts'])
part = np.zeros(len(me.polygons), dtype=np.int32); me.attributes['part'].data.foreach_get('value', part)
sword_v = sorted({v for p in me.polygons if part[p.index] == PARTS.index('Sword') for v in p.vertices})
co = [mesh.matrix_world @ me.vertices[i].co for i in sword_v]
tip = max(co, key=lambda x: (x - g0).dot(b0))
off = (tip - g0) - b0 * (tip - g0).dot(b0)
w0 = (-off).normalized()                                          # the blade curves toward its spine (away from edge)


def frame(x, y):
    x = x.normalized(); y = (y - x * y.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


R = frame(b, w) @ frame(b0, w0).inverted()
K = Matrix.Translation(c) @ R.to_4x4() @ Matrix.Translation(-g0)
P.reset(rig)
mi = mesh.matrix_world.inverted()
for i, x in zip(sword_v, co):
    me.vertices[i].co = mi @ (K @ x)
me.update()
bpy.context.view_layer.objects.active = rig
for o in bpy.data.objects:
    o.select_set(o == rig)
bpy.ops.object.mode_set(mode='EDIT')
eb = rig.data.edit_bones['Sword']
inv = rig.matrix_world.inverted(); mw = rig.matrix_world
z_old = mw.to_3x3() @ eb.z_axis
eb.head = inv @ (K @ (mw @ eb.head)); eb.tail = inv @ (K @ (mw @ eb.tail))
eb.align_roll(inv.to_3x3() @ (R @ z_old))
bpy.ops.object.mode_set(mode='OBJECT')
prop['grip'] = list(c); prop['blade_dir'] = list(b); prop['palm_normal'] = list((R @ Vector(prop['palm_normal'])).normalized())
bpy.context.scene['pfem_sword'] = json.dumps(prop)
print('GRIP', 'centre', np.round(np.array(c), 3), 'blade', np.round(np.array(b), 3), 'moved', round((c - g0).length, 3))
bpy.ops.wm.save_mainfile()
