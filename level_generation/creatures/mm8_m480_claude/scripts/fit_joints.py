"""Fit troll joints from skin cross-sections; service joints are search seeds only."""
from pathlib import Path
import bpy,bmesh,numpy as np,json,sys,runpy,math
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
s=P/'scripts/meshy_joints.py';sys.argv=[str(s),'--',str(P/'meshy/rig_v1/result_rigged_character_glb_url.glb'),str(P/'work/step1.blend')];runpy.run_path(str(s),run_name='__main__')
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'));body=bpy.data.objects['Body'];bm=bmesh.new();bm.from_mesh(body.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[v for v in bm.verts if body.data.attributes['piece'].data[v.index].value!=0],context='VERTS')
M={k:np.array(v) for k,v in json.loads((P/'work/meshy_joints.json').read_text())['joints'].items()};J={k:v.copy() for k,v in M.items()};report={};centrelines={}
def rings(p,n):
 b=bm.copy();res=bmesh.ops.bisect_plane(b,geom=b.verts[:]+b.edges[:]+b.faces[:],plane_co=Vector(p),plane_no=Vector(n));edges=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];adj={}
 for e in edges:
  a,c=e.verts;adj.setdefault(a,[]).append(c);adj.setdefault(c,[]).append(a)
 seen=set();out=[]
 for v in adj:
  if v in seen:continue
  stack=[v];comp=[]
  while stack:
   x=stack.pop()
   if x in seen:continue
   seen.add(x);comp.append(x);stack.extend(adj[x])
  if len(comp)<4 or any(len(adj[x])!=2 for x in comp):continue
  pts=np.array([tuple(x.co) for x in comp]);cs=set(comp);per=sum(e.calc_length() for e in edges if e.verts[0] in cs);out.append((pts.mean(0),per,pts))
 b.free();return out
def near(q,n,limit=.12):
 rs=[r for r in rings(q,n) if np.linalg.norm(r[0]-q)<limit];assert rs,('missing skin ring',q.tolist());return min(rs,key=lambda r:np.linalg.norm(r[0]-q))
for side in 'LR':
 sh,el,wr=[M[f'{side}_{n}'] for n in ['UpperArm','Forearm','Hand']];d=(wr-el)/np.linalg.norm(wr-el)
 options=[]
 for t in np.linspace(-.045,.045,31):
  q=wr+d*t;r=near(q,d)
  if .10<r[1]<.40:options.append(r)
 assert options
 J[f'{side}_Hand']=min(options,key=lambda r:r[1])[0];wr=J[f'{side}_Hand']
 # Local upper-arm and forearm ring centers independently locate the bent elbow.
 centres=[]
 for t in np.linspace(.12,.94,55):
  q=sh+(wr-sh)*t;rs=[r for r in rings(q,wr-sh) if np.linalg.norm(r[0]-q)<.10]
  if rs:
   r=min(rs,key=lambda r:np.linalg.norm(r[0]-q));centres.append((t,r[0],r[1]))
 ts=np.array([v[0] for v in centres]);cs=np.array([v[1] for v in centres]);centrelines[f'{side}_arm']=cs.tolist()
 def fit(mask):
  pts=cs[mask];assert len(pts)>=3,(side,ts.tolist());c=pts.mean(0);a=np.linalg.svd(pts-c)[2][0];return c,a if a@(wr-sh)>0 else -a
 a,u=fit((ts>.15)&(ts<.40));b,v=fit((ts>.63)&(ts<.90));ab=a-b;den=1-(u@v)**2
 if den>1e-4:
  t1=((u@v)*(v@ab)-(u@ab))/den;t2=((v@ab)-(u@v)*(u@ab))/den;elbow=((a+u*t1)+(b+v*t2))/2
 else:raise RuntimeError('Elbow hinge is too straight for independent two-line fit')
 frac=(elbow-sh)@(wr-sh)/np.dot(wr-sh,wr-sh);assert .25<frac<.75,(side,frac)
 J[f'{side}_Forearm']=near(elbow,u+v)[0]
 # Shoulder center on its measured arm cross-section, beneath the deltoid surface.
 J[f'{side}_UpperArm']=a+u*((sh-a)@u)
 for name in ['Calf','Foot']:
  seed=M[f'{side}_{name}'];r=near(seed,(0,0,1));J[f'{side}_{name}']=r[0]
 seed=M[f'{side}_Thigh'];hip_sections=[]
 for dz in np.linspace(.05,.16,12):
  q=seed-np.array([0,0,dz]);rs=[r for r in rings(q,(0,0,1)) if r[2][:,0].min()*r[2][:,0].max()>0 and np.linalg.norm(r[0]-q)<.12]
  if rs:hip_sections.append(min(rs,key=lambda r:np.linalg.norm(r[0]-q))[0])
 assert len(hip_sections)>=3,(side,'hip sections')
 pts=np.array(hip_sections);c=pts.mean(0);axis=np.linalg.svd(pts-c)[2][0];assert abs(axis[2])>.3;J[f'{side}_Thigh']=c+axis*((seed[2]-c[2])/axis[2])
 # Toe pivot at the ball of the broad foot, kept inside its actual ring.
 toe=M[f'{side}_Toe0'];J[f'{side}_Toe0']=near(toe,(0,1,0))[0]
 report[side]={'wrist_perimeter':min(options,key=lambda r:r[1])[1],'elbow_fraction':float(frac),'elbow_line_gap_m':float(np.linalg.norm((a+u*t1)-(b+v*t2))),'seed_offsets_m':{n:float(np.linalg.norm(J[f'{side}_{n}']-M[f'{side}_{n}'])) for n in ['UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0']}}
for name in ['Pelvis','Spine','Spine1','Spine2','Neck','Head']:
 q=M[name];rs=[r for r in rings(q,(0,0,1)) if r[2][:,0].min()<0<r[2][:,0].max()];assert rs,name;J[name]=min(rs,key=lambda r:np.linalg.norm(r[0]-q))[0]
# Keep the shoulders and pelvis paired; asymmetry of the generator is not intended skeletal asymmetry.
for n in ['UpperArm','Forearm','Hand','Thigh','Calf','Foot','Toe0']:
 a=J['L_'+n];b=J['R_'+n];v=(a+b*np.array([-1,1,1]))/2;J['L_'+n]=v;J['R_'+n]=v*np.array([-1,1,1])
for side,sg in [('L',1),('R',-1)]:
 # Clavicle root belongs inside the upper chest, not on the protruding shoulder skin.
 J[f'{side}_Clavicle']=J['Spine2']*.65+J[f'{side}_UpperArm']*.35
out={'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report};(P/'work/joints_final.json').write_text(json.dumps(out,indent=2)+'\n');(P/'work/centrelines.json').write_text(json.dumps(centrelines));print(json.dumps(out,indent=2));bm.free()
