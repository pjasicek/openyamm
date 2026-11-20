"""World-space transform helpers for the fitted m488 rig."""
import bpy
def W(rig, n):
    return rig.matrix_world @ rig.pose.bones[n].matrix


def set_world(rig, n, M):
    rig.pose.bones[n].matrix = rig.matrix_world.inverted() @ M
    bpy.context.view_layer.update()


def rot_world(M, R3):
    """M (4x4 world) with its rotation replaced by R3 (3x3), translation kept."""
    out = R3.to_4x4(); out.translation = M.translation.copy(); return out

