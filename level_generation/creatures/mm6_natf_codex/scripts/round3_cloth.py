import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
bpy.ops.wm.open_mainfile(filepath=str(P/'work/round3_fitted.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];chains=json.loads(sc['natf_skirt']);N=len(chains)
rest=np.array([c['points']for c in chains]);lengths=np.linalg.norm(np.diff(rest,axis=1),axis=2);out=np.array([[math.cos(c['angle']),math.sin(c['angle']),0]for c in chains]);pelrest=rig.data.bones['B_Pelvis'].matrix_local.copy();rels={}
for c in chains:
 par='B_Pelvis'
 for n in c['bones']:rels[n]=rig.data.bones[par].matrix_local.inverted()@rig.data.bones[n].matrix_local;par=n
caps=[(f'B_{s}_Thigh',f'B_{s}_Calf',.092)for s in 'LR']+[(f'B_{s}_Calf',f'B_{s}_Foot',.074)for s in 'LR']+[(f'B_{s}_Foot',f'B_{s}_Toe0',.064)for s in 'LR']
def delta(Pt,a,b):
 ab=b-a;t=np.clip(np.sum((Pt-a)*ab,axis=-1)/max(np.dot(ab,ab),1e-10),0,1);return Pt-(a+t[...,None]*ab)
report={}
for role in ['Running','Attack']:
 ac=bpy.data.actions[role];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];frames=[];prevq={};worst=0
 for f in range(int(ac.frame_range[1])+1):
  sc.frame_set(f);sp=rig.pose.bones['B_Pelvis'].matrix.copy();M=sp@pelrest.inverted();R=np.array(M.to_3x3());T=np.array(M.translation);X=rest@R.T+T;roots=X[:,0].copy();U=out@R.T
  collision=[(np.array(rig.pose.bones[a].head),np.array(rig.pose.bones[b].head),r+(.045 if a.endswith("Thigh")else .035))for a,b,r in caps]
  for iteration in range(14):
   X[:,1:]=.8*X[:,1:]+.1*(np.roll(X[:,1:],1,axis=0)+np.roll(X[:,1:],-1,axis=0))
   X[:,0]=roots
   for k in range(3):
    d=X[:,k+1]-X[:,k];X[:,k+1]=X[:,k]+d/np.maximum(np.linalg.norm(d,axis=1),1e-9)[:,None]*lengths[:,k,None]
    for a,b,r in collision:
     for midpoint in [False,True]:
      Q=(X[:,k]+X[:,k+1])*.5 if midpoint else X[:,k+1];D=delta(Q,a,b);norm2=np.sum(D*D,axis=1);h=np.sum(D*U,axis=1);shift=np.where(norm2<r*r,np.maximum(0,-h+np.sqrt(np.maximum(0,h*h+r*r-norm2))),0);shift=np.minimum(shift,.10);X[:,k+1]+=U*shift[:,None]*(2 if midpoint else 1)
    X[:,k+1,2]=np.maximum(X[:,k+1,2],.004)
  for c,pts in zip(chains,X):
   par=sp
   for k,n in enumerate(c['bones']):
    base=par@rels[n];d=Vector(pts[k+1])-base.translation;rot=(base.to_3x3()@Vector((0,1,0))).rotation_difference(d.normalized()).to_matrix();world=(rot@base.to_3x3()).to_4x4();world.translation=base.translation;q=(base.inverted()@world).to_quaternion()
    if n in prevq and q.dot(prevq[n])<0:q=-q
    prevq[n]=q.copy();pb=rig.pose.bones[n];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=f);par=world
  worst=max(worst,float(np.max(np.linalg.norm(X-(rest@R.T+T),axis=2))))
 report[role]={'frames':int(ac.frame_range[1])+1,'max_cage_adjustment_m':worst};print('SKIRT',role,report[role],flush=True)
 for layer in ac.layers:
  for strip in layer.strips:
   for bag in strip.channelbags:
    for fc in bag.fcurves:
     if 'Skirt_'in fc.data_path:
      for key in fc.keyframe_points:key.interpolation='LINEAR'
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/round3_cloth.blend'))
