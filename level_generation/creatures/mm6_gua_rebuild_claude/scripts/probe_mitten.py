"""MM9 mitten frame per hand on the fitted rig: finger direction (Hand -> Finger1), palm normal (where Finger12 moves when the
fist of Hattack1 frame 13 is applied to the finger bones only), thumb side. Args: <rig blend>"""
import bpy, sys
import numpy as np
bpy.ops.wm.open_mainfile(filepath=sys.argv[sys.argv.index('--') + 1])
rig = bpy.data.objects['MM9_Rig']
sc = bpy.context.scene
def H(n): return np.array(tuple(rig.matrix_world @ rig.pose.bones[n].head))
def T(n): return np.array(tuple(rig.matrix_world @ rig.pose.bones[n].tail))
rig.animation_data_create(); rig.animation_data.action = None
for pb in rig.pose.bones: pb.matrix_basis.identity()
bpy.context.view_layer.update()
rest = {S: (H(f'Bip01 {S} Hand'), H(f'Bip01 {S} Finger1'), H(f'Bip01 {S} Finger12'), T(f'Bip01 {S} Finger12'), H(f'Bip01 {S} Finger0')) for S in 'RL'}
act = bpy.data.actions['Hattack1']
rig.animation_data.action = act; sc.frame_set(13)
q = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
rig.animation_data.action = None
for pb in rig.pose.bones:
    pb.matrix_basis = q[pb.name] if 'Finger' in pb.name else pb.matrix_basis.__class__.Identity(4)
bpy.context.view_layer.update()
for S in 'RL':
    h, f1, f12, tip, f0 = rest[S]
    hd = (f1 - h) / np.linalg.norm(f1 - h)
    mv = T(f'Bip01 {S} Finger12') - tip; mv -= hd * (mv @ hd)
    n = mv / np.linalg.norm(mv)
    print('MITTEN', S, 'hd', hd.round(3).tolist(), 'palm', n.round(3).tolist(), 'thumb', ((f0 - h)).round(3).tolist(), 'len', round(float(np.linalg.norm(tip - h)), 3))

from mathutils import Euler
for ax in range(3):
    for S in 'RL':
        for pb in rig.pose.bones: pb.matrix_basis.identity()
        for n in ('Finger1', 'Finger11', 'Finger12'):
            pb = rig.pose.bones[f'Bip01 {S} {n}']; pb.rotation_mode = 'XYZ'; e = [0, 0, 0]; e[ax] = 0.6; pb.rotation_euler = e
        bpy.context.view_layer.update()
        h, f1, f12, tip, f0 = rest[S]; hd = (f1 - h) / np.linalg.norm(f1 - h)
        mv = T(f'Bip01 {S} Finger12') - tip; mv -= hd * (mv @ hd)
        print('AXIS', ax, S, (mv / np.linalg.norm(mv)).round(3).tolist())
