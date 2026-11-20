"""Measure skin rings and the three connected claw branches before building bone frames."""
from pathlib import Path
import bpy,bmesh,json,numpy as np
from mathutils import Vector
P=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(P/'work/step1.blend'))
body=bpy.data.objects['Body'];me=body.data;co=np.array([tuple(v.co) for v in me.vertices]);pv=np.array([v.value for v in me.attributes['piece'].data])
base=bmesh.new();base.from_mesh(me);base.verts.ensure_lookup_table();bmesh.ops.delete(base,geom=[v for v in base.verts if pv[v.index]!=0],context='VERTS')
M=json.loads((P/'work/meshy_joints_symmetric.json').read_text());J={k:np.array(v) for k,v in M['joints'].items()}
def ring(p,n):
 bm=base.copy();res=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=Vector(p),plane_no=Vector(n));es=[e for e in res['geom_cut'] if isinstance(e,bmesh.types.BMEdge)];adj={}
 for e in es:
  a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 seen=set();out=[]
 for v in adj:
  if v in seen:continue
  st=[v];vs=[]
  while st:
   a=st.pop()
   if a in seen:continue
   seen.add(a);vs.append(a);st.extend(adj[a])
  if len(vs)<4:continue
  points=np.array([tuple(v.co) for v in vs]);c=points.mean(0);vset=set(vs);per=sum(e.calc_length() for e in es if e.verts[0] in vset)
  if np.linalg.norm(c-p)<.15:out.append((c,per))
 bm.free();return min(out,key=lambda x:np.linalg.norm(x[0]-p)) if out else None
# X-ray fit: the hunched spine runs through the torso, with the neck pivot behind the skull.
J.update({k:np.array(v) for k,v in {'Spine':(0,.02,1.04),'Spine1':(0,.035,1.15),'Spine2':(0,.06,1.27),'Neck':(0,-.16,1.30),'Head':(0,-.27,1.32)}.items()})
report={};centres={}
for side in ('R',):
 sh,el,wr=(J[side+'_'+n] for n in ('UpperArm','Forearm','Hand'));direction=wr-el;direction/=np.linalg.norm(direction)
 candidates=[]
 for t in np.linspace(-.07,.07,29):
  q=wr+direction*t;r=ring(q,direction)
  if r is not None:candidates.append((r[1],r[0],t))
 assert candidates
 _,wrist,delta=min(candidates,key=lambda r:r[0]);J[side+'_Hand']=wrist
 r=ring(el,wrist-sh);J[side+'_Forearm']=r[0] if r is not None else el
 ankle=J[side+'_Foot'];cand=[]
 for z in np.linspace(.15,.27,25):
  r=ring(np.array([ankle[0],ankle[1],z]),np.array([0,0,1]))
  if r is not None and np.linalg.norm(r[0][:2]-ankle[:2])<.07:cand.append((r[1],r[0]))
 assert cand;J[side+'_Foot']=min(cand,key=lambda x:x[0])[1]
 report[side]={'wrist_shift':float(np.linalg.norm(wrist-wr)),'wrist_axis_offset':float(delta),'elbow_shift':float(np.linalg.norm(J[side+'_Forearm']-el)),'ankle_shift':float(np.linalg.norm(J[side+'_Foot']-ankle))}
 for suffix in ('Hand','Forearm','Foot'):J['L_'+suffix]=J['R_'+suffix]*np.array([-1,1,1])
 for t in np.linspace(0,1,30):
  q=sh*(1-t)+wrist*t;r=ring(q,wrist-sh)
  if r is not None:centres.setdefault(side,[]).append(r[0].tolist())
base.free()
E=np.array([tuple(e.vertices) for e in me.edges]);adj=[[] for _ in co]
for a,b in E:adj[a].append(int(b));adj[b].append(int(a))
def components(mask):
 ids=np.flatnonzero(mask);remaining=set(ids.tolist());out=[]
 while remaining:
  st=[remaining.pop()];comp=[]
  while st:
   i=st.pop();comp.append(i)
   for j in adj[i]:
    if j in remaining:remaining.remove(j);st.append(j)
  if len(comp)>=8:out.append(comp)
 return out
fingers={}
for side,sgn in [('R',-1),('L',1)]:
 wr=J[side+'_Hand'];hand=(pv==0)&(sgn*co[:,0]>.44)&(co[:,1]<.05)&(co[:,2]<wr[2]+.08)&(np.linalg.norm(co-wr,axis=1)<.90)
 levels=[]
 for z in np.arange(wr[2]+.02,.04,-.003):
  cs=components(hand&(co[:,2]<z))
  if cs:levels.append(cs)
 owners=[{v:i for i,c in enumerate(cs) for v in c} for cs in levels]
 kids=[[[j for j,c in enumerate(levels[k+1]) if owners[k].get(c[0])==i] for i in range(len(levels[k]))] for k in range(len(levels)-1)]+[[[] for _ in levels[-1]]]
 memo={}
 def chain(k,i):
  if (k,i) not in memo:
   c=kids[k][i];memo[k,i]=len(c)<=1 and (not c or chain(k+1,c[0]))
  return memo[k,i]
 branches=[]
 for k,cs in enumerate(levels):
  for i,c in enumerate(cs):
   parent=next((j for j,ch in enumerate(kids[k-1]) if i in ch),None) if k else None
   if chain(k,i) and len(c)>=15 and (not k or parent is None or not chain(k-1,parent)):branches.append(c)
 assert len(branches)==3,(side,[(len(c),co[c].mean(0).tolist()) for c in branches])
 branches.sort(key=lambda c:sgn*co[c].mean(0)[0])
 fingers[side]=[]
 for i,ids in enumerate(branches):
  pts=co[ids];top=pts[:,2].max();kn=pts[pts[:,2]>top-.014].mean(0);kn[2]+=.018;tip=pts[np.argmin(pts[:,2])];mid=pts[np.abs(pts[:,2]-(top-.035))<.02].mean(0)
  if not np.all(np.isfinite(mid)):mid=kn*.8+tip*.2
  fingers[side].append({'name':f'B_{side}_Finger{i}','base':kn.tolist(),'direction':(mid-kn).tolist(),'tip':tip.tolist(),'vertices':ids,'hard_vertices':[int(v) for v in ids if co[v,2]<top-.065]})
 print('CLAW_BRANCHES',side,[len(x['vertices']) for x in fingers[side]],flush=True)
out={'height_m':M['height_m'],'joints':{k:v.tolist() for k,v in J.items()},'report':report,'symmetry_plane_before_centre':M['symmetry_plane_before_centre'],'method':'Meshy body estimates, measured skin wrist/elbow/ankle rings, native-matched bilateral mesh.'}
(P/'work/joints_final.json').write_text(json.dumps(out,indent=2)+'\n');(P/'work/claws_fit.json').write_text(json.dumps(fingers,indent=2)+'\n');(P/'work/centrelines.json').write_text(json.dumps(centres,indent=2)+'\n')
print('RING_FIT',report,flush=True)
