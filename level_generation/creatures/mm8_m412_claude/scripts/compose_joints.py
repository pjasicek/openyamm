"""Fit joints to the pirate's sleeve, wrist and boot sections; record Meshy deltas."""
import bpy, bmesh, json, sys, runpy
import numpy as np
from pathlib import Path
from mathutils import Vector
p=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(p/'work/step1.blend'))
o=bpy.data.objects['Body']; me=o.data
print('VALIDATION changes',me.validate(verbose=True))
co=np.array([v.co[:] for v in me.vertices]); pv=np.array([a.value for a in me.attributes['piece'].data])
M=json.loads((p/'work/meshy_joints.json').read_text())['joints']; J={k:np.array(v) for k,v in M.items()}
def section(piece,point,normal):
 bm=bmesh.new(); bm.from_mesh(me); bm.verts.ensure_lookup_table()
 bmesh.ops.delete(bm,geom=[v for v in bm.verts if pv[v.index]!=piece],context='VERTS')
 cut=bmesh.ops.bisect_plane(bm,geom=bm.verts[:]+bm.edges[:]+bm.faces[:],plane_co=Vector(point),plane_no=Vector(normal))
 edges=[e for e in cut['geom_cut'] if isinstance(e,bmesh.types.BMEdge)]
 adj={}
 for e in edges:
  a,b=e.verts;adj.setdefault(a,[]).append(b);adj.setdefault(b,[]).append(a)
 seen=set();loops=[]
 for v in adj:
  if v in seen:continue
  st=[v];comp=[]
  while st:
   q=st.pop()
   if q in seen:continue
   seen.add(q);comp.append(q);st.extend(adj[q])
  if len(comp)>=4 and all(len(adj[q])==2 for q in comp):
   coords=np.array([q.co[:] for q in comp]);loops.append(coords.mean(0))
 assert loops, (piece,point)
 centre=min(loops,key=lambda q:np.linalg.norm(q-point));bm.free();return centre
# The cuff/prosthesis confuses the generic minimum-ring wrist search; measure its local cross-section instead.
for sd,piece in [('R',3),('L',7)]:
 axis=J[sd+'_Hand']-J[sd+'_Forearm'];axis/=np.linalg.norm(axis)
 J[sd+'_Hand']=section(piece,J[sd+'_Hand'],axis)
 J[sd+'_Forearm']=section(0,J[sd+'_Forearm'],axis)
for sd,piece in [('L',5),('R',6)]:
 J[sd+'_Foot']=section(piece,J[sd+'_Foot'],[0,0,1])
report={k:{'delta_cm':round(float(np.linalg.norm(J[k]-M[k]))*100,2)} for k in J}
for sd in ('R','L'):
 u=np.linalg.norm(J[sd+'_Forearm']-J[sd+'_UpperArm']);f=np.linalg.norm(J[sd+'_Hand']-J[sd+'_Forearm'])
 report[sd+'_arm']={'upper_m':float(u),'fore_m':float(f),'elbow_t':float(u/(u+f))}
 assert 0.35<u/(u+f)<0.65,report[sd+'_arm']
print('JOINT REPORT',json.dumps(report))
(p/'work/joints_final.json').write_text(json.dumps({'height_m':1.7,'joints':{k:v.tolist() for k,v in J.items()},'report':report},indent=2))
sys.argv=['joint_xray.py','--',str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints_final'),str(p/'work/meshy_joints.json')]
runpy.run_path(str(p/'scripts/joint_xray.py'),run_name='__main__')
