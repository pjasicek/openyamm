"""Fit upper-body skin cross-sections; seeds are measured from the clay front/side views."""
import bpy,bmesh,json,math
import numpy as np
from pathlib import Path
from mathutils import Matrix,Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/socket_fit.blend'))
o=bpy.data.objects['BroodMother'];me=o.data
scale=json.loads((P/'review/geometry_ingest.json').read_text())['scale_from_meshy']
raw=np.load(P/'work/raw_mesh.npz')['vertices'];floor=float(raw[:,2].min())
R=Matrix.Rotation(math.radians(45),3,'Z')
def tx(p):return np.array(R@Vector(np.array(p)-[0,0,floor]))*scale
seeds={'Pelvis':[0,.16,.075],'Spine':[0,.175,.105],'Spine1':[0,.19,.13],'Spine2':[0,.205,.16],
 'Neck':[-.015,.23,.215],'Head':[-.055,.235,.275],
 'L_Clavicle':[.04,.205,.155],'L_UpperArm':[.1101,.2342,.1657],'L_Forearm':[.2193,.2205,.0754],'L_Hand':[.2617,.0062,.0348],
 'R_Clavicle':[-.045,.205,.15],'R_UpperArm':[-.1345,.2338,.1701],'R_Forearm':[-.2644,.1828,.0909],'R_Hand':[-.2062,-.0035,.0638]}
J={n:tx(p) for n,p in seeds.items()}
base=bmesh.new();base.from_mesh(me)
def rings(p,n):
 bm=base.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(p),plane_no=Vector(n),dist=1e-6)
 edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];adj={}
 for e in edges:
  a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 seen=set();out=[]
 for v in adj:
  if v in seen:continue
  stack=[v];seen.add(v);part=[]
  while stack:
   k=stack.pop();part.append(k)
   for w in adj[k]:
    if w not in seen:seen.add(w);stack.append(w)
  if len(part)>=5:
   co=np.array([tuple(v.co) for v in part]);out.append({'centre':co.mean(0),'points':co,'closed':all(len(adj[v])==2 for v in part)})
 bm.free();return out
report={}
for side in ('L','R'):
 shoulder=J[side+'_UpperArm'];elbow=J[side+'_Forearm'];wrist=J[side+'_Hand']
 for role,seed,direction in [('Forearm',elbow,wrist-shoulder),('Hand',wrist,wrist-elbow)]:
  rs=rings(seed,direction)
  if role=='Forearm':
   # At the bent elbow the section joins nearby shell pieces; the two visible skin hits define its centre.
   local=np.concatenate([r['points'] for r in rs]);local=local[np.linalg.norm(local-seed,axis=1)<.30]
   assert len(local)>=4,(side,len(local))
   J[side+'_'+role]=seed
   report[side+'_'+role]={'centre':seed.tolist(),'method':'midpoint of opposing clay-view skin ray hits',
     'section_local_centre':local.mean(0).tolist(),'section_points':len(local),
     'section_delta_m':float(np.linalg.norm(local.mean(0)-seed))}
   continue
  rs=[r for r in rs if np.linalg.norm(r['centre']-seed)<.30 and .20<np.linalg.norm(np.ptp(r['points'],axis=0))<.85]
  rs.sort(key=lambda r:np.linalg.norm(r['centre']-seed))
  if not rs:raise RuntimeError('No isolated skin ring: '+side+role)
  r=rs[0];J[side+'_'+role]=r['centre'];report[side+'_'+role]={'seed':seed.tolist(),'centre':r['centre'].tolist(),'seed_distance_m':float(np.linalg.norm(r['centre']-seed)),'ring_points':len(r['points']),'closed':r['closed'],'bounds':[r['points'].min(0).tolist(),r['points'].max(0).tolist()]}

base.free()
report['upper_body_seeds']='Clay front/side inspection, mesh-fitted wrist/elbow sections; unsupported seated anatomy uses local rig, no paid humanoid auto-rig.'
out={'joints':{k:v.tolist() for k,v in J.items()},'report':report,'raw_to_blender':{'scale':scale,'yaw_degrees':45,'floor_raw_z':floor}}
(P/'work/joints.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(report,indent=2))
