"""Review round 1: existing geometry, surface skin, hip clearance, palm-seated reverse grip and quiet wrist."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
P=Path(__file__).resolve().parents[1];sys.dont_write_bytecode=True;sys.path.insert(0,str(P/'scripts'));import common
levels=[0] if '--preview' in sys.argv else range(4)
for level in levels:
 bpy.ops.wm.open_mainfile(filepath=str(P/f'work/round1/source_lod{level}.blend'));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];k=bpy.data.objects['KnifeAsset'];me=b.data;sc=bpy.context.scene;r.animation_data.action=None
 for pb in r.pose.bones:pb.matrix_basis.identity()
 bpy.context.view_layer.update();co=np.array([v.co[:]for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data]);gn={g.index:g.name for g in b.vertex_groups}
 # Skin hidden under the waistband belongs to the pelvis, not the independently stepping thigh.
 for vi in np.flatnonzero((pv==0)&(co[:,2]>.78)&(co[:,2]<1.055)):
  v=me.vertices[int(vi)];t=float(np.clip((1.055-v.co.z)/.03,0,1));v.co.x*=1-.25*t;v.co.y=-.035+(v.co.y+.035)*(1-.25*t)
  old={gn[g.group]:g.weight for g in v.groups if gn[g.group]!='_reduction_protect'}
  for g in b.vertex_groups:g.remove([int(vi)])
  for name,w in old.items():
   if w*(1-t)>1e-6:b.vertex_groups[name].add([int(vi)],w*(1-t),'REPLACE')
  pelvis=b.vertex_groups['B_Pelvis'];pelvis.add([int(vi)],t+old.get('B_Pelvis',0)*(1-t),'REPLACE')
 for vi in np.flatnonzero((pv==0)&(co[:,2]>.34)&(co[:,2]<.78)):
  v=me.vertices[int(vi)];t=float(np.clip((v.co.z-.34)/.04,0,1));cx=.11 if v.co.x>0 else -.11;v.co.x=cx+(v.co.x-cx)*(1-.10*t);v.co.y=-.025+(v.co.y+.025)*(1-.10*t)
 for f in me.polygons:f.use_smooth=True
 for e in me.edges:e.use_edge_sharp=False
 if me.has_custom_normals:me.normals_split_custom_set([(0,0,0)]*len(me.loops))
 tex=P/'work/round1/textures/lod0'
 for mi,mat in enumerate(me.materials):
  stem=['mfp','mfp_head'][mi]
  for node in mat.node_tree.nodes:
   if node.type!='TEX_IMAGE' or not node.image:continue
   name=node.image.name.lower();kind='normal' if 'normal' in name else 'metal_rough' if 'metal_rough' in name else 'basecolor';node.image=bpy.data.images.load(str(tex/f'{stem}_{kind}.png'));node.image.colorspace_settings.name='sRGB' if kind=='basecolor' else 'Non-Color'
 # Build the closed grip in the unchanged hand frame. Its centre lies at the palm-side finger roots.
 H=r.data.bones['B_R_Hand'].matrix_local.copy();W=H.translation;CH={i:[f'B_R_Finger{i}',f'B_R_Finger{i}1',f'B_R_Finger{i}2']for i in range(1,5)};CH[0]=['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002'];kn=[r.data.bones[CH[i][0]].head_local.copy()for i in range(1,5)];K=sum(kn,Vector())/4;long=(K-W).normalized();axis=(kn[-1]-kn[0]).normalized();normal=axis.cross(long).normalized()
 tips=sum((r.data.bones[CH[i][-1]].head_local for i in range(1,5)),Vector())/4
 if normal.dot(tips-K)<0:normal=-normal
 C=K-long*.034+normal*.026
 oldKnife=r.data.bones['Knife'].matrix_local.copy();A=axis;Y=(long-A*long.dot(A)).normalized();X=Y.cross(A).normalized();KM=Matrix((X,Y,A)).transposed().to_4x4();KM.translation=C
 # Local Z exits the little-finger side. Preserve the actual blade mesh; orient its edge by the grip frame.
 # Twist around the handle only, not the animated wrist.
 KM=KM@Matrix.Rotation(math.radians(113.4),4,'Z')
 knifeBasis=(H.inverted()@oldKnife).inverted()@(H.inverted()@KM)
 # Curl each actual phalanx in its anatomical flexion plane. No translations of the finger bases.
 def turn(n,ax,angle):
  pb=r.pose.bones[n];M=pb.matrix.copy();h=M.translation.copy();pb.matrix=Matrix.Translation(h)@Matrix.Rotation(angle,4,ax)@Matrix.Translation(-h)@M;bpy.context.view_layer.update()
 FJ=json.loads((P/'work/finger_joints.json').read_text())['R']
 for digit in range(1,5):
  chain=CH[digit]
  # Straighten the fitted phalanges in the palm flexion plane before adding a fist curl.
  for j,name in enumerate(chain):
   pb=r.pose.bones[name];tip=r.pose.bones[chain[j+1]].head if j<2 else pb.matrix@pb.bone.matrix_local.inverted()@Vector(FJ[name+'_tip']);direction=tip-pb.head;target=long-axis*long.dot(axis);q=direction.rotation_difference(target);ax,ang=q.to_axis_angle();turn(name,ax,ang)
  js=[np.array(r.pose.bones[n].head)for n in chain]+[np.array(r.pose.bones[chain[-1]].matrix@r.data.bones[chain[-1]].matrix_local.inverted()@Vector(FJ[chain[-1]+'_tip']))];ax=long.cross(normal).normalized();choices=[]
  for a0 in range(75,86,5):
   for a1 in range(45,111,5):
    for a2 in range(15,86,5):
     pts=[q.copy()for q in js]
     for j,degrees in enumerate([a0,a1,a2]):
      R=np.array(Matrix.Rotation(math.radians(degrees),3,ax))
      for kk in range(j+1,4):pts[kk]=pts[j]+R@(pts[kk]-pts[j])
     pp=np.concatenate([np.linspace(pts[j],pts[j+1],5)for j in range(3)]);v=pp-np.array(C);rad=np.linalg.norm(v-np.outer(v@np.array(axis),np.array(axis)),axis=1)
     score=np.square(rad-.016).sum()+100*np.square(np.minimum(rad-.013,0)).sum();choices.append((score,[a0,a1,a2]))
  angles=min(choices,key=lambda x:x[0])[1]
  for name,degrees in zip(chain,angles):turn(name,ax,math.radians(degrees))
  print('FINGER_CURL',digit,angles,flush=True)
 # Thumb opposes the curled fingers, with the pad over the handle.
 thumb=json.loads((P/'work/grip_closed.json').read_text())
 for name in CH[0]:r.pose.bones[name].rotation_quaternion=Quaternion(thumb['finger_local'][name])
 # Place the opposing thumb pad over the handle, using the existing three phalanges.
 tipgroup=b.vertex_groups[CH[0][-1]].index;tipids=[v.index for v in me.vertices if sum(g.weight for g in v.groups if g.group==tipgroup)>.6];assert tipids
 target=C-axis*.010+normal*.013
 for iteration in range(35):
  for name in reversed(CH[0]):
   ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());skin=ev.to_mesh();tip=sum((skin.vertices[i].co for i in tipids),Vector())/len(tipids);ev.to_mesh_clear();pb=r.pose.bones[name];d0=tip-pb.head;d1=target-pb.head
   if d0.length<1e-6 or d1.length<1e-6:continue
   q=d0.rotation_difference(d1);ax,ang=q.to_axis_angle();turn(name,ax,min(ang,math.radians(12)))
 bpy.context.view_layer.update();fingerq={name:r.pose.bones[name].rotation_quaternion.copy()for ch in CH.values()for name in ch}
 act=bpy.data.actions['Attack'];r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(12,subframe=.5)
 # Hold a modest fixed wrist relative to the forearm; the library arm supplies the swing.
 handq=Quaternion(Vector((0,1,0)),math.radians(44))@Quaternion(Vector((0,0,1)),math.radians(-25))
 names=['B_R_Hand','B_R_ForearmTwist','Knife']+list(fingerq)
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if any(fc.data_path.startswith('pose.bones["'+n+'"]')for n in names)and not(fc.data_path.endswith('scale')):bag.fcurves.remove(fc)
 end=float(act.frame_range[1]);r.animation_data.action=None
 for f in [0,end]:
  r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];sc.frame_set(int(f),subframe=f%1)
  pb=r.pose.bones['B_R_Hand'];pb.rotation_quaternion=handq;pb.keyframe_insert('rotation_quaternion',frame=f)
  pb=r.pose.bones['B_R_ForearmTwist'];pb.rotation_quaternion=Quaternion((r.data.bones['B_R_Forearm'].matrix_local.inverted()@r.data.bones['B_R_Hand'].head_local).normalized(),math.radians(26.4));pb.keyframe_insert('rotation_quaternion',frame=f)
  pb=r.pose.bones['Knife'];pb.location=knifeBasis.to_translation();pb.rotation_quaternion=knifeBasis.to_quaternion();pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  for name,q in fingerq.items():pb=r.pose.bones[name];pb.rotation_quaternion=q;pb.location=(0,0,0);pb.keyframe_insert('rotation_quaternion',frame=f);pb.keyframe_insert('location',frame=f)
  generated=r.animation_data.action
  if generated!=act:
   # keyframe insertion without an active action creates a temporary slot: move channels explicitly below.
   raise RuntimeError('Lost active action while keying')
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0]
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for point in fc.keyframe_points:point.interpolation='LINEAR'
 # Pronate through the forearm and a modest wrist offset, held constant through the slash.
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];fa=r.pose.bones['B_R_Forearm'];axisFa=(r.data.bones['B_R_Forearm'].matrix_local.inverted()@r.data.bones['B_R_Hand'].head_local).normalized();twist=Quaternion(axisFa,math.radians(44));values=[]
 for frame in np.linspace(0,end,round(end*48/30)+1):
  sc.frame_set(int(frame),subframe=frame%1);values.append((frame,fa.rotation_quaternion.copy()@twist))
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path=='pose.bones["B_R_Forearm"].rotation_quaternion':bag.fcurves.remove(fc)
 for frame,q in values:fa.rotation_quaternion=q;fa.keyframe_insert('rotation_quaternion',frame=frame)
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];samples=[]
 for frame in np.linspace(0,end,round(end*48/30)+1):
  sc.frame_set(int(frame),subframe=frame%1);M=r.pose.bones['B_R_UpperArm'].matrix.copy();t=frame/30;ease=lambda a:max(0,min(1,a))**2*(3-2*max(0,min(1,a)));amount=math.radians(45)*ease((t-.24)/.28)*(1-ease((t-.9)/.6));rot=Matrix.Rotation(amount,4,'Z')@M;rot.translation=M.translation;pb=r.pose.bones['B_R_UpperArm'];pb.matrix=rot;bpy.context.view_layer.update();samples.append((frame,pb.rotation_quaternion.copy()))
 for layer in act.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in list(bag.fcurves):
     if fc.data_path=='pose.bones["B_R_UpperArm"].rotation_quaternion':bag.fcurves.remove(fc)
 for frame,q in samples:r.pose.bones['B_R_UpperArm'].rotation_quaternion=q;r.pose.bones['B_R_UpperArm'].keyframe_insert('rotation_quaternion',frame=frame)
 (P/'review/round1/grip_frame.json').write_text(json.dumps({'hand_local_grip':list(H.inverted()@C),'palm_axis':list(H.to_3x3().inverted()@normal),'pinky_axis':list(A),'knife_basis':list(map(list,knifeBasis))},indent=2))
 r.animation_data.action=bpy.data.actions['Standing'];r.animation_data.action_slot=r.animation_data.action.slots[0];sc.frame_set(0);bpy.ops.wm.save_as_mainfile(filepath=str(P/f'work/round1/lod{level}.blend'))
 if level==0 and '--preview' in sys.argv:
  for ob in list(sc.objects):
   if ob not in [b,k,r]:bpy.data.objects.remove(ob,do_unlink=True)
  common.workbench_clay(sc,True);sc.display.shading.light='FLAT';sc.world.color=(.2,.2,.2)
  for role,frames in [('Standing',[0]),('Hit',[8]),('Attack',[0,6,10,12.5,16,22,30,46])]:
   r.animation_data.action=bpy.data.actions[role];r.animation_data.action_slot=r.animation_data.action.slots[0]
   for f in frames:
    sc.frame_set(int(f),subframe=f%1);common.render_views(str(P/f'review/round1/repair_{role}_{f:g}'),.98,2.1,views=('front','three_quarter'),resolution=(420,630))
    if role=='Attack' and f in [10,12.5]:
     h=r.pose.bones['B_R_Hand'].head;common.render_views(str(P/f'review/round1/grip_{f:g}'),h.z-.03,.26,views=('front','left','three_quarter'),resolution=(600,600),target=(h.x,h.y))
 print('REPAIRED',level,flush=True)
