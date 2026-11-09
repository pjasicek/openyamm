"""Fit separate robe, cuff, hair and tassel chains; keep all deformation within the 128-joint palette."""
from pathlib import Path
import bpy,json,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/motion_twist.blend'))
rig=bpy.data.objects['Rig'];body=bpy.data.objects['Body'];me=body.data;sc=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([a.value for a in me.attributes['piece'].data]);gr=np.array([a.value for a in me.attributes['garment_region'].data])
robe=(pv==0)&(gr==1)
faces=[tuple(f.vertices) for f in me.polygons if all(robe[i] for i in f.vertices)]
tree=BVHTree.FromPolygons(co.tolist(),faces)
axis=np.array(rig.data.bones['B_Pelvis'].head_local);chains=[]
def add(name,kind,parent,pts,**meta):
 c=dict(name=name,kind=kind,parent=parent,pts=np.array(pts).tolist(),**meta);c['bones']=[name+'_'+str(i) for i in range(len(pts)-1)];chains.append(c);return c
for i in range(12):
 a=2*math.pi*i/12;d=Vector((math.sin(a),math.cos(a),0));pts=[]
 for z in [1.05,.79,.53,.28,.03]:
  q,_,_,_=tree.ray_cast(Vector((axis[0],axis[1],z)),d,.6)
  assert q is not None,(i,z)
  pts.append(tuple(q))
 add(f'Robe_{i:02}','robe','B_Pelvis',pts,angle=a)
# Cuffs hang from two locations along each forearm, with a smooth attachment band around the arm itself.
for side,sign in [('L',1),('R',-1)]:
 a=np.array(rig.data.bones[f'B_{side}_Forearm'].head_local);b=np.array(rig.data.bones[f'B_{side}_Hand'].head_local)
 for k,t in enumerate([.2,1.]):
  root=a+(b-a)*t;mask=(pv==0)&~robe&(co[:,0]*sign>.18)&(abs(co[:,0]-root[0])<.045)&(co[:,2]<root[2]-.07)
  assert mask.sum()>4
  z=np.quantile(co[mask,2],.04)+.008;low=co[mask & (co[:,2]<z+.045)].mean(0)
  end=np.array([root[0],low[1],z]);pts=[root+(end-root)*f for f in np.linspace(0,1,4)]
  add(f'Cuff_{side}_{k}','cuff',f'B_{side}_ForearmTwist',pts,side=side,t=t)
for side,sign in [('L',1),('R',-1)]:
 pts=[]
 for z in [1.52,1.32,1.13]:
  mask=(pv==1)&(co[:,0]*sign>0)&(co[:,1]>.015)&(abs(co[:,2]-z)<.055)
  assert mask.sum()>3
  q=co[mask].mean(0);q[2]=z;pts.append(q)
 add('Hair_'+side,'hair','B_Head',pts,side=side)
for piece in [5,6]:
 pts=co[pv==piece];root=pts[pts[:,2]>1.06].mean(0);end=pts[pts[:,2]<pts[:,2].min()+.04].mean(0)
 add('Tassel_'+str(piece),'tassel','B_Spine',[root,(root+end)/2,end],piece=piece)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');eb=rig.data.edit_bones
for c in chains:
 par=eb[c['parent']]
 for i,n in enumerate(c['bones']):
  b=eb.new(n);b.head=c['pts'][i];b.tail=c['pts'][i+1];b.parent=par;b.use_connect=i>0;par=b
bpy.ops.object.mode_set(mode='OBJECT')
assert len(rig.data.bones)==124,len(rig.data.bones)
for c in chains:
 for n in c['bones']:body.vertex_groups.new(name=n)
def smooth(t):
 t=np.clip(t,0,1);return float(t*t*(3-2*t))
def cw(c,z):
 zs=np.array(c['pts'])[:,2];k=int(np.clip(np.searchsorted(-zs,-z)-1,0,len(zs)-2));t=(zs[k]-z)/(zs[k]-zs[k+1]);w={c['bones'][k]:1.}
 if t<.35 and k>0:
  b=.5*np.clip(1-t/.35,0,1);w={c['bones'][k]:1-b,c['bones'][k-1]:b}
 elif t>.65 and k<len(zs)-2:
  b=.5*np.clip((t-.65)/.35,0,1);w={c['bones'][k]:1-b,c['bones'][k+1]:b}
 return w
def mix(a,b,t):
 w={n:v*(1-t) for n,v in a.items()}
 for n,v in b.items():w[n]=w.get(n,0)+v*t
 return w
wv={};region=np.zeros(len(co),int)
for v in me.vertices:
 i=v.index;q=co[i];old={body.vertex_groups[g.group].name:g.weight for g in v.groups};w=None
 if robe[i]:
  a=math.atan2(q[0]-axis[0],q[1]-axis[1])%(2*math.pi);f=a/(2*math.pi)*12;k=int(f)
  w=mix(cw(chains[k],q[2]),cw(chains[(k+1)%12],q[2]),f-k)
  w=mix(w,{'B_Pelvis':1},smooth((q[2]-.97)/.105));region[i]=1
 elif pv[i]==0 and abs(q[0])>.19:
  side='L' if q[0]>0 else 'R';a=np.array(rig.data.bones[f'B_{side}_Forearm'].head_local);b=np.array(rig.data.bones[f'B_{side}_Hand'].head_local)
  t=float(np.clip((q[0]-a[0])/(b[0]-a[0]),0,1));z=(a+(b-a)*t)[2];drop=z-q[2]
  blend=smooth((drop-.035)/.09)
  if blend>0:
   cs=[c for c in chains if c['kind']=='cuff' and c['side']==side]
   w=mix(old,mix(cw(cs[0],q[2]),cw(cs[1],q[2]),float(np.clip((t-.2)/.8,0,1))),blend);region[i]=2 if side=='L' else 3
 elif pv[i]==1:
  cs=[c for c in chains if c['kind']=='hair'];h=mix(cw(cs[1],q[2]),cw(cs[0],q[2]),float(np.clip((q[0]+.05)/.1,0,1)))
  w=mix({'B_Head':1},h,smooth((1.54-q[2])/.12)*smooth((q[1]-.005)/.03));region[i]=4
 elif pv[i] in (5,6):
  c=next(c for c in chains if c.get('piece')==pv[i]);w=mix(cw(c,q[2]),{c['parent']:1},smooth((q[2]-1.02)/.06));region[i]=5
 if w is not None:wv[i]=w
# Diffuse only inside each cloth region, preserving attachment boundaries and material ownership.
adj=[[] for _ in co]
for e in me.edges:
 a,b=e.vertices
 if region[a] and region[a]==region[b]:adj[a].append(b);adj[b].append(a)
for _ in range(2):
 nxt={}
 for i,w in wv.items():
  nb=[j for j in adj[i] if j in wv]
  avg={}
  for j in nb:
   for n,x in wv[j].items():avg[n]=avg.get(n,0)+x/max(1,len(nb))
  nxt[i]=mix(w,avg,.3) if nb else w
 wv=nxt
for i,w in wv.items():
 for g in body.vertex_groups:g.remove([i])
 top=sorted(w.items(),key=lambda x:-x[1])[:8];total=sum(x for _,x in top)
 for n,x in top:
  if x>1e-5:body.vertex_groups[n].add([i],x/total,'REPLACE')
a=me.attributes.get('cloth_region') or me.attributes.new('cloth_region','INT','POINT');a.data.foreach_set('value',region)
sc['garment_chains']=json.dumps(chains)
(p/'work/garment_chains.json').write_text(json.dumps(chains,indent=2)+'\n')
print('GARMENT_RIG',len(rig.data.bones),dict(zip(*np.unique(region,return_counts=True))))
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/motion_cloth_rig.blend'))
