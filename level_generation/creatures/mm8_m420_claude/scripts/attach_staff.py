import bpy,sys,json
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/actions_twist.blend'));rig=bpy.data.objects['Rig']
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];bpy.context.scene.frame_set(0)
Hpose=rig.pose.bones['B_R_Hand'].matrix.copy();G=json.loads((P/'work/grip_pose.json').read_text());axis=Vector(G['handle_axis_hand_local']).normalized()
y=Hpose.to_3x3().inverted()@Vector((0,1,0));y=(y-axis*y.dot(axis)).normalized();x=y.cross(axis).normalized()
local=Matrix((x,y,axis)).transposed().to_4x4();local.translation=Vector(G['handle_centre_hand_local'])
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis=Matrix()
bpy.context.view_layer.update();T=rig.data.bones['B_R_Hand'].matrix_local@local
with bpy.data.libraries.load(str(P/'work/staff_final_geometry.blend'),link=False) as (src,dst):dst.objects=['StaffMesh']
o=dst.objects[0];bpy.context.collection.objects.link(o)
for v in o.data.vertices:v.co=T@v.co
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Staff');b.head=T.translation;b.tail=T@Vector((0,0,.2));b.parent=rig.data.edit_bones['B_R_Hand'];b.align_roll(T.to_3x3().col[1])
s=rig.data.edit_bones.new('Socket_Staff');s.head=T@Vector((0,-.045,.4968));s.tail=s.head+T.to_3x3()@Vector((0,-.06,0));s.parent=b;s.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
o.vertex_groups.new(name='Staff').add(list(range(len(o.data.vertices))),1,'REPLACE');mod=o.modifiers.new('Rig','ARMATURE');mod.object=rig
(P/'work/staff_transform.json').write_text(json.dumps({'matrix':list(map(list,T)),'socket_local_staff':[0,-.045,.4968]},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'))
