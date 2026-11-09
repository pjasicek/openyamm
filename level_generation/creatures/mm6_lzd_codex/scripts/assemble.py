"""Textured reduced actor, a rigid detachable bow, nocked arrow and two uniformly-scaled string segments."""
import bpy,bmesh,json,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_reduced.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene;me=body.data;rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update()
def material(name,base,normal,mr):
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF')
 def tex(path,cs):
  n=nt.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(path));n.image.colorspace_settings.name=cs;n.image.pack();return n
 nt.links.new(tex(base,'sRGB').outputs['Color'],bs.inputs['Base Color']);nm=nt.nodes.new('ShaderNodeNormalMap');nt.links.new(tex(normal,'Non-Color').outputs['Color'],nm.inputs['Color']);nt.links.new(nm.outputs['Normal'],bs.inputs['Normal']);nm.inputs['Strength'].default_value=.65
 sep=nt.nodes.new('ShaderNodeSeparateColor');nt.links.new(tex(mr,'Non-Color').outputs['Color'],sep.inputs['Color']);nt.links.new(sep.outputs['Green'],bs.inputs['Roughness']);nt.links.new(sep.outputs['Blue'],bs.inputs['Metallic']);bs.inputs['Specular IOR Level'].default_value=.18;return mat
bodymat=material('Lizard_A',*[P/f'textures/body_{n}_1k.png'for n in ('basecolor','normal','metal_rough')]);headmat=material('LizardHead_A',*[P/f'textures/head_{n}_1k.png'for n in ('basecolor','normal','metal_rough')]);bowmat=material('LizardBow_A',*[P/f'textures/bow/{n}_1k.png'for n in ('basecolor','normal','metal_rough')])
me.materials.clear();me.materials.append(bodymat);me.materials.append(headmat)
for f in me.polygons:
 hd=me.attributes['head'].data[f.index].value;f.material_index=hd
 if hd:
  for li in f.loop_indices:me.uv_layers['UVMap'].data[li].uv=me.uv_layers['HeadUV'].data[li].uv
me.uv_layers.remove(me.uv_layers['HeadUV']);me.uv_layers.active=me.uv_layers['UVMap']
# The reference draw frame defines the bow's back; its long axis was corrected in the hand pose.
G=json.loads((P/'work/grip_pose.json').read_text());C=Vector(G['handle_centre_hand_local']);A=Vector(G['handle_axis_hand_local']);at=bpy.data.actions['Attack'];rig.animation_data.action=at;rig.animation_data.action_slot=at.slots[0];scene.frame_set(21);hp=rig.pose.bones['B_L_Hand'].matrix;axis=(hp.to_3x3()@A).normalized();behind=Vector((0,1,0));behind=(behind-axis*behind.dot(axis)).normalized();bx=behind.cross(axis).normalized();rot=Matrix([bx,behind,axis]).transposed();local=hp.to_3x3().inverted()@rot
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();bowrest=rig.data.bones['B_L_Hand'].matrix_local@Matrix.Translation(C)@local.to_4x4()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for n,parent,M in [('Bow','B_L_Hand',bowrest),('Arrow','Bow',Matrix()),('StringTop','Bow',Matrix()),('StringBottom','Bow',Matrix()),('Socket_Arrow','Bow',bowrest@Matrix.Translation((0,-.12,.04)))]:
 eb=rig.data.edit_bones.new(n);eb.head=M.translation;eb.tail=eb.head+M.to_3x3().col[1]*.1;eb.align_roll(M.to_3x3().col[2]);eb.parent=rig.data.edit_bones[parent];eb.use_deform=n!='Socket_Arrow'
bpy.ops.object.mode_set(mode='OBJECT')
for n in ['Bow','Arrow','StringTop','StringBottom','Socket_Arrow']:rig.pose.bones[n].rotation_mode='QUATERNION'
objects=[]
for name,arrow,piece in [('BowMesh',False,201),('ArrowMesh',True,202)]:
 with bpy.data.libraries.load(str(P/'work/bow_textured.blend'),link=False)as(src,dst):dst.objects=['BowArrow']
 ob=dst.objects[0];scene.collection.objects.link(ob);ob.name=name;bm=bmesh.new();bm.from_mesh(ob.data);at=bm.faces.layers.int['prop_part'];bmesh.ops.delete(bm,geom=[f for f in bm.faces if (f[at]>=5)!=arrow],context='FACES');bm.to_mesh(ob.data);bm.free()
 ob.data.materials.clear();ob.data.materials.append(bowmat)
 for f in ob.data.polygons:f.material_index=0
 for v in ob.data.vertices:
  if arrow:v.co-=Vector((.22,.03,0))
  else:v.co=bowrest@v.co
 ob.data.attributes.new('piece','INT','POINT').data.foreach_set('value',[piece]*len(ob.data.vertices));ob.vertex_groups.new(name='Arrow'if arrow else'Bow').add(list(range(len(ob.data.vertices))),1,'REPLACE');objects.append(ob)
# Both strings reuse a leather texel in the bow atlas. Uniform scale preserves the runtime normal contract.
string_uv=json.loads((P/'work/string_uv.json').read_text())
for n,piece in [('StringTop',203),('StringBottom',204)]:
 verts=[(math.cos(j*math.tau/6)*.001,math.sin(j*math.tau/6)*.001,z)for z in (0,1)for j in range(6)];faces=[(i,(i+1)%6,(i+1)%6+6,i+6)for i in range(6)];sm=bpy.data.meshes.new(n);sm.from_pydata(verts,[],faces);sm.update();ob=bpy.data.objects.new(n+'Mesh',sm);scene.collection.objects.link(ob);sm.materials.append(bowmat);uv=sm.uv_layers.new(name='UVMap')
 for u in uv.data:u.uv=string_uv
 sm.attributes.new('piece','INT','POINT').data.foreach_set('value',[piece]*len(verts));ob.vertex_groups.new(name=n).add(list(range(len(verts))),1,'REPLACE');objects.append(ob)
bpy.ops.object.select_all(action='DESELECT');body.select_set(True)
for o in objects:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.object.join();body.name='Body'
report={};rest={n:rig.data.bones[n].matrix_local.copy()for n in ['Arrow','StringTop','StringBottom']}
def rigidmap(start,end):
 d=end-start;rot=d.to_track_quat('Z','Y').to_matrix().to_4x4();rot.translation=start;return rot,d.length
for act in bpy.data.actions:
 if act.name not in ['Standing','Walking','Running','Attack','Hit','Death','Dead','Fidget']:continue
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];N=int(act.frame_range[1]);rows=[]
 for f in range(N+1):
  scene.frame_set(f)
  roll=150.0
  if act.name=='Attack':
   enter=float(np.clip((f-10)/9,0,1));enter=enter*enter*(3-2*enter);roll=150*(1-enter)
   if f>22:roll=min(150.,25*(f-22))
  pb=rig.pose.bones['Bow'];pb.rotation_quaternion=Quaternion((0,0,1),math.radians(roll));pb.keyframe_insert('rotation_quaternion',frame=f);bpy.context.view_layer.update()
  bm=rig.pose.bones['Bow'].matrix;mid=bm@Vector((0,.215,.04));tips=[bm@Vector((0,.215,.55)),bm@Vector((0,.215,-.55))];draw=0
  if act.name=='Attack'and f<23:draw=float(np.clip((f-14)/2,0,1))
  # Nock lies on the draw fingers; release disconnects it from the recoiling hand.
  rh=rig.pose.bones['B_R_Hand'].matrix;kn=rig.pose.bones['B_R_Finger11'].head;tip=rig.pose.bones['B_R_Finger12'].head;nock=kn.lerp(tip,.55);nock=mid.lerp(nock,draw)
  for n,start in zip(['StringTop','StringBottom'],tips):
   M,L=rigidmap(start,nock);M=M@Matrix.Scale(L,4);pb=rig.pose.bones[n];pb.matrix=M@rest[n];pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f)
  target=bm@Vector((0,-.08,.04));M,L=rigidmap(nock,target);scale=1.22;M=M@Matrix.Scale(scale,4)@Matrix.Translation((0,0,.32));pb=rig.pose.bones['Arrow'];pb.matrix=M@rest['Arrow'];visible=act.name=='Attack'and 19<=f<23
  if not visible:pb.scale*=.001
  pb.keyframe_insert('location',frame=f);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('scale',frame=f);rows.append({'frame':f,'draw':draw,'arrow_visible':visible,'nock':list(nock),'bow':list(bm.translation),'arrow_to_bow_m':L})
 report[act.name]=rows
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
(P/'work/bow_animation.json').write_text(json.dumps({'clips':report,'impact_seconds':23/30,'bow_hand_rotation':[list(r)for r in local]},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/master.blend'))
print('ASSEMBLED',sum(len(f.vertices)-2 for f in body.data.polygons),'triangles',len(rig.data.bones),'bones')
