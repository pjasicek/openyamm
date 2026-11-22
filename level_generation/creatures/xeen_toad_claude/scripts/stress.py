"""Extreme poses on work/rig_v1.blend before animating: rest with bones, hop (hind legs extended back, front up),
leap (front legs raised and spread, as the native leap frame), roll onto the back, head up + throat puff + tongue out.
Writes review/stress_<pose>.png (quarter and side)."""
import bpy, os, sys, math
from mathutils import Vector, Matrix
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C, posing as P
HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
bpy.ops.wm.open_mainfile(filepath=os.path.join(HERE, 'work', 'rig_v1.blend'))
rig = bpy.data.objects['Toad_Rig']; pb = rig.pose.bones
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def tongue(scale):
    pb['Tongue1'].scale = (scale,) * 3; bpy.context.view_layer.update()


def shoot(name, cams):
    for cname, (loc, tgt) in cams.items():
        C.render(loc, tgt, 2.6, os.path.join(HERE, 'review', f'stress_{name}_{cname}.png'), res=(700, 560))


CAMS = {'quarter': ((-2.4, -3.0, 1.6), (0, 0, 0.35)), 'side': ((4, 0, 0.5), (0, 0, 0.45))}
P.reset(rig); tongue(0.02); shoot('rest', CAMS)
P.reset(rig); tongue(0.02)
pb['Body'].location = (0, 0, 0)
P.rotate_world(rig, 'Body', X, 25)                       # front up
for s, sg in (('L', 1), ('R', -1)):
    P.rotate_world(rig, f'Thigh_{s}', Z, -sg * 35); P.rotate_world(rig, f'Thigh_{s}', X, 30)
    P.rotate_world(rig, f'Shin_{s}', X, -80)
shoot('hop', CAMS)
P.reset(rig); tongue(0.02)
for s, sg in (('L', 1), ('R', -1)):
    P.rotate_world(rig, f'UpperArm_{s}', Y, -sg * 60)
    P.rotate_world(rig, f'ForeArm_{s}', Y, -sg * 30)
P.rotate_world(rig, 'Chest', X, 20)
shoot('leap', CAMS)
P.reset(rig); tongue(0.02)
root = pb['Body']
P.rotate_world(rig, 'Body', Y, 180, pivot=Vector((0, 0.1, 0.45)))
for s in 'LR':
    P.rotate_world(rig, f'Thigh_{s}', X, 30)
shoot('roll', CAMS)
P.reset(rig); tongue(1.0)
P.rotate_world(rig, 'Head', X, 12)
pb['Throat'].scale = (1.5, 1.5, 1.5); bpy.context.view_layer.update()
shoot('tongue', CAMS)
