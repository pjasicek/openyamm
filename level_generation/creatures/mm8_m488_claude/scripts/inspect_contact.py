from pathlib import Path
import bpy,sys,json
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/cage.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];act=bpy.data.actions['Running'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];bpy.context.scene.frame_set(20)
em=body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
for i in (8614,4789,5603,6197):
 v=body.data.vertices[i];print('CONTACT',i,'rest',v.co[:],'posed',em.vertices[i].co[:],'weights',[(body.vertex_groups[g.group].name,round(g.weight,3)) for g in v.groups])
for n in ('B_Pelvis','B_R_Thigh','B_Wrap_Right','B_L_Thigh'):
 b=rig.pose.bones[n];print('BONE',n,'rest',b.bone.head_local[:],b.bone.tail_local[:],'pose',b.head[:],b.tail[:], 'delta', (b.matrix@b.bone.matrix_local.inverted()).to_quaternion()[:])
common.workbench_clay(bpy.context.scene);common.render_views(str(p/'review/animation/wrap_probe'),1.05,2.5,views=('front','right','back','three_quarter'),resolution=(768,768))
