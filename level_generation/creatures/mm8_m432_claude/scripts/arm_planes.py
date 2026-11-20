"""Choose smooth elbow planes over each whole clip, preserving both wrist targets and hand orientation."""
import bpy,sys,math,json,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
import armik
from mathutils.bvhtree import BVHTree
bpy.ops.wm.open_mainfile(filepath=str(P/os.environ.get('ARM_INPUT','work/rig_gripped.blend')));r=bpy.data.objects['Rig'];sc=bpy.context.scene
limit=int(os.environ.get('ARM_PHI','170'));PH=np.arange(-limit,limit+1,10);report={}
body=bpy.data.objects['Body'];bn=[g.name for g in body.vertex_groups]
arm_weight=np.array([sum(e.weight for e in v.groups if any(k in bn[e.group] for k in ('UpperArm','Forearm','Hand','Finger','Clavicle'))) for v in body.data.vertices])
body_faces=[tuple(f.vertices) for f in body.data.polygons if all(arm_weight[i]<.2 for i in f.vertices)]
def setact(a):
 r.animation_data.action=a
 if a is not None and len(a.slots):r.animation_data.action_slot=a.slots[0]
def snap():return {b.name:b.matrix_basis.copy() for b in r.pose.bones}
def restore(p):
 for n,m in p.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def costs(s):
 fb,hb=r.data.bones[f'B_{s}_Forearm'],r.data.bones[f'B_{s}_Hand'];fr=r.pose.bones[fb.name].matrix.to_3x3()@fb.matrix_local.to_3x3().inverted();hr=r.pose.bones[hb.name].matrix.to_3x3()@hb.matrix_local.to_3x3().inverted()
 rel=(fr.inverted()@hr).to_quaternion();ax=(hb.head_local-fb.head_local).normalized();sw,tw=armik.split_swing_twist(rel,ax)
 return math.degrees(min(sw.angle,2*math.pi-sw.angle)),math.degrees(tw)
for name in os.environ.get('ARM_CLIPS','Standing,Walking,Running,Attack,Hit,Cast,Death').split(','):
 ac=bpy.data.actions[name];poses=[]
 for f in range(int(ac.frame_range[1])+1):setact(ac);sc.frame_set(f);poses.append(snap())
 setact(None);report[name]={}
 for side in os.environ.get('ARM_SIDES',('RLRL' if name=='Attack' else 'RL')):
  tables=[];candidates=[]
  states=[(int(phi),roll) for phi in PH for roll in (range(-180,180,15) if name=='Attack' else [0])]
  grip=json.loads((P/f'work/grip_pose{"" if side=="R" else "_L"}.json').read_text());gc=Vector(grip['handle_centre_hand_local']);ga=Vector(grip['handle_axis_hand_local'])
  for frame,pose in enumerate(poses):
   restore(pose);sh=armik.W(r,f'B_{side}_UpperArm').translation.copy();el=armik.W(r,f'B_{side}_Forearm').translation.copy();h=armik.W(r,f'B_{side}_Hand').copy();target=h.translation;u=(target-sh).normalized();pole=(el-sh)-u*(el-sh).dot(u);table=[];opts=[]
   if pole.length<1e-6:pole=Vector((0,0,-1))
   tree=None
   if name=='Attack':
    ev=body.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();co=[v.co.copy() for v in me.vertices];ev.to_mesh_clear();tree=BVHTree.FromPolygons(co,body_faces)
   desired_centre=h@gc
   if side=='L' and name in ('Standing','Walking','Running','Attack','Hit','Fidget'):
    gr=json.loads((P/'work/grip_pose.json').read_text());rh=r.pose.bones['B_R_Hand'].matrix;desired_centre=rh@Vector(gr['handle_centre_hand_local'])-(rh.to_3x3()@Vector(gr['handle_axis_hand_local']))*(.115+.03*math.sin(math.pi*frame/(len(poses)-1))**2 if name=='Attack' else .115)
   other='L' if side=='R' else 'R';oe=r.pose.bones[f'B_{other}_Forearm'].head.copy();ow=r.pose.bones[f'B_{other}_Hand'].head.copy();ov=ow-oe
   for phi,roll in states:
    restore(pose);handrot=Quaternion(h.to_3x3()@ga,math.radians(roll)).to_matrix()@h.to_3x3().normalized();wrist=desired_centre-handrot@gc
    reach=armik.solve(r,side,wrist,pole=sh+Quaternion(u,math.radians(float(phi)))@pole,hand_rot=handrot)
    sw,tw=costs(side);bias=30 if side=='R' else -30
    contact=0.
    if tree is not None:
     a,e,z=[r.pose.bones[f'B_{side}_{n}'].head.copy() for n in ('UpperArm','Forearm','Hand')]
     for start,end,radius in ((a,e,.07),(e,z,.07)):
      for t in (.2,.4,.6,.8):
       pt=start.lerp(end,t);loc,normal,idx,dist=tree.find_nearest(pt,.2)
       if loc is not None:
        signed=dist if (pt-loc).dot(normal)>=0 else -dist;contact+=max(0,radius-signed)**2
     for t in (.1,.2,.3,.4,.5,.6,.7,.8,.9):
      pt=e.lerp(z,t);proj=max(0,min(1.0,(pt-oe).dot(ov)/ov.length_squared));distance=(pt-oe-ov*proj).length;contact+=max(0,.105-distance)**2
    table.append(100000000*max(0,reach-.999)**2+10000000*contact+sw+.02*sw*sw+.6*abs(tw-bias)+1000*max(0,abs(tw)-90)**2+1000000*max(0,sw-60)**2+.05*abs(phi)+.15*abs(roll))
    opts.append(({f'B_{side}_{n}':r.pose.bones[f'B_{side}_{n}'].matrix_basis.copy() for n in ('UpperArm','Forearm','Hand')},sw,tw))
   tables.append(table);candidates.append(opts)
  state_values=np.array(states);transition=.65*np.abs(state_values[:,None,0]-state_values[None,:,0])+.5*np.minimum(np.abs(state_values[:,None,1]-state_values[None,:,1]),360-np.abs(state_values[:,None,1]-state_values[None,:,1]));acc=np.array(tables[0]);back=[]
  for row in tables[1:]:
   sums=acc[:,None]+transition;back.append(np.argmin(sums,axis=0));acc=np.min(sums,axis=0)+row
  state=int(np.argmin(acc));path=[state]
  for b in reversed(back):state=int(b[state]);path.append(state)
  path.reverse();swings=[];twists=[]
  for f,state in enumerate(path):poses[f].update(candidates[f][state][0]);swings.append(candidates[f][state][1]);twists.append(candidates[f][state][2])
  report[name][side]={'phi_roll':[states[i] for i in path],'swings':swings,'twists':twists,'max_swing':max(swings),'max_abs_twist':max(map(abs,twists))}
  print('ARMPLANES',name,side,report[name][side]['max_swing'],report[name][side]['max_abs_twist'],flush=True)
 setact(ac);prev={}
 for f,p in enumerate(poses):
  for n,m in p.items():
   if not any(k in n for k in ('UpperArm','Forearm','Hand')):continue
   q=m.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q;b=r.pose.bones[n];b.rotation_mode='QUATERNION';b.rotation_quaternion=q;b.keyframe_insert('rotation_quaternion',frame=f)
 setact(None)
(P/'work/arm_plane_fit.json').write_text(json.dumps(report,indent=1));bpy.ops.wm.save_as_mainfile(filepath=str(P/os.environ.get('ARM_OUTPUT','work/rig_armplanes.blend')))
