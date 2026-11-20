"""Stress poses for the rat rig: rest with bones, stride, rear-up, tail curl, head turn, death roll.
Args: blend-relative out_prefix. Renders side + three-quarter of each pose into one sheet (system PIL)."""
import bpy, sys, os, math, json, subprocess
from mathutils import Vector, Matrix, Quaternion
args = sys.argv[sys.argv.index('--') + 1:]
out = args[0]
bpy.ops.wm.open_mainfile(filepath=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'work/rig_v1.blend'))
rig = bpy.data.objects['Rat_Rig']; mesh = bpy.data.objects['Rat']; sc = bpy.context.scene


def reset():
    for b in rig.pose.bones:
        b.rotation_mode = 'QUATERNION'; b.rotation_quaternion = (1, 0, 0, 0); b.location = (0, 0, 0)
    bpy.context.view_layer.update()


def rot(name, axis, deg):
    """Rotate a bone about a world axis through its head."""
    b = rig.pose.bones[name]; h = b.head.copy()
    R = Matrix.Translation(h) @ Matrix.Rotation(math.radians(deg), 4, Vector(axis)) @ Matrix.Translation(-h)
    b.matrix = R @ b.matrix; bpy.context.view_layer.update()


X, Y, Z = (1, 0, 0), (0, 1, 0), (0, 0, 1)
POSES = {
    'rest': [],
    'stride': [('Thigh_L', X, 35), ('Shin_L', X, -30), ('Thigh_R', X, -30), ('Shin_R', X, 25),
               ('UpperArm_L', X, -30), ('UpperArm_R', X, 30), ('ForeArm_R', X, -30), ('Spine2', X, 6)],
    'rear': [('Spine1', X, -35), ('Spine2', X, -15), ('Spine3', X, -10), ('Neck1', X, 15),
             ('UpperArm_L', X, -50), ('UpperArm_R', X, -50), ('ForeArm_L', X, 40), ('ForeArm_R', X, 40),
             ('Thigh_L', X, -30), ('Thigh_R', X, -30)],
    'tail_head': [('Jaw', X, 28), ('Tail1', X, -30), ('Tail2', Z, 25), ('Tail3', Z, 25), ('Tail4', Z, 25), ('Tail5', Z, 25),
                  ('Neck1', Z, 30), ('Head', X, 25), ('Spine2', Z, 10), ('Spine3', Z, 10)],
    'death_roll': [('Spine1', Y, 80), ('UpperArm_L', X, 40), ('UpperArm_R', X, -40), ('Thigh_L', X, 40),
                   ('Thigh_R', X, -20), ('Neck1', Y, 20), ('Tail2', Z, 30)],
}
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_rat as C
cells = []
for name, ops in POSES.items():
    reset()
    for b, ax, deg in ops:
        rot(b, ax, deg)
    for view, loc in (('side', (-1.6, 0.0, 0.2)), ('q', (-1.0, -1.1, 0.6))):
        path = f'{out}_{name}_{view}.png'
        C.render_ortho(loc, (0, 0.0, 0.12), 1.2, path, bones=(name == 'rest'))
        cells.append(path)
compose = """
import sys
from PIL import Image
paths = sys.argv[2:]; out = sys.argv[1]
ims = [Image.open(p) for p in paths]; w, h = ims[0].size
o = Image.new('RGB', (w * 2, h * (len(ims) // 2)))
for i, im in enumerate(ims): o.paste(im, ((i % 2) * w, (i // 2) * h))
o.save(out)
"""
subprocess.run(['/usr/bin/python3', '-c', compose, out + '_sheet.png'] + cells, check=True)
print('SHEET', out + '_sheet.png')
