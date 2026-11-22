"""Pose helper (Blender): the titan in its sleeping pose. pose(cfg) imports the source, applies the base frame and
the world-axis bone rotations (in order, each about the bone's current head) and returns (arm, body). Rotations: [bone, X|Y|Z, degrees], [bone, AIM, [x, y, z]] or [bone, TWIST, degrees]. laid(mesh)
turns a baked standing mesh onto its back: body up -> -X (head at the -X end), body front (-Y) -> +Z, so the titan's
left side lies toward +Y (away from the front)."""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import posing  # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
LAY = Matrix(((0, 0, -1, 0), (1, 0, 0, 0), (0, -1, 0, 0), (0, 0, 0, 1)))


def pose(cfg, keep_all_meshes=False):
    path = os.path.join(REPO, cfg['source'])
    if keep_all_meshes:
        path = os.path.join(REPO, cfg['source_lods'])
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.gltf(filepath=path)
        arm = next(o for o in bpy.context.scene.objects if o.type == 'ARMATURE')
        if arm.animation_data is None:
            arm.animation_data_create()
        body = None
    else:
        arm, body = posing.import_creature(path)
    posing.apply_pose(arm, {'base': cfg['base']})
    for bone, axis, val in cfg['world_rotations']:
        pb = arm.pose.bones[bone]
        head = pb.head.copy()
        if axis == 'AIM':        # swing the bone so it points along a world direction
            rot = (pb.tail - pb.head).normalized().rotation_difference(Vector(val).normalized()).to_matrix().to_4x4()
        elif axis == 'TWIST':    # turn the bone about its own length
            rot = Matrix.Rotation(math.radians(val), 4, (pb.tail - pb.head).normalized())
        else:
            rot = Matrix.Rotation(math.radians(val), 4, axis)
        pb.matrix = Matrix.Translation(head) @ rot @ Matrix.Translation(-head) @ pb.matrix
        bpy.context.view_layer.update()
    return arm, body
