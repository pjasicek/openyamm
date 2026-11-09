"""Mesh-fitted skirt cage; exact-length chains with one-sided leg collision, based on the thief cloak method."""
import bpy,json,math,sys,numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));sys.dont_write_bytecode=True
bpy.ops.wm.open_mainfile(filepath=str(P/'work/rig_adapted.blend'));sc=bpy.context.scene;rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data
rig.animation_data.action=None
for pb in rig.pose.bones:pb.matrix_basis.identity()
bpy.context.view_layer.update();co=np.array([tuple(v.co)for v in me.vertices]);pv=np.array([x.value for x in me.attributes['piece'].data]);centres={i:co[pv==i].mean(0)for i in set(pv.tolist())}
from cloth_region import garment
cloth=garment(me,co,pv)
faces=[tuple(f.vertices)for f in me.polygons if all(cloth[i]for i in f.vertices)];tree=BVHTree.FromPolygons([Vector(v)for v in co],faces)
N=20;levels=[1.015,.86,.70,.53];axis=Vector((-.006,0,0));chains=[]
for c in range(N):
 a=c*math.tau/N;out=Vector((math.cos(a),math.sin(a),0));points=[]
 for z in levels:
  origin=Vector((axis.x,axis.y,z));loc,normal,idx,dist=tree.ray_cast(origin,out,.5)
  if loc is None:
   # The last ring is within the feather fringe; use the continuous skirt surface immediately above it.
   loc,normal,idx,dist=tree.ray_cast(Vector((axis.x,axis.y,max(z,.59))),out,.5)
  assert loc is not None,(c,z)
  points.append([loc.x,loc.y,z])
 chains.append({'angle':a,'points':points,'bones':[f'Skirt_{c:02d}_{k}'for k in range(3)]})
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for c in chains:
 par=rig.data.edit_bones['B_Pelvis']
 for k,n in enumerate(c['bones']):
  b=rig.data.edit_bones.new(n);b.head=Vector(c['points'][k]);b.tail=Vector(c['points'][k+1]);b.parent=par;b.use_connect=k>0;par=b
bpy.ops.object.mode_set(mode='OBJECT');assert len(rig.data.bones)==112
for c in chains:
 for n in c['bones']:body.vertex_groups.new(name=n)
def cw(c,z):
 if z>.96:return {c['bones'][0]:max(0,(1.015-z)/.055),'B_Pelvis':min(1,max(0,(z-.96)/.055))}
 k=0 if z>.86 else 1 if z>.70 else 2;t=(levels[k]-z)/(levels[k]-levels[k+1]);w={c['bones'][k]:1}
 if t<.30 and k>0:q=.5*(1-t/.30);w={c['bones'][k]:1-q,c['bones'][k-1]:q}
 elif t>.70 and k<2:q=.5*(t-.70)/.30;w={c['bones'][k]:1-q,c['bones'][k+1]:q}
 return w
for i in np.where(cloth)[0]:
 x,y,z=centres[pv[i]] if pv[i]>15 else co[i];a=math.atan2(y-axis.y,x-axis.x)%math.tau;u=a*N/math.tau;c=int(u);t=u-c;w={}
 for ch,f in [(chains[c],1-t),(chains[(c+1)%N],t)]:
  for n,v in cw(ch,z).items():w[n]=w.get(n,0)+v*f
 w={max(w,key=w.get):1.0} if pv[i]>15 else dict(sorted(w.items(),key=lambda x:-x[1])[:4]);tot=sum(w.values());assert tot>0
 for g in list(me.vertices[i].groups):body.vertex_groups[g.group].remove([int(i)])
 for n,v in w.items():
  if v>1e-7:body.vertex_groups[n].add([int(i)],float(v/tot),'REPLACE')
attr=me.attributes.get('cloth')or me.attributes.new('cloth','INT','POINT');attr.data.foreach_set('value',cloth.astype(np.int32))
rest=np.array([c['points']for c in chains]);lengths=np.linalg.norm(np.diff(rest,axis=1),axis=2);out=np.array([[math.cos(c['angle']),math.sin(c['angle']),0]for c in chains]);pelrest=rig.data.bones['B_Pelvis'].matrix_local.copy();rels={}
for c in chains:
 par='B_Pelvis'
 for n in c['bones']:rels[n]=rig.data.bones[par].matrix_local.inverted()@rig.data.bones[n].matrix_local;par=n
caps=[(f'B_{s}_Thigh',f'B_{s}_Calf',.092)for s in 'LR']+[(f'B_{s}_Calf',f'B_{s}_Foot',.074)for s in 'LR']+[(f'B_{s}_Foot',f'B_{s}_Toe0',.064)for s in 'LR']
def delta(Pt,a,b):
 ab=b-a;t=np.clip(np.sum((Pt-a)*ab,axis=-1)/max(np.dot(ab,ab),1e-10),0,1);return Pt-(a+t[...,None]*ab)
report={}
for role in ['Standing','Walking','Running','Attack','Cast','Hit','Death','Fidget','Dead']:
 ac=bpy.data.actions[role];rig.animation_data.action=ac;rig.animation_data.action_slot=ac.slots[0];frames=[];prevq={};worst=0
 for f in range(int(ac.frame_range[1])+1):
  sc.frame_set(f);sp=rig.pose.bones['B_Pelvis'].matrix.copy();M=sp@pelrest.inverted();R=np.array(M.to_3x3());T=np.array(M.translation);X=rest@R.T+T;roots=X[:,0].copy();U=out@R.T
  collision=[(np.array(rig.pose.bones[a].head),np.array(rig.pose.bones[b].head),r+.018)for a,b,r in caps]
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
sc['natf_skirt']=json.dumps(chains);(P/'work/skirt_motion.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/rig_cloth.blend'))
