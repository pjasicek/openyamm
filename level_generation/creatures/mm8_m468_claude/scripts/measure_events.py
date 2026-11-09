import runpy,json,numpy as np
from pathlib import Path
p=Path(__file__).resolve().parents[1];g=runpy.run_path(str(p.parents[2]/'level_generation/creatures/claude_shared/gates/run_gates.py'),run_name='measure')
G=g['Glb'](p/'export/m468_full.glb');m=g['load_meshes'](G)[0];out={}
for name,a,start,end in G.clips():
 if name not in ('Attack','Cast'):continue
 rows=[]
 for t in np.arange(start,end+.001,1/30):
  pose=G.pose(a,np.array([t]))[0];points=m.posed(pose);row={'time':round(float(t),5),'frame':round(float(t)*30)}
  for s in 'LR':
   row[s]=pose[G.names[f'B_{s}_Hand'],:3,3].tolist();ix=np.array([n.startswith(f'B_{s}_Finger') for n in m.bone_names]);take=(ix[m.joints]*m.weights).sum(1)>.5;row[s+'_claw_front']=float(points[take,1].min())
  rows.append(row)
 out[name]=rows;print('EVENT',name,[(r['frame'],*[round(r[k],3) for k in ('R_claw_front','L_claw_front')]) for r in rows])
(p/'review/event_trajectories.json').write_text(json.dumps(out,indent=2))
