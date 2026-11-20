"""Fit the native rearward tail without changing body or head topology."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);parts=np.array([x.value for x in me.attributes['part'].data])
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index]!=5],context='VERTS')
def section(p,n):
 b=bm.copy();cut=bmesh.ops.bisect_plane(b,geom=list(b.verts)+list(b.edges)+list(b.faces),plane_co=Vector(p),plane_no=Vector(n));edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
 adj={}
 for e in edges:
  a,c=e.verts;adj.setdefault(a,[]).append(c);adj.setdefault(c,[]).append(a)
 seen=set();out=[]
 for v in adj:
  if v in seen:continue
  q=[v];vs=set()
  while q:
   x=q.pop()
   if x in vs:continue
   vs.add(x);seen.add(x);q+=adj[x]
  es=[e for e in edges if e.verts[0] in vs];length=sum(e.calc_length() for e in es)
  if length>.01:
   c=sum(((e.verts[0].co+e.verts[1].co)*.5*e.calc_length() for e in es),Vector())/length;out.append((np.array(c),length/(2*math.pi)))
 b.free()
 return min(out,key=lambda x:np.linalg.norm(x[0]-p)) if out else (np.array(p),.01)
raw=np.array([[-.01,.015,1.17],[-.01,-.02,1.05],[-.01,-.065,.9],[-.01,-.13,.75],[-.01,-.165,.6],[-.02,-.16,.44],[-.045,-.07,.29],[-.11,.07,.155],[-.21,.25,.13],[-.35,.405,.16],[-.45,.51,.23],[-.5,.575,.34],[-.53,.605,.45],[-.545,.63,.58]])
for _ in range(3):
 old=raw.copy()
 for i in range(len(raw)-1):
  n=old[min(i+1,len(old)-1)]-old[max(0,i-1)];raw[i]=section(old[i],n)[0]
raw[0,0]=0
# Smooth the measured centreline and resample by distance.
for _ in range(2):
 pts=[raw[0]]
 for a,b in zip(raw[:-1],raw[1:]):pts.extend([.75*a+.25*b,.25*a+.75*b])
 pts.append(raw[-1]);raw=np.array(pts)
arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];samples=np.linspace(0,arc[-1],30);old=np.column_stack([np.interp(samples,arc,raw[:,i]) for i in range(3)])
new=old.copy();new[:,0]=-.01
for i in range(1,len(new)):
 d=old[i]-old[i-1];new[i,1]=new[i-1,1]+(1 if d[1]>=0 else -1)*np.linalg.norm(d[:2])
# Parallel transport gives the tail a continuous material frame instead of a twist at the bend.
def frames(points):
 t=np.gradient(points,axis=0);t/=np.linalg.norm(t,axis=1)[:,None];side=Vector((1,0,0));out=[];prev=Vector(t[0])
 for v in t:
  v=Vector(v);side=prev.rotation_difference(v)@side;side=(side-v*side.dot(v)).normalized();out.append(np.array(Matrix((side,v,side.cross(v))).transposed()));prev=v
 return np.array(out)
fo,fn=frames(old),frames(new);target=co.copy();best=np.full(len(co),1e9);segidx=np.zeros(len(co),int);local=np.zeros(len(co))
for i in range(len(old)-1):
 d=old[i+1]-old[i];t=np.clip((co-old[i])@d/(d@d),0,1);dist=np.linalg.norm(co-old[i]-t[:,None]*d,axis=1);mask=dist<best;best[mask]=dist[mask];segidx[mask]=i;local[mask]=t[mask]
for j in np.where(parts==5)[0]:
 i=segidx[j];t=local[j];a=(1-t)*old[i]+t*old[i+1];b=(1-t)*new[i]+t*new[i+1];ro=(1-t)*fo[i]+t*fo[i+1];rn=(1-t)*fn[i]+t*fn[i+1];target[j]=b+rn@np.linalg.solve(ro,co[j]-a)
for v,c in zip(me.vertices,target):v.co=c

bm.free()
for f in me.polygons:f.use_smooth=True
co=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles()
np.savez(P/'work/fitted_geometry.npz',co=co,parts=parts,tri=np.array([t.vertices[:] for t in me.loop_triangles]),edges=np.array([e.vertices[:] for e in me.edges]))
(P/'work/tail_rest.json').write_text(json.dumps({'joints':new.tolist(),'original_joints':old.tolist(),'arc':samples.tolist(),'root_index':int(np.argmin(new[:,2]))},indent=2))
J={'Pelvis':[-.01,.025,1.15],'Spine':[-.01,.035,1.29],'Spine1':[-.01,.045,1.41],'Spine2':[-.01,.065,1.53],'Neck':[-.01,.085,1.74],'Head':[-.01,.035,1.88]}
for sd,sg in [('L',1),('R',-1)]:
 J.update({sd+'_Clavicle':[sg*.08,.065,1.53],sd+'_UpperArm':[sg*.273,.070,1.52],sd+'_Forearm':[sg*.440,.068,1.245],sd+'_Hand':[sg*.520,-.002,1.012]})
(P/'work/joints_final.json').write_text(json.dumps({'joints':J},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
src=(P/'scripts/prepare_water.py').read_text();tail=src[src.index('sc=bpy.context.scene;'):].replace("f'geometry_{name}.png'","f'fitted_{name}.png'");exec(compile(tail,'fitted_review','exec'))
