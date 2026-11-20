import bpy,numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/prop_fixed.blend'));r=bpy.data.objects['Rig'];o=bpy.data.objects['ClubMesh'];s=bpy.context.scene;a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];s.frame_set(0);b=r.pose.bones['Club'];print('OBJ',o.matrix_world,'ARM',r.matrix_world,'mod',[(m.name,m.type,getattr(m,'object',None))for m in o.modifiers]);print('matrix',b.matrix,'loc',b.location,'scale',b.scale)
M=b.matrix.copy();M.translation+=Vector((-1,0,1));b.matrix=M;print('SET',b.location,'matrix',b.matrix,'target',M);bpy.context.view_layer.update();print('UPDATED',b.location,'matrix',b.matrix)
b.keyframe_insert('location',frame=0);b.keyframe_insert('rotation_quaternion',frame=0);s.frame_set(1);s.frame_set(0);print('READBACK',b.location,'matrix',b.matrix)
for fc in a.layers[0].strips[0].channelbag(a.slots[0]).fcurves:
 if 'Club'in fc.data_path:print(fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation)for k in list(fc.keyframe_points)[:6]])
