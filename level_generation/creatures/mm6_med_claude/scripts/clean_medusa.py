"""Fit the native rearward tail and graft the detailed head under its collar."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([v.co[:] for v in me.vertices]);parts=np.array([x.value for x in me.attributes['part'].data])
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index]!=0],context='VERTS')
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
raw=np.array([[0,0,1.32],[0,.01,1.17],[0,0,1.02],[0,-.07,.87],[0,-.15,.71],[.02,-.17,.55],[.05,-.08,.39],[.14,.04,.23],[.30,.20,.16],[.47,.31,.21],[.61,.41,.31],[.73,.50,.36],[.84,.58,.30],[.936,.635,.17]])
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
new=old.copy();new[:,0]=0
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
for j in np.where((parts==0)&(co[:,2]<1.32))[0]:
 i=segidx[j];t=local[j];a=(1-t)*old[i]+t*old[i+1];b=(1-t)*new[i]+t*new[i+1];ro=(1-t)*fo[i]+t*fo[i+1];rn=(1-t)*fn[i]+t*fn[i+1];target[j]=b+rn@np.linalg.solve(ro,co[j]-a)
for v,c in zip(me.vertices,target):v.co=c
# Head and old snake locks are superseded; keep both original hands and arms.
bm.free();bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if parts[v.index] not in [0,1,4,6,9] or (parts[v.index]==0 and v.co.z>1.785)],context='VERTS');bm.to_mesh(me);bm.free()
with bpy.data.libraries.load(str(P/'work/head_source.blend'),link=False) as (src,dst):dst.objects=['HeadSource']
head=dst.objects[0];bpy.context.collection.objects.link(head)
hco=np.array([v.co[:] for v in head.data.vertices]);hp=np.array([x.value for x in head.data.attributes['part'].data]);base=hco[(hp==6)&(hco[:,2]<1.79)];center=(base.min(0)+base.max(0))*.5;delta=np.array([-center[0],-center[1],0])
for v in head.data.vertices:v.co+=Vector(delta)
for a in head.data.attributes['part'].data:a.value+=100
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);head.select_set(True);bpy.context.view_layer.objects.active=body;bpy.ops.object.join()
co=np.array([v.co[:] for v in body.data.vertices]);lift=-min(0,float(co[:,2].min()))
for v in body.data.vertices:v.co.z+=lift
new[:,2]+=lift
for f in body.data.polygons:f.use_smooth=True
body.data.calc_loop_triangles();co=np.array([v.co[:] for v in body.data.vertices]);pa=np.array([v.value for v in body.data.attributes['part'].data]);tri=np.array([t.vertices[:] for t in body.data.loop_triangles]);edges=np.array([e.vertices[:] for e in body.data.edges]);np.savez(P/'work/fitted_geometry.npz',co=co,parts=pa,tri=tri,edges=edges)
(P/'work/tail_rest.json').write_text(json.dumps({'joints':new.tolist(),'original_joints':old.tolist(),'arc':samples.tolist(),'root_index':int(np.argmin(new[:,2])),'head_delta':delta.tolist(),'lift':lift},indent=2)+'\n')
print('FITTED',len(co),len(tri),'tail length',samples[-1],'head shift',delta,'floor',co[:,2].min())
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
# Reuse the project review setup after its import/data preparation section.
src=(P/'scripts/prepare_medusa.py').read_text();tail=src[src.index('sc=bpy.context.scene;'):].replace("f'geometry_{name}.png'","f'fitted_{name}.png'");exec(compile(tail,'fitted_review','exec'))
