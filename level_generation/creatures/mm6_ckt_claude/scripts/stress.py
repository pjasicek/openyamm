"""Extreme poses to look for tearing: wings up / down / folded, legs crouched and stepping, tail curled, neck
turned. Args: out_png"""
import bpy, sys, os, subprocess
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common_ckt as C
import posing as P
from mathutils import Vector
out = sys.argv[sys.argv.index('--') + 1]
rig = bpy.data.objects['Ckt_Rig']
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def pose(name):
    P.reset(rig)
    for s, g in (('L', 1), ('R', -1)):
        if name == 'wings_up':
            P.rotate_world(rig, f'UpperArm_{s}', Y, -g * 45)
        if name == 'wings_down':
            P.rotate_world(rig, f'UpperArm_{s}', Y, g * 50); P.rotate_world(rig, f'ForeArm_{s}', Y, g * 20)
        if name == 'wings_fold':
            P.rotate_world(rig, f'UpperArm_{s}', Z, -g * 50)
            for k in (1, 2, 3):
                P.rotate_world(rig, f'Finger{k}a_{s}', Z, -g * 60)
        if name == 'legs':
            P.rotate_world(rig, f'Thigh_{s}', X, 35 if s == 'L' else -30)
            P.rotate_world(rig, f'Shin_{s}', X, -40 if s == 'L' else 20)
    if name == 'tail_neck':
        for i in range(1, 9):
            P.rotate_world(rig, f'Tail{i}', Z, 12)
            P.rotate_world(rig, f'Tail{i}', X, 4)
        P.rotate_world(rig, 'Neck1', Z, 30); P.rotate_world(rig, 'Neck2', Z, 25); P.rotate_world(rig, 'Head', X, -25)


cells = []
for name in ('wings_up', 'wings_down', 'wings_fold', 'legs', 'tail_neck'):
    pose(name)
    for view, loc in (('f', (0, -4, 0.2)), ('q', (-2.6, -2.6, 1.6))):
        p = out.replace('.png', f'_{name}_{view}.png')
        C.render_ortho(loc, (0, 0, 0.2), 1.2, p, res=(400, 400)); cells.append(p)
subprocess.run(['/usr/bin/python3', '-c', """
import sys
from PIL import Image
ims=[Image.open(p) for p in sys.argv[2:]]; o=Image.new('RGB',(400*5,800))
[o.paste(im,((i//2)*400,(i%2)*400)) for i,im in enumerate(ims)]; o.save(sys.argv[1])
""", out] + cells, check=True)
for p in cells: os.remove(p)
