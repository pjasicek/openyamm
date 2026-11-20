"""Dump a library locomotion clip (Mixamo FBX or humanoid-set FBX) as joint world positions and rotations per frame.

Blender, background: -- <out.npz> <fbx> [<fbx> ...] (one npz per fbx: <out dir>/<slug>.npz when several are given).
Coordinates are converted to the GLB convention (glTF: +Y up; Blender (x, y, z) -> (x, z, -y)). Canonical joint names
(Mixamo names without prefix): Hips, Spine, Spine1, Spine2, Neck, Head, {Left,Right}{UpLeg,Leg,Foot,ToeBase,ToeEnd}.
The humanoid set's B_* names are mapped onto them; its Motion root bone (root-motion travel) is simply part of the
world transform, so travel stays in the hips path (the analysis works relative to the hips).
"""
import bpy
import math
import os
import sys

import numpy as np
from mathutils import Matrix

args = sys.argv[sys.argv.index('--') + 1:]
out, fbxs = args[0], args[1:]
SET = {'B_Pelvis': 'Hips', 'B_Spine': 'Spine', 'B_Spine1': 'Spine1', 'B_Spine2': 'Spine2', 'B_Neck': 'Neck',
       'B_Head': 'Head'}
for s, side in (('L', 'Left'), ('R', 'Right')):
    SET.update({f'B_{s}_Thigh': f'{side}UpLeg', f'B_{s}_Calf': f'{side}Leg', f'B_{s}_Foot': f'{side}Foot',
                f'B_{s}_Toe0': f'{side}ToeBase', f'B_{s}_Clavicle': f'{side}Shoulder',
                f'B_{s}_UpperArm': f'{side}Arm', f'B_{s}_Forearm': f'{side}ForeArm', f'B_{s}_Hand': f'{side}Hand'})
CANON = ['Hips', 'Spine', 'Spine1', 'Spine2', 'Neck', 'Head']
for side in ('Left', 'Right'):
    CANON += [f'{side}{b}' for b in ('UpLeg', 'Leg', 'Foot', 'ToeBase', 'Shoulder', 'Arm', 'ForeArm', 'Hand')]
CONVERT = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))   # Blender -> glTF axes


def canonical(name):
    if name in SET:
        return SET[name]
    return name.split(':')[-1]


def dump(fbx, path):
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    for act in list(bpy.data.actions):
        bpy.data.actions.remove(act)
    bpy.ops.import_scene.fbx(filepath=os.path.abspath(fbx))
    scene = bpy.context.scene
    fps = scene.render.fps / scene.render.fps_base
    arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    bones = {canonical(b.name): b.name for b in arm.data.bones}
    missing = [c for c in CANON if c not in bones]
    if missing:
        raise SystemExit(f'{fbx}: missing {missing}')
    act = arm.animation_data.action
    f0, f1 = (int(round(v)) for v in act.frame_range)
    # toe end: the ToeBase bone tail (Mixamo has ToeBase -> Toe_End; the set's Toe0 tail)
    W = CONVERT @ arm.matrix_world
    arm.animation_data.action = None
    for pb in arm.pose.bones:
        pb.matrix_basis = Matrix()
    bpy.context.view_layer.update()
    rest = {}
    for c in CANON:
        pb = arm.pose.bones[bones[c]]
        rest[c] = np.array(W @ pb.matrix)
    rest_tail = {side: np.array(W @ arm.pose.bones[bones[f'{side}ToeBase']].tail) for side in ('Left', 'Right')}
    arm.animation_data.action = act
    frames = list(range(f0, f1 + 1))
    mats = np.zeros((len(frames), len(CANON), 4, 4))
    tails = np.zeros((len(frames), 2, 3))
    for i, f in enumerate(frames):
        scene.frame_set(f)
        for j, c in enumerate(CANON):
            mats[i, j] = np.array(W @ arm.pose.bones[bones[c]].matrix)
        for j, side in enumerate(('Left', 'Right')):
            tails[i, j] = np.array(W @ arm.pose.bones[bones[f'{side}ToeBase']].tail)
    # world matrices carry the armature's import scale (Mixamo FBX: 0.01); positions are in metres
    np.savez(path, names=np.array(CANON), mats=mats, toe_tails=tails, fps=fps, frames=np.array(frames),
             rest=np.stack([rest[c] for c in CANON]), rest_toe_tails=np.stack([rest_tail['Left'], rest_tail['Right']]),
             source=os.path.relpath(os.path.abspath(fbx)))
    print(f'EXTRACT {os.path.basename(fbx)}: {len(frames)} frames at {fps:g} fps -> {path}')


for fbx in fbxs:
    if len(fbxs) == 1 and out.endswith('.npz'):
        target = out
    else:
        slug = ''.join(ch if ch.isalnum() else '_' for ch in os.path.splitext(os.path.basename(fbx))[0]).strip('_')
        target = os.path.join(out, slug + '.npz')
    dump(fbx, target)
