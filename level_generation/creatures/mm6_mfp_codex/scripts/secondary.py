import bpy,sys,runpy,os,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import common
os.environ['R_HANDLE']='0.009';os.environ['GRIP_RENDER']=str(P/'review/grip_refined')
sys.argv=['grip_solve.py','--',str(P/'work/rig_motion.blend'),'Attack','15'];runpy.run_path(str(P/'scripts/grip_solve.py'),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_motion.blend'))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];sc=bpy.context.scene;r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();G=json.loads((P/'work/grip_pose.json').read_text())
pv=np.array([a.value for a in b.data.attributes['piece'].data]);co=np.array([v.co[:]for v in b.data.vertices])
bpy.context.view_layer.objects.active=r;bpy.ops.object.mode_set(mode='EDIT');eb=r.data.edit_bones
for c in range(8):
 a=c*math.tau/8;bo=eb.new(f'Skirt_{c}');bo.head=(.115*math.cos(a),-.03+.085*math.sin(a),.955);bo.tail=(.19*math.cos(a),-.03+.15*math.sin(a),.32);bo.parent=eb['B_Pelvis']
braid=co[pv==3];pts=[]
for z in [1.48,1.28,1.08,.865]:
 band=braid[np.abs(braid[:,2]-z)<.035];pt=band.mean(0)if len(band)else braid.mean(0);pt[2]=z;pts.append(Vector(pt))
for j in range(3):
 bo=eb.new(f'Braid_{j}');bo.head=pts[j];bo.tail=pts[j+1];bo.parent=eb['B_Head']if j==0 else eb[f'Braid_{j-1}']
H=eb['B_R_Hand'].matrix.copy();C=H@Vector(G['handle_centre_hand_local']);A=-(H.to_3x3()@Vector(G['handle_axis_hand_local'])).normalized();Y=Vector((0,1,0));Y=(Y-A*Y.dot(A)).normalized();X=Y.cross(A);KM=Matrix((X,Y,A)).transposed().to_4x4();KM.translation=C
bo=eb.new('Knife');bo.matrix=KM;bo.length=.16;bo.parent=eb['B_R_Hand']
bo=eb.new('Socket_Knife_Tip');bo.head=C+A*.215;bo.tail=bo.head+A*.02;bo.parent=eb['Knife'];bo.use_deform=False
bpy.ops.object.mode_set(mode='OBJECT')
for n in [f'Skirt_{c}'for c in range(8)]+[f'Braid_{c}'for c in range(3)]:b.vertex_groups.new(name=n)
def weights(i,w):
 for g in b.vertex_groups:g.remove([i])
 for n,v in w.items():
  if v>1e-6:b.vertex_groups[n].add([i],float(v),'REPLACE')
for v in b.data.vertices:
 if pv[v.index]==1:
  a=math.atan2(v.co.y+.03,v.co.x)%math.tau;x=a/math.tau*8;c=int(x);mix=x-c;w=np.clip((.98-v.co.z)/.20,0,1)
  weights(v.index,{'B_Pelvis':1-w,f'Skirt_{c}':w*(1-mix),f'Skirt_{(c+1)%8}':w*mix})
 if pv[v.index]==3:
  x=np.clip((1.48-v.co.z)/.20,0,2.99);j=min(2,int(x));mix=x-j
  weights(v.index,{f'Braid_{j}':1-mix if j<2 else 1,**({f'Braid_{j+1}':mix}if j<2 else {})})
# Preserve a textured Meshy prop with real curved blade, ferrules and wrapped grip.
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(P/'meshy/knife_geometry_v1/model_urls_glb.glb'));obs=[o for o in bpy.data.objects if o not in before and o.type=='MESH']
for o in bpy.data.objects:o.select_set(o in obs)
bpy.context.view_layer.objects.active=obs[0]
if len(obs)>1:bpy.ops.object.join()
k=bpy.context.object;k.name='KnifeAsset';k.parent=None;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
kco=np.array([v.co[:]for v in k.data.vertices]);lo=kco.min(0);hi=kco.max(0);scale=.28/(hi[2]-lo[2]);origin=Vector(((lo[0]+hi[0])/2,(lo[1]+hi[1])/2,lo[2]+.050/scale))
for v in k.data.vertices:v.co=KM@((v.co-origin)*scale)
# Keep the actual mesh cross-section; measured at the grip for the grip gate.
k.parent=r;am=k.modifiers.new('Armature','ARMATURE');am.object=r;k.vertex_groups.new(name='Knife').add(list(range(len(k.data.vertices))),1,'REPLACE')
for poly in k.data.polygons:poly.use_smooth=True
# Snapshot source body poses; secondary channels are then written without touching their action evaluation.
base={}
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];rows=[]
 for f in range(int(a.frame_range[1])+1):
  sc.frame_set(f);rows.append({n:r.pose.bones[n].matrix.copy() for n in ['B_Pelvis','B_Head','B_L_Foot','B_R_Foot']})
 base[a.name]=rows
r.animation_data.action=None
for a in bpy.data.actions:
 r.animation_data.action=a;r.animation_data.action_slot=a.slots[0];prev={}
 for f,M in enumerate(base[a.name]):
  sc.frame_set(f)
  for n,q in G['finger_local'].items():
   pb=r.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion(q)if a.name=='Attack'else Quaternion();pb.keyframe_insert('rotation_quaternion',frame=f)
  kb=r.pose.bones['Knife'];kb.scale=(1,)*3 if a.name=='Attack'else(.001,)*3;kb.keyframe_insert('scale',frame=f)
  # Garment meridians follow the displaced calves; upper fabric stays pinned to the pelvis.
  T=M['B_Pelvis']@r.data.bones['B_Pelvis'].matrix_local.inverted()
  for c in range(8):
   n=f'Skirt_{c}';rb=r.data.bones[n];pb=r.pose.bones[n];a0=c*math.tau/8;wL=(math.cos(a0)+1)/2
   dh=Vector()
   for sd,w in [('L',wL),('R',1-wL)]:
    ft=r.data.bones[f'B_{sd}_Foot'];delta=M[f'B_{sd}_Foot'].translation-(T@ft.head_local);dh+=delta*w
   target=T@rb.tail_local+dh*.85
   if a.name in ['Death','Dead']:target.z=max(.025,target.z)
   head=T@rb.head_local;R=T.to_3x3()@rb.matrix_local.to_3x3();R=(R@Vector((0,1,0))).rotation_difference((target-head).normalized()).to_matrix()@R
   mat=R.to_4x4();mat.translation=head;pb.matrix=mat;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=f)
  for j in range(3):
   n=f'Braid_{j}';pb=r.pose.bones[n];rb=r.data.bones[n];lag=max(0,f-2*(j+1));H=base[a.name][lag]['B_Head']@r.data.bones['B_Head'].matrix_local.inverted();R=H.to_3x3()@rb.matrix_local.to_3x3();mat=R.to_4x4();mat.translation=pb.head
   if a.name in ['Death','Dead']:
    direction=R@Vector((0,1,0));target=mat.translation+direction*rb.length
    if target.z<.03:target.z=.03;R=direction.rotation_difference((target-mat.translation).normalized()).to_matrix()@R;mat=R.to_4x4();mat.translation=pb.head
   pb.matrix=mat;bpy.context.view_layer.update();pb.keyframe_insert('rotation_quaternion',frame=f)
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
r.animation_data.action=None
for pb in r.pose.bones:pb.matrix_basis.identity()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_secondary.blend'))
sys.argv=['twist_bones.py','--',str(P/'work/rig_secondary.blend'),str(P/'work/rig_equipped.blend')];runpy.run_path(str(P/'scripts/twist_bones.py'),run_name='__main__')
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];pv=np.array([x.value for x in b.data.attributes['piece'].data])
for part in [7,10,11,12,18,21]:
 ids=np.flatnonzero(pv==part);sd='L'if np.mean([b.data.vertices[i].co.x for i in ids])>0 else 'R'
 for g in b.vertex_groups:g.remove(ids.tolist())
 b.vertex_groups[f'B_{sd}_ForearmTwist'].add(ids.tolist(),1,'REPLACE')
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_equipped.blend'))
# Preserve body/head topology for exact per-face UV transfer.
for label,layer in [('body','UVMap'),('head','HeadUV')]:
 sys.argv=['transfer_uv.py','--',str(P/'work/rig_equipped.blend'),str(P/f'meshy/{label}_retexture_v1'),str(P/'work/rig_equipped.blend'),layer];runpy.run_path(str(P/'scripts/transfer_uv.py'),run_name='__main__')
for layer in ['UVMap','HeadUV']:
 sys.argv=['uv_raster.py','--',str(P/'work/rig_equipped.blend'),layer,'1024'];runpy.run_path(str(P/'scripts/uv_raster.py'),run_name='__main__')
