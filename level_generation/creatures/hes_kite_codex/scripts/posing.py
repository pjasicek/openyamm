"""World-axis posing for the project-local flyer rig."""
import math
import bpy
from mathutils import Matrix, Vector


def reset(rig):
    for b in rig.pose.bones:
        b.rotation_mode='QUATERNION'; b.matrix_basis.identity()
    bpy.context.view_layer.update()


def rotate(rig,name,axis,degrees):
    b=rig.pose.bones[name];h=b.head.copy()
    b.matrix=Matrix.Translation(h)@Matrix.Rotation(math.radians(degrees),4,axis)@Matrix.Translation(-h)@b.matrix
    bpy.context.view_layer.update()


def translate(rig,delta):
    b=rig.pose.bones['Spine1'];b.matrix=Matrix.Translation(Vector(delta))@b.matrix
    bpy.context.view_layer.update()


def wing(rig,pair,side,up,elbow=0,fold=0,curl=0):
    s=1 if side=='L' else -1;n=pair+'_'+side
    rotate(rig,n+'_Upper','Y',-s*up)
    rotate(rig,n+'_Fore','Y',-s*elbow)
    rotate(rig,n+'_Fore','Z',s*fold)
    for k in range(1,4):rotate(rig,n+'_Finger'+str(k),'Y',s*curl)


def coordinates(mesh):
    import numpy as np
    ev=mesh.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh()
    c=np.empty(len(me.vertices)*3);me.vertices.foreach_get('co',c);ev.to_mesh_clear()
    return c.reshape(-1,3)
