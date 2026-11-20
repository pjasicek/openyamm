"""Fit a closed 12-chain skirt cage to the measured generated cloth surface."""
import bpy,sys,json,math,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/body_complete.blend'))
sc=bpy.context.scene;rig=bpy.data.objects['Rig'];ob=bpy.data.objects['Body'];me=ob.data
rig.animation_data.action=None
for b in rig.pose.bones:b.matrix_basis.identity()
bpy.context.view_layer.update()
pv=np.array([a.value for a in me.attributes['piece'].data]);co=np.array([v.co[:] for v in me.vertices])
ids=np.flatnonzero(pv==100);faces=[tuple(f.vertices) for f in me.polygons if all(pv[i] in (0,100) for i in f.vertices)]
tree=BVHTree.FromPolygons(co.tolist(),faces)
axis=np.array(rig.data.bones['B_Pelvis'].head_local);axis[2]=0
def surface(deg,z):
 a=math.radians(deg);d=Vector((math.sin(a),math.cos(a),0));o=Vector((axis[0],axis[1],z));hits=[];dist=0
 while dist<.8:
  h,_,_,L=tree.ray_cast(o+d*(dist+.0001),d,.8-dist)
  if h is None:break
  hits.append(h);dist+=L+.0001
 return (hits[0]+hits[-1])*.5 if hits else None
chains=[]
for deg in np.arange(-180,180,30):
 ang=np.degrees(np.arctan2(co[ids,0]-axis[0],co[ids,1]-axis[1]))
 near=ids[abs((ang-deg+180)%360-180)<12]
 low=float(co[near,2].min());hem=max(low+.025,.22)
 pts=[surface(deg,z) for z in (1.055,.91,.765,.62,.475,.33)]
 for dz in np.arange(0,.16,.01):
  h=surface(deg,hem+dz)
  if h is not None:break
 pts.append(h)
 assert all(x is not None for x in pts),(deg,hem,pts)
 chains.append({'deg':float(deg),'pts':[list(x) for x in pts]})
for o in bpy.data.objects:o.select_set(o==rig)
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for j,c in enumerate(chains):
 par=rig.data.edit_bones['B_Pelvis'];c['bones']=[]
 for k in range(6):
  b=rig.data.edit_bones.new(f'Skirt_{j:02}_{k}');b.head=c['pts'][k];b.tail=c['pts'][k+1]
  b.parent=par;b.use_connect=k>0;b.use_deform=True;par=b;c['bones'].append(b.name)
bpy.ops.object.mode_set(mode='OBJECT')
for c in chains:
 for n in c['bones']:ob.vertex_groups.new(name=n)
def sm(x,a,b):
 v=np.clip((x-a)/(b-a),0,1);return float(v*v*(3-2*v))
def vertical(c,z):
 # Linear between bone midpoints gives a broad, continuous bend along the dress.
 mid=[(c['pts'][k][2]+c['pts'][k+1][2])*.5 for k in range(6)]
 if z>=mid[0]:return {c['bones'][0]:1}
 for k in range(5):
  if z>=mid[k+1]:
   u=(mid[k]-z)/(mid[k]-mid[k+1]);return {c['bones'][k]:1-u,c['bones'][k+1]:u}
 return {c['bones'][5]:1}
W={}
for i in ids:
 x,y,z=co[i];a=(math.degrees(math.atan2(x-axis[0],y-axis[1]))+180)/30
 j=int(math.floor(a))%12;t=a-math.floor(a);w={}
 for c,share in ((chains[j],1-t),(chains[(j+1)%12],t)):
  for n,v in vertical(c,z).items():w[n]=w.get(n,0)+v*share
 u=sm(z,.96,1.055);w={n:v*(1-u) for n,v in w.items()};w['B_Pelvis']=u;W[int(i)]=w
adj={int(i):[] for i in ids}
for e in me.edges:
 a,b=e.vertices
 if a in adj and b in adj:adj[a].append(b);adj[b].append(a)
for _ in range(2):
 new={}
 for i,w in W.items():
  out={n:v*.6 for n,v in w.items()}
  for j in adj[i]:
   for n,v in W[j].items():out[n]=out.get(n,0)+.4*v/len(adj[i])
  new[i]=out
 W=new
for i,w in W.items():
 for g in list(me.vertices[i].groups):ob.vertex_groups[g.group].remove([i])
 keep=sorted(w.items(),key=lambda x:-x[1])[:4];total=sum(v for _,v in keep)
 for n,v in keep:
  if v>1e-6:ob.vertex_groups[n].add([i],v/total,'REPLACE')
sc['skirt_chains']=json.dumps(chains)
print('SKIRT',len(ids),'vertices',len(rig.data.bones),'bones')
bpy.ops.wm.save_as_mainfile(filepath=str(p/'work/skirt_rig.blend'))
