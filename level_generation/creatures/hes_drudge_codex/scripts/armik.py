"""World-space pose helpers used by the shared run fitter."""
import bpy
def W(rig,n): return rig.matrix_world @ rig.pose.bones[n].matrix
def set_world(rig,n,matrix):
    rig.pose.bones[n].matrix=rig.matrix_world.inverted() @ matrix
    bpy.context.view_layer.update()
def rot_world(matrix,rotation):
    result=rotation.to_4x4();result.translation=matrix.translation.copy();return result
