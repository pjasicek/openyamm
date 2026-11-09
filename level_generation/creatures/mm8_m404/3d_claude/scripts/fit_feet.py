"""Fit planted reptilian soles and the selected walk's support phases with fixed-length legs."""
import bpy,json,sys,math,numpy as np
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
bpy.ops.wm.open_mainfile(filepath=str(p/'work/rig_feet.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];sc=bpy.context.scene
names=[g.name for g in body.vertex_groups];rest=np.array([v.co[:] for v in body.data.vertices]);sole={}
for s in 'LR':
 mask=np.array([sum(g.weight for g in v.groups if names[g.group] in ('B_'+s+'_Foot','B_'+s+'_Toe0'))>.3 for v in body.data.vertices]);ids=np.where(mask)[0];ids=ids[rest[ids,2]<rest[ids,2].min()+.005];along=-rest[ids,1]
 sole[s]=(ids,ids[along<=np.quantile(along,.3)],ids[along>=np.quantile(along,.7)])
def setact(a):
 rig.animation_data.action=a
 if a is not None and len(a.slots):rig.animation_data.action_slot=a.slots[0]
def restore(snap):
 for n,M in snap.items():rig.pose.bones[n].matrix_basis=M
 bpy.context.view_layer.update()
def posed():
 bpy.context.view_layer.update();ob=body.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ob.to_mesh();c=np.array([v.co[:] for v in m.vertices]);ob.to_mesh_clear();return c
def solve(side,T,R):
 un,kn,fn=['B_'+side+'_'+n for n in ('Thigh','Calf','Foot')];U,K,F=[armik.W(rig,n).copy() for n in (un,kn,fn)];S,E,W=[m.translation.copy() for m in (U,K,F)];a,b=(E-S).length,(W-E).length
 d=T-S;reach=d.length/(a+b)
 assert reach<1.03,(side,reach)
 if reach>.999:T=S+d.normalized()*(a+b)*.999;d=T-S
 u=d.normalized();old=(W-S).normalized();v=E-S-old*(E-S).dot(old);v=old.rotation_difference(u)@v;v=(v-u*v.dot(u)).normalized();ca=max(-1,min(1,(a*a+d.length*d.length-b*b)/(2*a*d.length)))
 target=S+a*(u*ca+v*math.sqrt(max(0,1-ca*ca)));q=(E-S).rotation_difference(target-S);armik.set_world(rig,un,armik.rot_world(U,q.to_matrix()@U.to_3x3()))
 K=armik.W(rig,kn).copy();W=armik.W(rig,fn).translation.copy();q=(W-K.translation).rotation_difference(T-K.translation);armik.set_world(rig,kn,armik.rot_world(K,q.to_matrix()@K.to_3x3()))
 armik.set_world(rig,fn,armik.rot_world(armik.W(rig,fn),R))
setact(bpy.data.actions['Standing']);sc.frame_set(0);standing_z=armik.W(rig,'B_Pelvis').translation.z
report={}
for label in ('Standing','Fidget','Walking'):
 act=bpy.data.actions[label];frames=np.arange(0,float(act.frame_range[1])+.01,.25);source=[]
 for f in frames:
  setact(act);sc.frame_set(int(f),subframe=float(f%1));co=posed();source.append({'snap':{b.name:b.matrix_basis.copy() for b in rig.pose.bones},'low':{s:float(co[sole[s][0],2].min()) for s in 'LR'},'pelvis_z':armik.W(rig,'B_Pelvis').translation.z})
 lift={s:np.array([max(0,row['low'][s]-row['low']['R' if s=='L' else 'L']) for row in source]) for s in 'LR'}
 if label=='Walking':
  for s in 'LR':lift[s]*=.100/max(lift[s].max(),1e-6)
 else:lift={s:np.zeros(len(source)) for s in 'LR'}
 median_z=np.median([r['pelvis_z'] for r in source]);keys=[];errors=[]
 for i,(f,row) in enumerate(zip(frames,source)):
  setact(None);restore(row['snap'])
  if label=='Walking':
   M=armik.W(rig,'B_Pelvis').copy();M.translation.z=standing_z+.035+.15*(row['pelvis_z']-median_z);armik.set_world(rig,'B_Pelvis',M)
  targets={}
  for s in 'LR':
   fn='B_'+s+'_Foot';ids,heel,toe=sole[s];co=posed();M=armik.W(rig,fn).copy()
   _,_,vt=np.linalg.svd(co[ids]-co[ids].mean(0));normal=Vector(vt[-1]);normal=normal if normal.z>0 else -normal
   q=normal.rotation_difference(Vector((0,0,1)));R=q.to_matrix()@M.to_3x3();direction=q@Vector(co[toe].mean(0)-co[heel].mean(0));direction.z=0;q=direction.rotation_difference(Vector((0,-1,0)));R=q.to_matrix()@R
   armik.set_world(rig,fn,armik.rot_world(M,R));co=posed();T=M.translation.copy();T.z+=.002+lift[s][i]-co[ids,2].min()
   if label=='Walking':
    hip=armik.W(rig,'B_'+s+'_Thigh').translation;T.x=hip.x+.5*(T.x-hip.x);T.y=hip.y+.5*(T.y-hip.y)
   targets[s]=(T,R)
  lower=0.
  for s,(T,R) in targets.items():
   U,K,F=[armik.W(rig,'B_'+s+'_'+n).translation for n in ('Thigh','Calf','Foot')];length=(K-U).length+(F-K).length;horizontal=(T.x-U.x)**2+(T.y-U.y)**2
   assert horizontal<(length*.995)**2,'Foot plan beyond leg reach'
   lower=max(lower,U.z-T.z-math.sqrt((length*.995)**2-horizontal))
  if lower>0:
   M=armik.W(rig,'B_Pelvis').copy();M.translation.z-=lower;armik.set_world(rig,'B_Pelvis',M)
  for s,(T,R) in targets.items():solve(s,T,R)
  co=posed();errors.append({s:float(co[sole[s][0],2].min()) for s in 'LR'})
  keys.append({n:(rig.pose.bones[n].rotation_quaternion.copy(),rig.pose.bones[n].location.copy()) for n in ['B_Pelvis']+['B_'+s+'_'+b for s in 'LR' for b in ('Thigh','Calf','Foot')]})
 setact(act);prev={}
 for f,key in zip(frames,keys):
  for n,(q,l) in key.items():
   pb=rig.pose.bones[n]
   if n in prev and q.dot(prev[n])<0:q=-q
   prev[n]=q.copy();pb.rotation_quaternion=q;pb.location=l;pb.keyframe_insert('rotation_quaternion',frame=float(f))
   if n=='B_Pelvis':pb.keyframe_insert('location',frame=float(f))
 report[label]={'minimum_z':min(v for e in errors for v in e.values()),'peak_z':{s:max(e[s] for e in errors) for s in 'LR'}}
 print('FEET_FIT',label,report[label],flush=True)
json.dump(report,open(p/'work/feet_fit.json','w'),indent=2)
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/rig_feet_fitted.blend'))
