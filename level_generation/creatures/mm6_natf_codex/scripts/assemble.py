import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/textured_master.blend'));body=bpy.data.objects['Body'];rig=bpy.data.objects['Rig'];sc=bpy.context.scene
with bpy.data.libraries.load(str(P/'work/props.blend'))as(src,dst):dst.objects=['ForearmBlade','LeafShield']
props=dst.objects
for ob in props:sc.collection.objects.link(ob);ob.hide_render=False
blade,shield=[bpy.data.objects[n]for n in ['ForearmBlade','LeafShield']]
def material(name,tag):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(suffix,space):
  pref=f'natf_{tag}'if tag in ['body','head','shield']else tag;n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(P/f'textures/{pref}_{suffix}'));n.image.colorspace_settings.name=space;return n
 nt.links.new(tex('basecolor_1k.png','sRGB').outputs['Color'],bs.inputs['Base Color']);sp=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex('metal_rough_1k.png','Non-Color').outputs['Color'],sp.inputs['Color']);nt.links.new(sp.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sp.outputs['Blue'],bs.inputs['Metallic'])
 if tag in ['body','head']:
  nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex('normal_1k.png','Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal'])
 return mat
body.data.materials.clear();body.data.materials.append(material('Natf_A','body'));body.data.materials.append(material('NatfHead_A','head'));me=body.data
for f in me.polygons:
 f.material_index=me.attributes['head'].data[f.index].value
 if f.material_index:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
me.uv_layers.active=me.uv_layers['UVMap'];me.uv_layers['UVMap'].active_render=True
for o,tag in [(blade,'blade'),(shield,'shield')]:o.data.materials.clear();o.data.materials.append(material(o.name+'_A',tag))
act=bpy.data.actions['Standing'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(0)
g=json.loads((P/'work/shield_grip.json').read_text());hf=json.loads((P/'work/hand_frames.json').read_text());H=rig.pose.bones['B_L_Hand'].matrix.copy();C=H@Vector(g['handle_centre_hand_local']);X=(H.to_3x3()@Vector(g['handle_axis_hand_local'])).normalized();n=(H.to_3x3()@Vector(hf['L']['palm_local'])).normalized();n=(n-X*n.dot(X)).normalized();Z=-X.cross(n)
if Z.z<0:X=-X;Z=-Z
M=Matrix((X,-n,Z)).transposed().to_4x4();M.translation=C+n*.045-Z*.26;shieldM=rig.data.bones['B_L_Hand'].matrix_local@H.inverted()@M
E=rig.data.bones['B_R_Forearm'].head_local;W=rig.data.bones['B_R_Hand'].head_local;Z=(W-E).normalized();X=Vector((-1,0,0));X=(X-Z*X.dot(Z)).normalized();Y=Z.cross(X);bladeM=Matrix((X,Y,Z)).transposed().to_4x4();bladeM.translation=E+Z*.06+X*.043
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for ob,M,par in [(blade,bladeM,'B_R_Forearm'),(shield,shieldM,'B_L_Hand')]:
 bone=rig.data.edit_bones.new(ob.name);bone.head=M.translation;bone.tail=M@Vector((0,.1,0));bone.matrix=M;bone.length=.1;bone.parent=rig.data.edit_bones[par]
b=rig.data.edit_bones.new('BladeTip');b.head=bladeM@Vector(((588-385)*.65/990,0,.65));b.tail=b.head+Vector((0,0,.01));b.parent=rig.data.edit_bones['ForearmBlade']
bpy.ops.object.mode_set(mode='OBJECT')
for ob,M in [(blade,bladeM),(shield,shieldM)]:
 ob.data.transform(M);ob.parent=rig;mod=ob.modifiers.new('Rig','ARMATURE');mod.object=rig;g=ob.vertex_groups.new(name=ob.name);g.add(list(range(len(ob.data.vertices))),1,'REPLACE')
(P/'work/prop_attachments.json').write_text(json.dumps({'blade_rest_matrix':[list(r)for r in bladeM],'shield_rest_matrix':[list(r)for r in shieldM],'shield_grip_height_local':.26,'shield_grip_radius_m':.012,'blade_native':'forearm-mounted; fingers deliberately open','bones':len(rig.data.bones)},indent=2));assert len(rig.data.bones)<128
for im in bpy.data.images:
 if im.source=='FILE'and im.has_data:im.pack()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/assembled.blend'))
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(0);common.workbench_clay(sc,textured=True);common.render_views(str(P/'review/assembled'),.86,1.9,views=('front','left','back','right','three_quarter'),resolution=(640,900))
