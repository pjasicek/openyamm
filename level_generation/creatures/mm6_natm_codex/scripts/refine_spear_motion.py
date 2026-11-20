"""Fit the held spear against the actual falling torso/legs, preserving its rigid fist frame."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));from collision import inside
bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rr=bpy.data.objects['Rig'];aa=bpy.data.actions['Death'];rr.animation_data.action=aa;rr.animation_data.action_slot=aa.slots[0];source=[]
for f in range(int(aa.frame_range[1])+1):
 bpy.context.scene.frame_set(f);source.append({pb.name:pb.rotation_quaternion.copy()for pb in rr.pose.bones if pb.name.startswith('B_R_')})
bpy.ops.wm.open_mainfile(filepath=str(P/'work/contact_master.blend'));rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene;sys.modules.pop('arm_ik',None);from arm_ik import Side,swing_twist_deg
obj=Side('R');G=json.loads((P/'work/grip_pose.json').read_text());g=Vector(G['handle_centre_hand_local']);ax=Vector(G['handle_axis_hand_local']);me=body.data;pv=np.array([d.value for d in me.attributes['piece'].data]);weights=np.zeros(len(me.vertices))
for v in me.vertices:
 weights[v.index]=sum(x.weight for x in v.groups if body.vertex_groups[x.group].name.startswith('B_R_')and any(t in body.vertex_groups[x.group].name for t in ['Arm','Forearm','Hand','Finger']))
handids=[v.index for v in me.vertices if sum(x.weight for x in v.groups if body.vertex_groups[x.group].name.startswith(('B_R_Hand','B_R_Finger')))>.65]
me.calc_loop_triangles();tri=np.array([list(t.vertices)for t in me.loop_triangles]);tri=tri[np.all(pv[tri]==0,axis=1)&np.all(weights[tri]<.1,axis=1)];act=bpy.data.actions['Death'];poses=[];report=[];previous=None;previousRa=None
zs=np.linspace(-.89,1.08,65);zs=zs[np.abs(zs)>.15]
for f in range(int(act.frame_range[1])+1):
 rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0];sc.frame_set(f);rig.animation_data.action=None
 for n,q in source[f].items():rig.pose.bones[n].rotation_quaternion=q
 bpy.context.view_layer.update();H=rig.pose.bones['B_R_Hand'].matrix.copy();R0=H.to_3x3();A0=(R0@ax).normalized();C0=H@g;S=rig.pose.bones['B_R_UpperArm'].head.copy();E=rig.pose.bones['B_R_Forearm'].head.copy();ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();v=[p.co.copy()for p in mm.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(v,tri.tolist(),all_triangles=True);handlocal=[H.inverted()@v[i]for i in handids];options=[]
 targets=[C0+Vector((dx,dy,dz))for dx in [0,-.04,.04]for dy in [0,.04,-.04]for dz in [0,.02,.04]]
 for C in targets:
  az=max(-(C.z-.036)/1.08,min((C.z-.036)/.89,A0.z));az=max(-.95,min(.95,az));flat=math.sqrt(1-az*az)
  axes=[A0]+[Vector((math.cos(math.radians(d))*flat,math.sin(math.radians(d))*flat,az))for d in sorted(set(list(range(0,360,15))+[round(math.degrees(math.atan2(A0.y,A0.x)))+k for k in [-10,-5,0,5,10]]))]
  for A in axes:
   if min((C+A*z).z for z in [-.89,1.08])<.025:continue
   R=A0.rotation_difference(A).to_matrix()@R0;W=C-R@g
   if (W-S).length>(obj.l1+obj.l2)*.995 or min((W+R@p).z for p in handlocal)<.005:continue
   depth=0;contacts=0
   for z in zs:
    p=C+A*float(z);q,n,idx,d=tree.find_nearest(p)
    if q is None:continue
    if d<.017:depth=max(depth,.017-d);contacts+=1
    elif (p-q).dot(n)<0 and inside(tree,p):depth=max(depth,d+.017);contacts+=1
   cost=depth*20000+contacts*3+(C-C0).length*50+math.degrees(A.angle(A0))*.07
   if previous:cost+=math.degrees(A.angle(previous[0]))*.25+(C-previous[1]).length*100
   options.append((cost,C,A,R,depth))
 assert options,(f,'no reachable spear pose')
 fitted=[]
 for cost,C,A,R,depth in sorted(options,key=lambda x:x[0])[:8]:
  W=C-R@g;axis=(W-S).normalized();pole=E-S
  for deg in range(-150,151,10):
   r=obj.pose_anatomical(C,R,Quaternion(axis,math.radians(deg))@pole);parent=rig.pose.bones['B_R_Clavicle'].matrix.to_3x3()@obj.rel['Arm'];upper=swing_twist_deg((parent.inverted()@r['Ra']).to_quaternion(),obj.uA)[1];c=cost+10000*max(0,.065-r['E'].z)+.06*abs(deg)+.08*abs(upper)+.07*abs(r['tw'])+.2*r['sw']+8*max(0,abs(upper)-85)+6*max(0,abs(r['tw'])-110)+6*max(0,r['sw']-65)
   if previousRa:c+=4.0*math.degrees(2*math.acos(min(1,abs(previousRa.dot(r['Ra'].to_quaternion())))))
   fitted.append((c,r,A,C,depth,upper))
 _,r,A,C,depth,upper=min(fitted,key=lambda x:x[0]);obj.apply(r);previousRa=r['Ra'].to_quaternion();fb=rig.data.bones['B_R_Forearm'];hb=rig.data.bones['B_R_Hand'];seg=(fb.matrix_local.inverted()@hb.head_local).normalized();rel=(rig.pose.bones[fb.name].matrix.inverted()@rig.pose.bones[hb.name].matrix).to_quaternion();rr=(fb.matrix_local.inverted()@hb.matrix_local).to_quaternion();tw=swing_twist_deg(rel@rr.inverted(),seg)[1];rig.pose.bones['B_R_ForearmTwist'].rotation_quaternion=Quaternion(seg,math.radians(max(-85,min(85,.65*tw))));ub=rig.data.bones['B_R_UpperArm'];uax=(ub.matrix_local.inverted()@fb.head_local).normalized();uw=swing_twist_deg(rig.pose.bones[ub.name].rotation_quaternion,uax)[1];rig.pose.bones['B_R_UpperArmTwist'].rotation_quaternion=Quaternion(uax,math.radians(-.5*uw));previous=(A.copy(),C.copy());poses.append({pb.name:pb.rotation_quaternion.copy()for pb in rig.pose.bones if pb.name.startswith('B_R_')});report.append({'frame':f,'proxy_penetration_m':depth,'grip_shift_m':(C-C0).length,'upper_roll_deg':upper,'wrist_swing_deg':r['sw'],'hand_roll_deg':r['tw']})
rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f,pose in enumerate(poses):
 for n,q in pose.items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
act=bpy.data.actions['Dead'];rig.animation_data.action=act;rig.animation_data.action_slot=act.slots[0]
for f in [0,1]:
 for n,q in poses[-1].items():pb=rig.pose.bones[n];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
rig.animation_data.action=None;bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/contact_master.blend'));(P/'review/spear_motion_refinement.json').write_text(json.dumps(report,indent=2));print('SPEAR CLEARANCE',max(r['proxy_penetration_m']for r in report),flush=True)
