"""Fit the library poses against the actual skinned surfaces, retaining the fixed palm frames."""
import bpy,sys,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'));import round1_fit as F
bpy.ops.wm.open_mainfile(filepath=str(P/globals().get('INPUT','work/round1_fitted.blend')));r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];axe=bpy.data.objects['AxeMesh'];sc=bpy.context.scene;F.r=r;F.body=b;F.sc=sc
me=b.data;rest=np.array([v.co[:] for v in me.vertices]);W=np.zeros((len(rest),len(b.vertex_groups)));names=[g.name for g in b.vertex_groups]
for v in me.vertices:
 for g in v.groups:W[v.index,g.group]=g.weight
E=np.array([e.vertices[:] for e in me.edges]);rl=np.linalg.norm(rest[E[:,0]]-rest[E[:,1]],axis=1);pv=np.array([v.value for v in me.attributes['piece'].data]);faces=[p.vertices[:] for p in me.polygons]
def w(sd,ks):return W[:,[i for i,n in enumerate(names) if n.startswith('B_'+sd+'_') and any(k in n for k in ks)]].sum(1)
ids={};ff={};edge={}
for sd in 'RL':
 own=w(sd,['UpperArm','Forearm','Hand','Finger','Clavicle']);arm=w(sd,['UpperArm','Forearm','Hand']);hand=w(sd,['Hand','Finger']);fore=w(sd,['Forearm']);ids[sd+'hand']=np.where(hand>.5)[0];ids[sd+'forearm']=np.where(fore>.5)[0];ff[sd]=[fc for fc in faces if all(own[i]<.2 and pv[i]!=1 for i in fc)];edge[sd]=(arm[E[:,0]]>.3)&(arm[E[:,1]]>.3)
wh=w('R',['Hand','Finger'])+w('L',['Hand','Finger']);ff['axe']=[fc for fc in faces if all(wh[i]<.2 for i in fc)]
ids['head']=np.where((pv==0)&((rest[:,2]>1.67)|((rest[:,2]>1.61+.25*(rest[:,1]+.03))&(rest[:,1]<.025)&(np.abs(rest[:,0])<.20))))[0];shoulder=(pv==0)&(np.abs(rest[:,0])>.12)&(rest[:,2]>1.27)&(rest[:,2]<1.54);ff['head']=[fc for fc in faces if all(shoulder[i] for i in fc)]
headset=set(ids['head']);headfaces=[fc for fc in faces if all(i in headset for i in fc)]
G=F.G;meta=json.loads((P/'work/round1_grip_frames.json').read_text());HF={s:Matrix(meta['frames'][s]) for s in 'RL'};AR=Matrix(meta['right_hand_to_axe']);axerest=r.data.bones['Axe'].matrix_local

def co(obj):
 e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();x=np.array([v.co[:] for v in m.vertices]);e.to_mesh_clear();return x

def depth(tree,points,sel):
 best=0
 for i in sel:
  loc,nrm,fi,d=tree.find_nearest(Vector(points[i]),.12)
  if loc is not None and d>best and (Vector(points[i])-loc).dot(nrm)<-.7*d:best=d
 return best

def measure():
 pts=co(b);ax=co(axe);result={};trees={s:BVHTree.FromPolygons(pts.tolist(),fl) for s,fl in ff.items()}
 for s in 'RL':
  for part in ['hand','forearm']:
   chosen=set(ids[s+part]);partfaces=[fc for fc in faces if all(v in chosen for v in fc)];pairs=BVHTree.FromPolygons(pts.tolist(),partfaces).overlap(trees[s]);crossing=sorted({v for x,y in pairs for v in partfaces[x]});result[s+part]=depth(trees[s],pts,crossing)
 am=F.M('Axe')@axerest.inverted();axis=np.array(am.to_3x3()@Vector((0,0,1)));origin=np.array(am.translation)
 for sd in 'RL':
  cen=np.array(F.M(f'B_{sd}_Hand')@Vector(G[sd]['handle_centre_hand_local']));v=pts[ids[sd+'hand']]-cen;along=v@axis;rad=np.linalg.norm(v-np.outer(along,axis),axis=1);result[sd+'grip']=max(0,.0182-float(rad[abs(along)<.05].min()))
 result['axe']=depth(trees['axe'],ax,range(len(ax)));hp=BVHTree.FromPolygons(pts.tolist(),headfaces).overlap(trees['head']);hi=sorted({v for a,bb in hp for v in headfaces[a]});result['head']=depth(trees['head'],pts,hi);ratio=np.linalg.norm(pts[E[:,0]]-pts[E[:,1]],axis=1)/np.maximum(rl,1e-8);result['G4']=max(float(np.percentile(ratio[mask],99)) for mask in edge.values());return result

def cost(m,angles):
 return 300*sum((max(0,d-(.008 if k=='head' else .0015))*100)**2 for k,d in m.items() if k!='G4')+1000*max(0,m['G4']-1.95)**2+sum(3*max(0,abs(a[0])-88)**2+max(0,a[1]-55)**2 for a in angles)

solutions={};reports={}
for nm in globals().get('ROLES',['Standing','Walking','Running','Attack','Cast','Hit','Fidget']):
 a=bpy.data.actions[nm];rows=[F.sample(a,i) for i in range(int(a.frame_range[1])+1)];out=[];stats=[];previous=np.zeros(5)
 for i,row in enumerate(rows):
  F.apply(row);A0=F.M('Axe')@axerest.inverted();neck=F.M('B_Neck');zs=meta['grip_z'];preferred={s:F.M(f'B_{s}_Forearm').translation for s in 'RL'}
  def evaluate(par):
   F.apply(row);A=A0.copy();A.translation+=Vector(par[:3]);rot=Matrix.Rotation(float(par[3]),3,'X')@Matrix.Rotation(float(par[4]),3,'Z');F.setmat('B_Neck',F.transform(rot@neck.to_3x3(),neck.translation));angles=[]
   for s in 'RL':
    HR=A.to_3x3()@HF[s];target=A@Vector((0,0,zs[s]))-HR@Vector(G[s]['handle_centre_hand_local']);angles.append(F.solvearm(s,target,HR,preferred[s]))
   F.setmat('Axe',F.M('B_R_Hand')@AR@axerest);m=measure()
   score=cost(m,angles)+5*np.dot(par[:3],par[:3])+2*np.dot(par[3:],par[3:])+10000*np.dot(par[:3]-previous[:3],par[:3]-previous[:3])+100*np.dot(par[3:]-previous[3:],par[3:]-previous[3:])
   # A translated child joint must still equal its measured segment length.
   for s in 'RL':
    un,fn,hn,la,lb,*_=F.armdata[s];error=abs((F.M(hn).translation-F.M(fn).translation).length-lb);score+=1e6*error*error
   return float(score),m,F.snapshot(),angles
  par=previous*.95;best,mm,pose,angles=evaluate(par)
  if best>.05:
   for step in [.04,.02,.01,.005]:
    for repeat in range(2):
     for axis in range(5):
      selected=par
      for sign in [-1,1]:
       test=par.copy();test[axis]+=sign*(step if axis<3 else step*3)
       if np.linalg.norm(test[:3])>.26 or max(abs(test[3:]))>math.radians(38):continue
       value,m,p,ang=evaluate(test)
       if value<best:best=value;mm=m;pose=p;angles=ang;selected=test
      par=selected
  previous=par;out.append(pose);stats.append({'frame':i,'correction':par.tolist(),'gates':mm,'angles':angles})
  if i%6==0:print('CONTACT FIT',nm,i,round(best,3),{k:round(v*(1 if k=='G4' else 1000),2) for k,v in mm.items()},flush=True)
 solutions[nm]=out;reports[nm]=stats
 if globals().get('CREATE_CAST',False) and nm=='Attack':
  pause=round(sc.render.fps*16/30*globals().get('TIME_FACTOR',1));hold=round(sc.render.fps*8/30*globals().get('TIME_FACTOR',1));solutions['Cast']=out[:pause+1]+[out[pause]]*hold+out[pause+1:]
for nm,rows in solutions.items():
 bpy.data.actions.remove(bpy.data.actions[nm]);a=bpy.data.actions.new(nm);a.use_fake_user=True;prev={}
 for i,row in enumerate(rows):
  F.apply(row);r.animation_data.action=a
  for n in F.names:
   pb=r.pose.bones[n];q=pb.matrix_basis.to_quaternion()
   if n in prev and q.dot(prev[n])<0:q.negate()
   prev[n]=q.copy();pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.keyframe_insert('rotation_quaternion',frame=i);pb.keyframe_insert('location',frame=i)
  r.animation_data.action=None
 a.use_frame_range=True;a.frame_start=0;a.frame_end=len(rows)-1
 for la in a.layers:
  for st in la.strips:
   for cb in st.channelbags:
    for fc in cb.fcurves:
     for k in fc.keyframe_points:k.interpolation='LINEAR'
(P/globals().get('REPORT','review/round1/contact_fit.json')).write_text(json.dumps(reports,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(P/globals().get('OUTPUT','work/round1_contacts.blend')))
