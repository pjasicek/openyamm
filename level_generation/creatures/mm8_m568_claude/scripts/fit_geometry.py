"""Repair the isolated thumb spike, shorten the trailing tail and measure skin sections."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step2.blend'))
body=bpy.data.objects['Body'];me=body.data
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([a.value for a in me.attributes['part'].data])
# One thumb vertex was displaced 28 cm; its mirrored counterpart preserves the valid local surface.
assert np.linalg.norm(co[906]-[-.334,-.306,1.135])<.003
ref=co.copy();ref[:,0]*=-1
near=np.argmin(np.linalg.norm(co-ref[906],axis=1))
nb=[e.vertices[1] if e.vertices[0]==906 else e.vertices[0] for e in me.edges if 906 in e.vertices]
q=co[nb].mean(0);q[0]*=-1
mirror=int(np.argmin(np.linalg.norm(co-q,axis=1)))
co[906]=co[mirror]*[-1,1,1]
# Preserve the vertical trunk/bend; smoothly compress only the rearward horizontal tail.
y=co[:,1];d=np.maximum(y-.15,0);co[:,1]=y-.52*(d-.13*(1-np.exp(-d/.13)))
for v,c in zip(me.vertices,co):v.co=c
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table()
bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7)
# Remove two duplicated outer digits confirmed in the close hand views, retaining thumb plus four fingers.
old_boundary={e for e in bm.edges if e.is_boundary}
remove=set()
for sign in [1,-1]:
 allowed={v for v in bm.verts if sign*v.co.x>.5 and v.co.z<1.145 and pa[v.index]==1}
 seen=set()
 for v in allowed:
  if v in seen:continue
  todo=[v];comp=set()
  while todo:
   w=todo.pop()
   if w in seen:continue
   seen.add(w);comp.add(w)
   todo.extend(e.other_vert(w) for e in w.link_edges if e.other_vert(w) in allowed)
  center=sum((v.co for v in comp),Vector())/len(comp)
  if len(comp)<90 and center.z>1.105 and center.y<-.30 and abs(center.x)>.75:remove.update(comp)
for v in bm.verts:
 x,y,z=abs(v.co.x),v.co.y,v.co.z
 if pa[v.index]==21 or (x>.765 and y>-.139 and z<1.17):remove.add(v)
remove=list(remove)
bmesh.ops.delete(bm,geom=remove,context='VERTS')
new_edges=[e for e in bm.edges if e.is_boundary and e not in old_boundary]
fill=bmesh.ops.holes_fill(bm,edges=new_edges,sides=0)
capverts=list({v for f in fill['faces'] for v in f.verts})
if capverts:bmesh.ops.smooth_vert(bm,verts=capverts,factor=.3,use_axis_x=True,use_axis_y=True,use_axis_z=True)
bmesh.ops.triangulate(bm,faces=fill['faces'])
bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
co=np.array([v.co[:] for v in me.vertices]);pa=np.array([a.value for a in me.attributes['part'].data])
bm=bmesh.new();bm.from_mesh(me);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if pa[v.index]!=1],context='VERTS')
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
raw=np.array([[0,-.055,1.38],[0,-.09,1.2],[0,-.16,1.0],[0,-.22,.8],[0,-.20,.6],[0,-.12,.4],[0,.05,.26],[0,.28,.19],[0,.50,.15],[0,.72,.12],[0,.95,.10],[0,1.18,.09],[0,1.40,.15]])
for _ in range(3):
 old=raw.copy()
 for i in range(len(raw)-1):raw[i]=section(old[i],old[min(i+1,len(old)-1)]-old[max(0,i-1)])[0]
raw[:,0]=0
raw[-1]=co[np.argmax(co[:,1])]
for _ in range(2):
 out=[raw[0]]
 for a,b in zip(raw[:-1],raw[1:]):out.extend([.75*a+.25*b,.25*a+.75*b])
 out.append(raw[-1]);raw=np.array(out)
arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(raw,axis=0),axis=1))];samples=np.linspace(0,arc[-1],27);joints=np.column_stack([np.interp(samples,arc,raw[:,i]) for i in range(3)])
root=int(np.argmin(np.linalg.norm(joints-[0,.20,.20],axis=1)))
(P/'work/tail_rest.json').write_text(json.dumps({'joints':joints.tolist(),'root_index':root,'arc':samples.tolist()},indent=2)+'\n')
J={}
for side,sgn in [('L',1),('R',-1)]:
 seeds={'UpperArm':[sgn*.29,.01,1.72],'Forearm':[sgn*.49,-.06,1.46],'Hand':[sgn*.67,-.14,1.28]}
 for name,seed in seeds.items():
  if name=='UpperArm':v=np.array(seed)
  else:v=section(np.array(seed),np.array([sgn*.6,-.2,-.7]))[0]
  J[side+'_'+name]=v.tolist()
print('JOINTS',J,'TAIL',joints.tolist())
bm.free()
(P/'work/joints_final.json').write_text(json.dumps({'joints':J},indent=2)+'\n')
me.calc_loop_triangles();np.savez(P/'work/fitted_geometry.npz',co=co,parts=pa,tri=np.array([t.vertices[:] for t in me.loop_triangles]),edges=np.array([e.vertices[:] for e in me.edges]))
for f in me.polygons:f.use_smooth=True
bpy.ops.wm.save_as_mainfile(filepath=str(P/'work/fitted_body.blend'))
src=(P/'scripts/inspect_geometry_v2.py').read_text();tail=src[src.index('sc=bpy.context.scene;'):].replace("f'geometry_v2_{name}.png'","f'fitted_{name}.png'").replace("(0,1.0,1.2),3.8","(0,.5,1.2),3.0").replace("(0,.15,1.15),2.5","(0,.4,1.15),3.0");exec(compile(tail,'fitted_review','exec'))
