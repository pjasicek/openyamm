"""Detailed lathed hardwood club from the generated standalone side design, with parked/drawn animation."""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_gated.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];scene=bpy.context.scene
G=json.loads((P/'work/grip_pose.json').read_text())
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
# The native club hangs beside the right hip, behind the purse, its weighted head downward.
park=Vector((-.35,.04,.89));axis=Vector((-.24,.02,-1)).normalized();Q=axis.to_track_quat('Z','Y')
M=Q.to_matrix().to_4x4();M.translation=park
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
b=rig.data.edit_bones.new('Club');b.head=park;b.tail=park+axis*.45;b.parent=rig.data.edit_bones['B_Pelvis'];b.align_roll(Q@Vector((0,1,0)))
bpy.ops.object.mode_set(mode='OBJECT')
# Bone Y is the haft axis; geometry below is authored in an independent Z-axis frame.
restbone=rig.data.bones['Club'].matrix_local.copy()
profile=[(-.065,.001),(-.061,.014),(-.055,.021),(-.045,.022),(-.034,.020),(-.025,.015),
(-.020,.0125),(-.018,.0128),(-.013,.0128),(-.011,.0125),(-.006,.0125),(-.004,.0128),
(.001,.0128),(.003,.0125),(.022,.0125),(.050,.013),(.08,.015),(.115,.016),(.15,.019),
(.20,.024),(.25,.033),(.29,.042),(.33,.05),(.37,.055),(.40,.054),(.425,.043),(.442,.027),(.45,.009),(.452,.001)]
verts=[];uvs=[];N=24
for z,r in profile:
 for j in range(N):
  a=j*2*math.pi/N;rr=r*(1+.025*math.sin(a*3+z*9)+.015*math.cos(a*7-z*5))
  verts.append(M@Vector((rr*math.cos(a),rr*math.sin(a),z)))
  # Project both sides onto the detailed orthographic wood design; avoid its transparent margins.
  x=48+(z+.065)/.517*1440
  center=281-15*max(0,(z-.10)/.352);height=45+120*max(0,(z-.14)/.30)
  y=center+height*.82*math.sin(a)
  uvs.append((x/1536,1-y/1024))
faces=[]
for i in range(len(profile)-1):
 for j in range(N):
  a=i*N+j;b=i*N+(j+1)%N;c=(i+1)*N+(j+1)%N;d=(i+1)*N+j
  faces.extend([(a,b,c),(a,c,d)])
faces.extend([tuple(range(N-1,-1,-1)),tuple((len(profile)-1)*N+j for j in range(N))])
me=bpy.data.meshes.new('ClubMesh');me.from_pydata(verts,[],faces);me.update();ob=bpy.data.objects.new('ClubMesh',me);scene.collection.objects.link(ob)
uv=me.uv_layers.new(name='UVMap')
for f in me.polygons:
 f.use_smooth=True
 for li,vi in zip(f.loop_indices,f.vertices):uv.data[li].uv=uvs[vi]
ob.parent=rig;mod=ob.modifiers.new('Armature','ARMATURE');mod.object=rig;vg=ob.vertex_groups.new(name='Club');vg.add(list(range(len(verts))),1,'REPLACE')
mat=bpy.data.materials.new('MerchantClub');mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;bs.inputs['Metallic'].default_value=0
im=bpy.data.images.load(str(P/'references_hd/club_design.png'));tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=im;mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);me.materials.append(mat)
# Geometry frame vs armature bone frame; attachment extraction retains this relation.
bone_from_design=restbone.inverted()@M
pelrest=rig.data.bones['B_Pelvis'].matrix_local.copy();handCenter=Vector(G['handle_centre_hand_local']);handAxis=Vector(G['handle_axis_hand_local'])
def smooth(x):x=min(1,max(0,x));return x*x*(3-2*x)
motion={}
for a in bpy.data.actions:
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];keys=[];prev=None
 for f in np.arange(0,float(a.frame_range[1])+.001,.5):
  scene.frame_set(int(f),subframe=float(f%1))
  Mp=rig.pose.bones['B_Pelvis'].matrix@pelrest.inverted()@M
  if a.name=='Attack':
   H=rig.pose.bones['B_R_Hand'].matrix;C=H@handCenter;A=(H.to_3x3()@handAxis).normalized();Qh=A.to_track_quat('Z','Y')
   w=smooth(f/6)*smooth((float(a.frame_range[1])-f)/7.5)
   Md=Mp.to_quaternion().slerp(Qh,w).to_matrix().to_4x4();Md.translation=Mp.translation.lerp(C,w)
  else:Md=Mp
  B=Md@bone_from_design.inverted();pb=rig.pose.bones['Club'];pb.rotation_mode='QUATERNION';pb.matrix=B
  q=pb.rotation_quaternion.copy()
  if prev is not None and q.dot(prev)<0:q=-q
  prev=q;pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=float(f));pb.keyframe_insert('location',frame=float(f))
  tip=Md@Vector((0,0,.452));keys.append([float(f/30),*tip,*Md.translation])
 motion[a.name]=keys
rig.animation_data.action=bpy.data.actions['Standing'];rig.animation_data.action_slot=rig.animation_data.action.slots[0];scene.frame_set(0)
(P/'review/club_motion.json').write_text(json.dumps(motion,indent=2));assert sum(len(f.vertices)-2 for f in me.polygons)>=1000
bpy.ops.file.pack_all();bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/with_club.blend'))
import common
body.hide_render=True;rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
common.workbench_clay(scene,True);lo,hi=common.world_bounds([ob]);mid=(lo+hi)*.5
common.render_views(str(P/'review/club_close'),mid.z,.67,views=('front','left','three_quarter'),resolution=(600,750),target=(mid.x,mid.y))
