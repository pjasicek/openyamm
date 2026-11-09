from pathlib import Path
import json,runpy,numpy as np,bpy
from mathutils import Vector
from mathutils.kdtree import KDTree
p=Path(__file__).resolve().parents[1];g=runpy.run_path(str(p.parents[2]/'level_generation/creatures/claude_shared/gates/run_gates.py'),run_name='measure');G=g['Glb'](p/'export/m436_reduced.glb');m=g['load_meshes'](G)[0];config=json.loads((p/'gates.json').read_text());g['configure_mesh'](m,config,g['Report'](config));clips={n:(a,s,e) for n,a,s,e in G.clips()};out={}
bpy.ops.wm.open_mainfile(filepath=str(p/'work/full_reduced.blend'));body=bpy.data.objects['Body'];kd=KDTree(len(body.data.vertices))
for v in body.data.vertices:kd.insert(v.co,v.index)
kd.balance();piece=np.array([body.data.attributes['piece'].data[kd.find(Vector(v))[1]].value for v in m.rest])
for role in ['Standing','Dead']:
 a,start,end=clips[role];points=m.posed(G.pose(a,np.array([start]))[0]);out[role]={'height':float(np.ptp(points[:,2])),'floor':float(points[:,2].min()),'skin_low':float(points[piece==0,2].min()),'vest_low':float(points[piece==1,2].min()),'torso_low':float(points[(piece==0)&(m.rest[:,2]>.8)&(m.rest[:,2]<1.4)&(abs(m.rest[:,0])<.20),2].min())}
out['runtime_scale']=228.199022/out['Standing']['height']
for role in ['Walking','Running']:
 a,start,end=clips[role];times=np.linspace(start,end,round((end-start)*120)+1);poses=G.pose(a,times);ys={s:[] for s in 'LR'};low={s:[] for s in 'LR'}
 for pose in poses:
  points=m.posed(pose)
  for s in 'LR':
   ids,heel,toe=m.feet[s];ys[s].append(float(points[ids,1].mean()));low[s].append(float(points[ids,2].min()))
 velocity=[]
 for s in 'LR':
  v=np.gradient(ys[s],times);select=(np.array(low[s])<.015)&(v>.1)
  velocity.extend(v[select].tolist())
 out[role]={'duration':float(end-start),'stride_length':float(np.median(velocity)*(end-start)),'stance_samples':len(velocity)}
for role in ['Attack']:
 a,start,end=clips[role];times=np.linspace(start,end,round((end-start)*60)+1);poses=G.pose(a,times);rows=[]
 for t,pose in zip(times,poses):
  points=m.posed(pose);row={'time':float(t)}
  for s in 'LR':
   fingers=np.array([n.startswith(f'B_{s}_Finger') for n in m.bone_names]);take=(fingers[m.joints]*m.weights).sum(1)>.5;row[s]=float(points[take,1].min());row[s+'_hand']=pose[G.names[f'B_{s}_Hand'],:3,3].tolist()
  rows.append(row)
 out[role]={'forward_minimum':min(rows,key=lambda r:r['R'] if role=='Attack' else (r['L']+r['R'])/2),'trajectory':rows}
(p/'review/delivery_measurements.json').write_text(json.dumps(out,indent=2));print('MEASUREMENTS',json.dumps({k:({n:v for n,v in val.items() if n!='trajectory'} if isinstance(val,dict) else val) for k,val in out.items()}))
