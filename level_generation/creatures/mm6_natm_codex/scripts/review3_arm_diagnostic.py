import bpy,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import reduction_common as C
bpy.ops.wm.open_mainfile(filepath=str(P/'work/runtime_lod0.blend'));r=bpy.data.objects['Rig'];import arm_ik as IK
for f in [21,34,43,55]:
 C.activate('Attack',f/48)
 for sd in 'LR':
  side=IK.Side(sd);h=r.pose.bones[f'B_{sd}_Hand'];fore=r.pose.bones[f'B_{sd}_Forearm'];axis=(sum((r.data.bones[f'B_{sd}_Finger{i}'].head_local for i in range(5)),Vector())/5-h.bone.head_local).normalized();axis=h.bone.matrix_local.to_3x3().inverted()@axis;rel=(fore.matrix.to_3x3()@side.rel['Hand']).inverted()@h.matrix.to_3x3();print('ACTUAL',f,sd,IK.swing_twist_deg(rel.to_quaternion(),axis),flush=True)
print('OBJECT',r.matrix_world,flush=True)
