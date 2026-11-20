"""MM9 HIGHWAYMAN mitten frame per hand on the fitted rig: finger direction (Hand -> Finger1), palm normal (where the Finger1 tail moves when
Hattack1's sword-fist rotation of Finger1 at frame 13 is applied to the finger bones only), thumb joint. Args: <rig blend>"""
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
rest = {S: (H(f'Bip01 {S} Hand'), H(f'Bip01 {S} Finger1'), T(f'Bip01 {S} Finger1'), H(f'Bip01 {S} Finger02')) for S in 'RL'}
print('ACTIONS', [a.name for a in bpy.data.actions][:30])
act = next(a for a in bpy.data.actions if a.name.startswith('Hattack1'))
rig.animation_data.action = act
for fr in (1, 13):
    sc.frame_set(fr)
    q = {pb.name: pb.matrix_basis.copy() for pb in rig.pose.bones}
    for pb in rig.pose.bones:
        pb.matrix_basis = q[pb.name] if 'Finger' in pb.name else pb.matrix_basis.__class__.Identity(4)
    rig.animation_data.action = None
    bpy.context.view_layer.update()
    for S in 'RL':
        h, f1, tip, f0 = rest[S]
        hd = (f1 - h) / np.linalg.norm(f1 - h)
        mv = T(f'Bip01 {S} Finger1') - tip; mv -= hd * (mv @ hd)
        n = mv / max(np.linalg.norm(mv), 1e-9)
        print('MITTEN', fr, S, 'hd', hd.round(3).tolist(), 'palm', n.round(3).tolist(), 'move', round(float(np.linalg.norm(mv)), 4), 'thumb', (f0 - h).round(3).tolist())
    rig.animation_data.action = act
