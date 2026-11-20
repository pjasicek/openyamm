import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(p/'work/textured_uv.blend'));b=bpy.data.objects['Body'];r=bpy.data.objects['Rig'];staff=bpy.data.objects['StaffMesh'];sc=bpy.context.scene
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
def material(name,prefix,review=True):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=0.;bs.inputs['Roughness'].default_value=.85
 def tex(suffix,space):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(p/'textures'/(prefix+suffix+'.png')),check_existing=True);n.image.colorspace_settings.name=space;n.image.pack();return n
 base=tex('_review_a' if review and prefix!='mep_staff' else '_basecolor_1k','sRGB');nt.links.new(base.outputs['Color'],bs.inputs['Base Color']);nt.nodes.active=base
 normal=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('_normal_1k','Non-Color').outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bs.inputs['Normal'])
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('_orm_1k','Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);return mat
b.data.materials.clear()
for name,prefix in [('Mep_A','mep'),('MepHead_A','mep_head')]:b.data.materials.append(material(name,prefix))
if 'MergedUV' in b.data.uv_layers:b.data.uv_layers.remove(b.data.uv_layers['MergedUV'])
merged=b.data.uv_layers.new(name='MergedUV')
for f in b.data.polygons:
 head=bool(b.data.attributes['head'].data[f.index].value);f.material_index=int(head)
 for li in f.loop_indices:merged.data[li].uv=b.data.uv_layers['HeadUV' if head else 'UVMap'].data[li].uv
b.data.uv_layers.active=merged;merged.active_render=True;staff.data.materials.clear();staff.data.materials.append(material('MepStaff_A','mep_staff'))
# Exposed eye and palm sockets, never offset from guessed Meshy bone tails.
B=r.data.bones;pv=[v.value for v in b.data.attributes['piece'].data];sockets=[]
for sd,label,eye in [('L','Left',12),('R','Right',13)]:
 h=B[f'B_{sd}_Hand'];d=(B[f'B_{sd}_Finger2'].head_local-h.head_local).normalized();ac=B[f'B_{sd}_Finger1'].head_local-B[f'B_{sd}_Finger4'].head_local;n=d.cross(ac).normalized()
 if n.y>0:n=-n
 sockets.append(('Socket_Palm_'+label,h.head_local+d*.042+n*.022,h.name))
 vertices=[v.co for v in b.data.vertices if pv[v.index]==eye];sockets.append(('Socket_Eye_'+label,sum(vertices,Vector())/len(vertices),'B_Head'))
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT')
for name,pos,parent in sockets:
 e=r.data.edit_bones.get(name) or r.data.edit_bones.new(name);e.head=pos;e.tail=pos+Vector((0,-.02,0));e.parent=r.data.edit_bones[parent];e.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
# Re-ground the evaluated fall after twist distribution; preserve the action's body path and corpse endpoint.
a=bpy.data.actions['Death'];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];values=[]
for i in range(int(a.frame_range[1])*2+1):
 f=i/2;sc.frame_set(int(f),subframe=f%1);ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(v.co.z for v in me.vertices);ev.to_mesh_clear();values.append((f,r.pose.bones['B_Pelvis'].location.z-low))
for f,z in values:r.pose.bones['B_Pelvis'].location.z=z;r.pose.bones['B_Pelvis'].keyframe_insert('location',index=2,frame=f)
sc.frame_set(int(a.frame_range[1]));dead=bpy.data.actions['Dead'];held={pb.name:(pb.rotation_quaternion.copy(),pb.location.copy()) for pb in r.pose.bones};bpy.data.actions.remove(dead);dead=bpy.data.actions.new('Dead');dead.use_fake_user=True;r.animation_data.action=dead
for frame in [0,30]:
 for n,(q,l) in held.items():
  pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
dead.use_frame_range=True;dead.frame_start=0;dead.frame_end=30
for act in bpy.data.actions:
 for layer in act.layers:
  for strip in layer.strips:
   for cb in strip.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/textured.blend'));common.workbench_clay(sc,True);sc.view_settings.view_transform='Standard';sc.view_settings.look='None';sc.display.shading.show_specular_highlight=False
for role,frames in [('Standing',[0]),('Attack',[7,20,28,34.375]),('Cast',[22]),('Death',[50,108])]:
 a=bpy.data.actions[role];r.animation_data.action=a;r.animation_data.action_slot=a.slots[0]
 for f in frames:
  sc.frame_set(int(f),subframe=f%1);lo,hi=common.world_bounds([b,staff]);center=(lo+hi)/2;common.render_views(str(p/f'review/textured_{role}_{f}'),center.z,max(2.15,(hi-lo).length*1.05),views=('front','left','three_quarter'),resolution=(700,850),target=(center.x,center.y))
