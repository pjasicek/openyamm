import bpy,sys,json,math,numpy as np,runpy
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/assembled.blend'));rig=bpy.data.objects['Rig'];sc=bpy.context.scene
from arm_ik import Side,swing_twist_deg
obj=Side('L');hf=json.loads((P/'work/hand_frames.json').read_text())['L'];g=json.loads((P/'work/shield_grip.json').read_text());gh=Vector(g['handle_centre_hand_local']);ga=Vector(g['handle_axis_hand_local'])
def basis(d,n):d=d.normalized();n=(n-d*n.dot(d)).normalized();return Matrix((d,n,d.cross(n))).transposed()
HF=basis(Vector(hf['long_local']),Vector(hf['palm_local']));report={}
aa=bpy.data.actions['Standing'];rig.animation_data.action=aa;rig.animation_data.action_slot=aa.slots[0];sc.frame_set(0);clav_rest=rig.pose.bones['B_L_Clavicle'].rotation_quaternion.copy()
for ac in bpy.data.actions:
 if ac.name not in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget']:continue
 rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];previous=None;prev_tw=None;prevq={};rolls=[];wrists=[];depths=[];samples=[]
 for f in range(int(ac.frame_range[1])+1):
  sc.frame_set(f);samples.append(rig.pose.bones['B_L_Hand'].head.copy())
 for f,T in enumerate(samples):
  sc.frame_set(f);cl=rig.pose.bones['B_L_Clavicle'];cl.rotation_quaternion=clav_rest.slerp(cl.rotation_quaternion,.15)if ac.name!='Death'else clav_rest;cl.keyframe_insert('rotation_quaternion',frame=f);bpy.context.view_layer.update();S=rig.pose.bones['B_L_UpperArm'].head.copy()
  u=min(1,max(0,(1.15-S.z)/.6))if ac.name=='Death'else 0;u=u*u*(3-2*u);a=u*math.pi/2;n=Vector((.8*math.cos(a),-.6*math.cos(a),math.sin(a)));d=n.copy();palm=Vector((-.8*math.sin(a),.6*math.sin(a),math.cos(a)));R=basis(d,palm)@HF.inverted()
  if ac.name=='Death':T=S+Vector((.32,-.21,-.15));T.z=max(T.z,S.z-.025,.30,.89*math.cos(a)-.10*math.sin(a)+.04)
  else:T.x=.40 if ac.name=='Running'else .36 if ac.name=='Walking'else .34;T.y=min(T.y,-.18);T.z+=.025
  if (T-S).length>(obj.l1+obj.l2)*.97:T=S+(T-S).normalized()*(obj.l1+obj.l2)*.97
  axis=(T-S).normalized();candidates=[];C=T+R@gh
  for deg in range(-180,181,5):
   r=obj.pose_anatomical(T,R,Quaternion(axis,math.radians(deg))@Vector((0,-1,0)));base=rig.pose.bones['B_L_Clavicle'].matrix.to_3x3()@obj.rel['Arm'];roll=abs(swing_twist_deg((base.inverted()@r['Ra']).to_quaternion(),obj.uA)[1]);rel=(r['Rf']@obj.rel['Hand']).inverted()@R;ax=(r['Rf']@obj.rel['Hand']).inverted()@(r['W']-r['E']);sw,tw=swing_twist_deg(rel.to_quaternion(),ax.normalized());tw=prev_tw+(tw-prev_tw+180)%360-180 if prev_tw is not None else tw;depth=max(0,(r['E']-C).dot(n)+.015);physical=math.degrees((r['W']-r['E']).angle(d));cost=roll*.2+max(0,roll-45)*50+max(0,physical-55)*80+max(0,abs(tw)-135)*5+abs(tw)*.01+depth*3000
   if previous is not None:
    delta=math.degrees(previous.rotation_difference(r['Ra'].to_quaternion()).angle);cost+=.5*delta+20*max(0,delta-6)
   candidates.append((cost,r,roll,physical,tw,depth))
  _,r,roll,sw,tw,dep=min(candidates,key=lambda x:x[0]);prev_tw=tw;share=max(-85,min(85,tw*.6));r['Rf']=Quaternion((r['W']-r['E']).normalized(),math.radians(share)).to_matrix()@r['Rf'];obj.apply(r);previous=r['Ra'].to_quaternion();rolls.append(roll);wrists.append((sw,abs(tw-share)));depths.append(dep)
  for part in ['UpperArm','Forearm','Hand']:
   pb=rig.pose.bones['B_L_'+part];q=pb.rotation_quaternion.copy()
   if part in prevq and q.dot(prevq[part])<0:q=-q
   prevq[part]=q.copy();pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
 report[ac.name]={'upper_roll_max':max(rolls),'wrist_axis_bend_max':max(x[0]for x in wrists),'wrist_twist_max':max(x[1]for x in wrists),'elbow_shield_clearance_failure_m':max(depths)};print('SHIELD IK',ac.name,report[ac.name],flush=True)
# The corpse inherits the fitted last death pose.
a=bpy.data.actions['Death'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(int(a.frame_range[1]));last={pb.name:pb.rotation_quaternion.copy()for pb in rig.pose.bones};a=bpy.data.actions['Dead'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
for f in range(int(a.frame_range[1])+1):
 for name,q in last.items():pb=rig.pose.bones[name];pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f)
# Refit the prop's immutable bind frame to the new neutral hand orientation and exact grip centre.
a=bpy.data.actions['Standing'];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];sc.frame_set(0);H=rig.pose.bones['B_L_Hand'].matrix.copy();C=H@gh;X=(H.to_3x3()@ga).normalized();n=(H.to_3x3()@Vector(hf['long_local'])).normalized();n=(n-X*n.dot(X)).normalized();Z=-X.cross(n)
if Z.z<0:X=-X;Z=-Z
M=Matrix((X,-n,Z)).transposed().to_4x4();M.translation=C+n*.045-Z*.26;new=rig.data.bones['B_L_Hand'].matrix_local@H.inverted()@M;old=rig.data.bones['LeafShield'].matrix_local.copy();delta=new@old.inverted();bpy.data.objects['LeafShield'].data.transform(delta);rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones['LeafShield'].matrix=new;rig.data.edit_bones['LeafShield'].length=.1;bpy.ops.object.mode_set(mode='OBJECT')
ns=runpy.run_path(str(P/'scripts/bake_twist.py'));[ns['bake_twist'](a)for a in bpy.data.actions if a.use_fake_user]
# Equipment is included in the floor correction; do not let a skirt feather or shield point fall below the floor.
root=rig.pose.bones['B_Pelvis'];inv=rig.data.bones['B_Pelvis'].matrix_local.to_3x3().inverted();floor={};obs=[bpy.data.objects[n]for n in ['Body','ForearmBlade','LeafShield']]
for a in bpy.data.actions:
 if a.name not in [*report,'Dead']:continue
 rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0];end=int(a.frame_range[1]);maxlift=0
 for it in range(2):
  shifts=np.zeros(end+1);roots=[]
  for f in np.arange(0,end+.001,.5):
   sc.frame_set(int(f),subframe=float(f%1));low=100
   for ob in obs:
    ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();low=min(low,min(v.co.z for v in me.vertices));ev.to_mesh_clear()
   dz=max(0,.001-low);shifts[int(f)]=max(shifts[int(f)],dz);shifts[min(end,math.ceil(f))]=max(shifts[min(end,math.ceil(f))],dz)
  for f in range(end+1):sc.frame_set(f);roots.append(root.location.copy()+inv@Vector((0,0,float(shifts[f]))))
  for f,l in enumerate(roots):root.location=l;root.keyframe_insert('location',frame=f)
  maxlift=max(maxlift,float(shifts.max()))
 floor[a.name]=maxlift
for a in bpy.data.actions:
 for layer in a.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     for key in fc.keyframe_points:key.interpolation='LINEAR'
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
blade=bpy.data.objects['ForearmBlade'];M=rig.data.bones['ForearmBlade'].matrix_local;iv=M.inverted()
for v in blade.data.vertices:
 q=iv@v.co
 if q.z>.17:q.x+=.032*min(1,max(0,(q.z-.17)/.065));v.co=M@q
(P/'review/equipment_fit.json').write_text(json.dumps({'arm':report,'floor_lifts_m':floor,'shield_bind':[list(r)for r in new]},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/production_master.blend'))
import common
common.workbench_clay(sc,textured=True)
for role in ['Standing','Attack','Cast','Death','Dead']:
 a=bpy.data.actions[role];rig.animation_data.action=a;rig.animation_data.action_slot=a.slots[0]
 for i in [0,2,4]:
  f=a.frame_range[1]*i/4;sc.frame_set(int(f),subframe=float(f%1));lo,hi=common.world_bounds(obs);c=(lo+hi)*.5;h=max(1.85,(hi-lo).z*1.12,(hi-lo).y*1.4,(hi-lo).x*1.4);common.render_views(str(P/f'review/fit_{role}_{i}'),c.z,h,views=('front','left','three_quarter'),resolution=(400,560),target=(c.x,c.y))
