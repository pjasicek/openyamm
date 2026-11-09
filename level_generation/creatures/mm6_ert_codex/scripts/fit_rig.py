"""Fit bent arm centres and wrist/ankle constrictions against Meshy's independent estimates."""
import bpy,bmesh,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];BASE=bmesh.new();BASE.from_mesh(body.data)
M={n:np.array(v) for n,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()}
J={n:v.copy() for n,v in M.items()}; report={}
def ring(p,n):
 bm=BASE.copy();r=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=Vector(p),plane_no=Vector(n))
 edges={e for e in r['geom_cut'] if isinstance(e,bmesh.types.BMEdge)}; result=[]
 while edges:
  first=edges.pop();stack=[first];comp=[first]
  while stack:
   e=stack.pop()
   for v in e.verts:
    for q in v.link_edges:
     if q in edges:edges.remove(q);stack.append(q);comp.append(q)
  if len(comp)<4:continue
  lengths=np.array([e.calc_length() for e in comp]);mid=np.array([tuple((e.verts[0].co+e.verts[1].co)/2) for e in comp]);c=(mid*lengths[:,None]).sum(0)/lengths.sum()
  if np.linalg.norm(c-p)<.15 and .15<lengths.sum()<1.35:result.append((c,float(lengths.sum())))
 bm.free()
 return min(result,key=lambda x:np.linalg.norm(x[0]-p)) if result else None
def sample(a,b,ts):
 out=[]
 for t in ts:
  r=ring(a+(b-a)*t,b-a)
  if r:out.append((float(t),r[0],r[1]))
 assert len(out)>5,('Insufficient rings',len(out))
 return out
def line(points,d):
 c=points.mean(0);u=np.linalg.svd(points-c)[2][0];return c,u if u@d>0 else -u
for sd in ['L','R']:
 s,e,w=[M[f'{sd}_{n}'] for n in ['UpperArm','Forearm','Hand']]
 upper=sample(s,e,np.linspace(.45,.95,20));lower=sample(e,w,np.linspace(.30,1.9,45))
 # The service ends the forearm too early; find the constriction before the curled knuckles.
 candidates=[q for q in lower if .85<q[0]<1.7]
 wrist=min(candidates,key=lambda q:q[2]);J[f'{sd}_Hand']=wrist[1]
 c1,u1=line(np.array([q[1] for q in upper]),e-s)
 c2,u2=line(np.array([q[1] for q in lower if .3<q[0]<wrist[0]*.85]),w-e)
 A=np.column_stack([u1,-u2]);a,b=np.linalg.lstsq(A,c2-c1,rcond=None)[0]
 elbow=(c1+a*u1+c2+b*u2)/2
 assert np.linalg.norm(elbow-e)<.20,(sd,'elbow estimate diverged',elbow,e)
 J[f'{sd}_Forearm']=elbow
 # Re-slice perpendicular to the actual forearm; the initial service axis cuts these bent arms obliquely.
 tip=lower[-1][1]; refined=sample(elbow,tip,np.linspace(.30,1.12,45))
 distal=[q for q in refined if .55<q[0]<1.03]
 smallest=min(q[2] for q in distal)
 wrist=max((q for q in distal if q[2]<smallest*1.08),key=lambda q:q[0])
 J[f'{sd}_Hand']=wrist[1]
 ankle=M[f'{sd}_Foot'];ars=[]
 for z in np.linspace(.13,.33,30):
  r=ring(np.array([ankle[0],ankle[1],z]),np.array([0,0,1]))
  if r:ars.append(r)
 assert ars
 J[f'{sd}_Foot']=min(ars,key=lambda q:q[1])[0]
 report[sd]={'wrist_t':wrist[0],'wrist_perimeter':wrist[2],'wrist_shift':float(np.linalg.norm(wrist[1]-w)),
 'upper_length':float(np.linalg.norm(elbow-s)),'forearm_length':float(np.linalg.norm(wrist[1]-elbow)),
 'rings':{'upper':[[t,c.tolist(),v] for t,c,v in upper],'forearm':[[t,c.tolist(),v] for t,c,v in lower],'refined':[[t,c.tolist(),v] for t,c,v in refined]}}
 print('FITTED',sd,{k:v for k,v in report[sd].items() if k!='rings'})
BASE.free()
(P/'work/joints_final.json').write_text(json.dumps({'height_m':2.4,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2))
sys.path.insert(0,str(Path('level_generation/creatures/mm6_bar1_claude/scripts').resolve()))
import runpy
sys.argv=['joint_xray','--',str(P/'work/step1.blend'),'Body',str(P/'work/joints_final.json'),str(P/'review/joints_fitted'),str(P/'work/meshy_joints.json')]
runpy.run_path('level_generation/creatures/mm6_bar1_claude/scripts/joint_xray.py',run_name='__main__')
