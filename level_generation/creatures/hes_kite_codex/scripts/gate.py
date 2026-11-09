import sys,json,math
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P.parent/'claude_shared/floor'));from glb_pose import Glb,Model
g=Glb(P/'export/hes_ashkite.glb');m=Model(g);report={};parts=[]
for a in json.loads((P/'export/attachments.json').read_text()):
 am=Model(Glb(P/'export'/a['model']));points=np.concatenate([c for c,tri in am.skinned_positions(am.world({}))]);node=next(i for i,n in enumerate(g.json['nodes']) if n.get('name')==a['node']);parts.append((node,points))
for clip in m.clips:
 times=m.clip_times(clip);samples=sorted(set(times+[(a+b)/2 for a,b in zip(times,times[1:])]))
 bounds=[];radii=[];attachment_min=[];attachment_max=[];root_heights=[]
 for t in samples:
  world=m.world(m.sample(clip,t));root_heights.append(float(world[m.root_joints[0]][1,3]));pts=np.concatenate([c for c,tri in m.skinned_positions(world)]);radii.append(float(np.linalg.norm(pts[:,[0,2]],axis=1).max()))
  attachment_min.append(min(float((np.c_[p,np.ones(len(p))]@world[n].T)[:,1].min()) for n,p in parts))
  attachment_max.append(max(float((np.c_[p,np.ones(len(p))]@world[n].T)[:,1].max()) for n,p in parts))
  assert np.isfinite(pts).all();bounds.append([pts.min(0).tolist(),pts.max(0).tolist()])
 low=min(b[0][1] for b in bounds);high=max(b[1][1] for b in bounds)
 report[clip]={'samples':len(samples),'seconds':times[-1],'min_y':low,'max_y':high,'max_radius':max(radii),'attachment_min_y':min(attachment_min),'attachment_max_y':max(attachment_max),'root_vertical_travel':float(np.ptp(root_heights))}
 assert low>-.025,(clip,low)
 assert min(attachment_min)>-.025,(clip,'attachment',min(attachment_min))
 if clip in ['Fly','Run']:
  assert np.ptp(root_heights)<1e-5,(clip,'flight root bob',np.ptp(root_heights))
  legs={}
  for side in 'LR':
   for part in ['Thigh','Shin','Foot']:
    name=part+'_'+side;node=next(i for i,n in enumerate(g.json['nodes']) if n.get('name')==name)
    quaternions=np.array([m.sample(clip,t).get(node,m.rest[node])[1] for t in samples])
    angle=float(np.degrees(2*np.arccos(np.clip(np.abs(quaternions@quaternions[0]),0,1))).max())
    assert angle>5,(clip,name,'static leg',angle)
    legs[name]=angle
  report[clip]['leg_rotation_from_first_degrees']=legs
  a=np.concatenate([c for c,tri in m.skinned_positions(m.world(m.sample(clip,0)))])
  b=np.concatenate([c for c,tri in m.skinned_positions(m.world(m.sample(clip,times[-1])))])
  assert np.max(np.linalg.norm(a-b,axis=1))<1e-4
assert set(report)=={'Fly','Run','Attack','Sting','Cast','Hit','Death','Dead'}
(P/'review/runtime_gates.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
