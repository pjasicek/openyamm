"""Fit native rigid equipment and drive the two hanging cloth panels on local bones."""
import bpy,sys,os,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'));import common
bpy.ops.wm.open_mainfile(filepath=str(P/'work/motion_fit.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text());HF=json.loads((P/'work/hand_frames.json').read_text())
def setact(a):
 rig.animation_data.action=a
 if a and len(a.slots):rig.animation_data.action_slot=a.slots[0]
setact(bpy.data.actions['Standing']);sc.frame_set(0);Hp=rig.pose.bones['B_R_Hand'].matrix.copy();C=Hp@Vector(G['handle_centre_hand_local']);A=(Hp.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();X=Vector((0,0,1));X=(X-A*X.dot(A)).normalized();Y=A.cross(X).normalized();S=Matrix([X,Y,A]).transposed().to_4x4();S.translation=C;Sr=rig.data.bones['B_R_Hand'].matrix_local@Hp.inverted()@S
E=rig.pose.bones['B_L_Forearm'].head;W=rig.pose.bones['B_L_Hand'].head;Z=(E-W).normalized();N=Vector((1,0,0));N=(N-Z*N.dot(Z)).normalized();Y=-N;X=Y.cross(Z).normalized();Y=Z.cross(X).normalized();M=Matrix([X,Y,Z]).transposed().to_4x4();M.translation=E.lerp(W,.38)+N*.072;Fp=rig.pose.bones['B_L_ForearmTwist'].matrix.copy();Mr=rig.data.bones['B_L_ForearmTwist'].matrix_local@Fp.inverted()@M
setact(None)
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update();bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
def bone(name,parent,M,length=.10,deform=True):
 b=rig.data.edit_bones.new(name);b.head=M.translation;b.tail=b.head+M.to_3x3().col[1]*length;b.align_roll(M.to_3x3().col[2]);b.parent=rig.data.edit_bones[parent];b.use_deform=deform;return b
bone('Spear','B_R_Hand',Sr);bone('Buckler','B_L_ForearmTwist',Mr)
T=Sr.copy();T.translation=Sr@Vector((0,0,1.08));bone('Socket_SpearTip','Spear',T,.03,False)
T=rig.data.edit_bones['B_L_Hand'].matrix.copy();T.translation=T@Vector((0,.105,-.03));bone('Socket_LeftPalm','B_L_Hand',T,.03,False)
for part,name,y in [(1,'ClothFront',-.135),(10,'ClothBack',.075)]:
 T=Matrix();T.translation=Vector((0,y,.967));bone(name,'B_Pelvis',T,.12)
bpy.ops.object.mode_set(mode='OBJECT')
with bpy.data.libraries.load(str(P/'work/props_untextured.blend'))as(src,dst):dst.objects=['Spear','Buckler']
for ob,M,name in zip(dst.objects,[Sr,Mr],['Spear','Buckler']):
 bpy.context.collection.objects.link(ob)
 if name=='Buckler':
  for v in ob.data.vertices:
   if v.co.y>.015 and abs(v.co.x)<=.1301 and abs(abs(v.co.z)-.09)<.027:
    v.co.y+=.050*max(0,math.sin(math.pi*(v.co.x+.13)/.26))
 ob.hide_render=False;ob.hide_set(False);ob.data.transform(M);ob.matrix_world=Matrix();ob.name=name+'Mesh';ob.parent=rig;mod=ob.modifiers.new('Rig','ARMATURE');mod.object=rig;ob.vertex_groups.new(name=name).add(list(range(len(ob.data.vertices))),1,'REPLACE')
 mat=ob.data.materials[0];mat.use_nodes=True;nt=mat.node_tree;bs=nt.nodes.get('Principled BSDF');tx=nt.nodes.new('ShaderNodeTexImage');tx.image=bpy.data.images.load(str(P/f'meshy/{name.lower()}_retexture_v1/texture_urls_0_base_color.png'));nt.links.new(tx.outputs['Color'],bs.inputs['Base Color'])
# Whole shells keep their topology and UVs; only their skin ownership changes.
pv=np.array([v.value for v in body.data.attributes['piece'].data]);co=np.array([tuple(v.co)for v in body.data.vertices]);cloth={}
for part,name in [(1,'ClothFront'),(10,'ClothBack')]:
 g=body.vertex_groups.new(name=name);ids=np.where(pv==part)[0];cloth[name]=ids.tolist()
 for i in ids:
  for old in body.vertex_groups:old.remove([int(i)])
  w=float(np.clip((.98-co[i,2])/.075,0,1));g.add([int(i)],w,'REPLACE');body.vertex_groups['B_Pelvis'].add([int(i)],1-w,'REPLACE')
# Start with pelvis-relative secondary motion. The exact cloth/body signed-distance audit refines it next.
for a in bpy.data.actions:
 setact(a)
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);pel=rig.pose.bones['B_Pelvis'].matrix.to_3x3()@rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();angles=[]
  for sd in 'LR':
   d=pel.inverted()@(rig.pose.bones[f'B_{sd}_Calf'].head-rig.pose.bones[f'B_{sd}_Thigh'].head);angles.append(math.atan2(-d.y,-d.z))
  for name,ang in [('ClothFront',-max(0,max(angles))*.55-.04),('ClothBack',max(0,-min(angles))*.55+.04)]:
   pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion((1,0,0),ang);pb.keyframe_insert('rotation_quaternion',frame=f)
setact(None);bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/equipped.blend'));(P/'work/attachments.json').write_text(json.dumps({'spear_rest_matrix':[list(r)for r in Sr],'buckler_rest_matrix':[list(r)for r in Mr],'sockets':['Socket_SpearTip','Socket_LeftPalm'],'cloth_vertex_ids':cloth},indent=2))
common.workbench_clay(sc,textured=True)
for name in ['Standing','Walking','Running','Attack','Cast','Hit','Fidget','Death']:
 setact(bpy.data.actions[name])
 for j in range(5):
  f=float(rig.animation_data.action.frame_range[1])*j/4;sc.frame_set(int(f),subframe=f-int(f));common.render_views(str(P/f'review/equipped_{name}_{j}'),.85,3.4,views=('front','left','three_quarter'),resolution=(350,400))
