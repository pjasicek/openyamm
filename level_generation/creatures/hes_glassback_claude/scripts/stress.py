"""Stress poses on the rig (before clips): rest with bones, legs stepping (front forward, hind back, middle lifted),
spine bend + head turn + tail curl, body roll, a lifted foot per pair. Renders work/stress_*.png. Args: -- <blend>"""
import bpy, os, sys, math
from mathutils import Vector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common as C
import posing as P
src = sys.argv[sys.argv.index('--') + 1:][0]
bpy.ops.wm.open_mainfile(filepath=C.path(src))
rig = bpy.data.objects[C.RIG]
P.reset(rig)
REST = {b.name: (rig.matrix_world @ b.matrix).copy() for b in rig.pose.bones}
cams = {'side': ((5, -0.2, 0.6), (0, -0.2, 0.6)), 'quarter': ((3.5, -3.5, 2.2), (0, 0, 0.5)),
        'front': ((0.0, -5, 0.6), (0, 0, 0.6))}


def shots(tag, bones=False):
    for n, (loc, tgt) in cams.items():
        C.render_ortho(loc, tgt, 3.6, C.path(f'work/stress_{tag}_{n}.png'), show=[C.MESH], res=(800, 560), bones=bones)


shots('rest', bones=True)
P.reset(rig)
for leg, dy, dz in (('FL', -0.25, 0.15), ('FR', 0.15, 0.0), ('ML', 0.0, 0.25), ('MR', -0.2, 0.0), ('HL', 0.2, 0.0),
                    ('HR', -0.15, 0.2)):
    ank = REST[f'Foot_{leg}'].translation
    tgt = ank + Vector((0, dy, dz))
    pole = tgt + Vector((0, 0.5 if leg[0] in 'FM' else -0.5, 0.1))
    P.two_bone_ik(rig, f'Upper_{leg}', f'Lower_{leg}', tgt, pole)
shots('stride')
P.reset(rig)
for n, deg in (('Spine2', 8), ('Spine3', 8)):
    P.rotate_world(rig, n, 'Z', deg)
P.rotate_world(rig, 'Neck1', 'Z', 15); P.rotate_world(rig, 'Head', 'Z', 15); P.rotate_world(rig, 'Head', 'X', -20)
for i in (1, 2, 3):
    P.rotate_world(rig, f'Tail{i}', 'Z', -15)
shots('bend')
P.reset(rig)
P.rotate_world(rig, 'Spine1', 'Y', 80, pivot=Vector((0, 0, 0)))
shots('roll')
