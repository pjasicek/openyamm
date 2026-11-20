"""48 Hz signed distances against closed cloth volumes, with opening/hem caps marked."""
import bpy,json,math,os,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/os.environ.get('GATE_BLEND','work/animation_finish.blend')))
r=bpy.data.objects['Rig'];b=bpy.data.objects['Body'];me=b.data;sc=bpy.context.scene
pv=np.array([v.value for v in me.attributes['piece'].data]);tags=[v.value for v in me.attributes['cuff'].data]
rest=np.array([v.co[:] for v in me.vertices]);me.calc_loop_triangles()
sets={sd:[tuple(t.vertices) for t in me.loop_triangles if tags[t.polygon_index]==1 and (rest[list(t.vertices),0].mean()>0)==(sd=='L')] for sd in ['L','R']}
sets['robe']=[tuple(t.vertices) for t in me.loop_triangles if all(pv[i]==1 for i in t.vertices)]
def topology(faces,kind):
 edges={}
 for f in faces:
  for a,z in zip(f,f[1:]+f[:1]):
   key=tuple(sorted((a,z)));edges.setdefault(key,[]).append((a,z))
 boundary=[v[0] for v in edges.values() if len(v)==1];loops=[]
 while boundary:
  a,z=boundary.pop();loop=[a,z]
  while loop[-1]!=loop[0]:
   k=next(i for i,e in enumerate(boundary) if e[0]==loop[-1]);loop.append(boundary.pop(k)[1])
  loops.append(loop[:-1])
 if kind=='robe':opening=min(range(len(loops)),key=lambda i:rest[loops[i],2].mean())
 else:
  el=np.array(r.data.bones[f'B_{kind}_Forearm'].head_local);axis=np.array(r.data.bones[f'B_{kind}_Hand'].head_local)-el
  opening=max(range(len(loops)),key=lambda i:(rest[loops[i]].mean(0)-el)@axis)
 return faces,loops,opening
TOPO={k:topology(f,k) for k,f in sets.items()}
print('TOPOLOGY',[(k,len(v[0]),[len(x) for x in v[1]],v[2]) for k,v in TOPO.items()],flush=True)
def volume(P,kind):
 faces,loops,opening=TOPO[kind];verts=[Vector(v) for v in P];fs=list(faces);caps=set();center=None;normal=Vector()
 for li,loop in enumerate(loops):
  c=sum((verts[i] for i in loop),Vector())/len(loop);ci=len(verts);verts.append(c)
  for a,z in zip(loop,loop[1:]+loop[:1]):
   if li==opening:caps.add(len(fs));normal+=(verts[a]-c).cross(verts[z]-c)*-1
   fs.append((z,a,ci))
  if li==opening:center=c
 return BVHTree.FromPolygons(verts,fs,all_triangles=True),caps,center,normal.normalized()
def distance(tree,x):
 q,n,fi,d=tree.find_nearest(x)
 direction=Vector((.811,.357,.463)).normalized();origin=x.copy();hits=0
 for _ in range(64):
  hit=tree.ray_cast(origin,direction,10)[0]
  if hit is None:break
  hits+=1;origin=hit+direction*.000001
 else:raise AssertionError('Unresolved cloth ray traversal')
 return (-d if hits%2 else d),fi
cube=BVHTree.FromPolygons([(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)],[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)])
assert distance(cube,Vector((0,0,0)))[0]<0 and distance(cube,Vector((2,0,0)))[0]>0
report={};fps=sc.render.fps/sc.render.fps_base
for act in bpy.data.actions:
 r.animation_data.action=act;r.animation_data.action_slot=act.slots[0];end=float(act.frame_range[1]);row={'samples_48hz':0,'sleeves':{'worst_penetration_mm':0.,'invalid_vertices':0},'robe':{'worst_penetration_mm':0.,'invalid_vertices':0}}
 for f in sorted(set(list(np.arange(0,end+.00001,fps/48))+[end])):
  sc.frame_set(int(f),subframe=float(f%1));ev=b.evaluated_get(bpy.context.evaluated_depsgraph_get());em=ev.to_mesh();P=[v.co.copy() for v in em.vertices];ev.to_mesh_clear();vol={k:volume(P,k) for k in TOPO};row['samples_48hz']+=1
  for sd,pi in [('L',2),('R',3)]:
   own=vol[sd];other=vol['R' if sd=='L' else 'L']
   for i in np.where(pv==pi)[0]:
    x=P[i]
    # The opening plane is the actual animated outer hem, not a wrist proxy.
    if (x-own[2]).dot(own[3])>=0:continue
    d,_=distance(own[0],x);od,_=distance(other[0],x);d=min(d,od)
    if d>1e-5:
     row['sleeves']['invalid_vertices']+=1
     if d*1000>row['sleeves']['worst_penetration_mm']:row['sleeves'].update(worst_penetration_mm=d*1000,frame=float(f),vertex=int(i))
  tree,caps,center,normal=vol['robe']
  for i in np.where(np.isin(pv,[7,8]))[0]:
   x=P[i];d,fi=distance(tree,x)
   loops=TOPO['robe'][1];hem=loops[TOPO['robe'][2]];top=loops[1-TOPO['robe'][2]]
   hi=min(hem,key=lambda j:(x-P[j]).length_squared);h=P[hi]
   up=Vector()
   for g in me.vertices[hi].groups:
    name=b.vertex_groups[g.group].name
    if name in r.data.bones:up+=(r.pose.bones[name].matrix.to_3x3()@r.data.bones[name].matrix_local.to_3x3().inverted()@Vector((0,0,1)))*g.weight
   below=(x-h).dot(up.normalized())<=0 or x.z<min(P[j].z for j in hem)
   if d>1e-5 and not below and fi not in caps:
    row['robe']['invalid_vertices']+=1
    if d*1000>row['robe']['worst_penetration_mm']:row['robe'].update(worst_penetration_mm=d*1000,frame=float(f),vertex=int(i),position=list(x))
 row['pass']=all(row[k]['invalid_vertices']==0 for k in ['sleeves','robe']);report[act.name]=row;print('PENETRATION',act.name,row,flush=True)
(p/os.environ.get('PENETRATION_REPORT','review/round4/penetration_lod0.json')).write_text(json.dumps({'sample_rate_hz':48,'tolerance_mm':.01,'hand_vertices':int(sum(np.isin(pv,[2,3]))),'boot_vertices':int(sum(np.isin(pv,[7,8]))),'input':os.environ.get('GATE_BLEND','work/animation_finish.blend'),'input_sha256':hashlib.sha256((p/os.environ.get('GATE_BLEND','work/animation_finish.blend')).read_bytes()).hexdigest(),'method':'Nearest-surface distance signed by ray parity of closed cloth volumes. Sleeves allow exit beyond the actual animated opening plane. Robe allows exit through its hem cap or below the nearest hem in the animated local cloth frame (also below the complete hem in world height). 0.01 mm arithmetic tolerance. Every skin-hand and remaining boot vertex; removed upper shafts were always covered. Synthetic inside/outside sign self-test passes.','clips':report},indent=2))
if not os.environ.get('PENETRATION_PROBE'):assert all(row['pass'] for row in report.values()),report
