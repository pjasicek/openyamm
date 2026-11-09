"""Apply the runtime's equal world-space head-turn shares and probe the exported head surface."""
import runpy,json,math,numpy as np
from pathlib import Path
from mathutils import Quaternion,Matrix
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe')
cfg=json.loads((P/'gates.json').read_text());report=g['Report'](cfg);a=g['Glb'](P/'export/mm8_m576.glb');m=g['load_meshes'](a)[0];g['configure_mesh'](m,cfg,report)
desc={}
for name in ('B_Neck','B_Head'):
 i=a.names[name];ids=[]
 def walk(j):
  ids.append(j)
  for k in a.doc['nodes'][j].get('children',[]):walk(k)
 walk(i);desc[name]=ids
rows=[]
for name,clip,start,end in a.clips():
 if name in ('Dead','Death'):continue
 worst={'depth_mm':0,'clip':name}
 for t,pose in zip(np.linspace(start,end,max(2,int((end-start)*24)+1)),a.pose(clip,np.linspace(start,end,max(2,int((end-start)*24)+1)))):
  for yaw in (-25,0,25):
   for pitch in (-15,0,15):
    q=Quaternion((0,0,1),math.radians(yaw))@Quaternion((-1,0,0),math.radians(pitch));share=Quaternion(q.axis,q.angle/2).to_matrix();p=pose.copy()
    for joint,ids in desc.items():
     pivot=p[a.names[joint],:3,3].copy();R=np.array(share)
     p[ids,:3,:3]=np.einsum('ij,tjk->tik',R,p[ids,:3,:3]);p[ids,:3,3]=(p[ids,:3,3]-pivot)@R.T+pivot
    v=m.posed(p);depth,index=g['penetration'](m.head_surface.build(v),v[m.head_samples])
    if depth>worst['depth_mm']:worst={'depth_mm':depth,'clip':name,'time_s':float(t),'yaw':yaw,'pitch':pitch,'vertex':index}
 rows.append(worst);print('HEAD LOOK',worst,flush=True)
(P/'review/head_look_clearance.json').write_text(json.dumps({'max_yaw_degrees':25,'max_pitch_degrees':15,'rows':rows},indent=2)+'\n')
assert max(r['depth_mm'] for r in rows)<=10,rows
