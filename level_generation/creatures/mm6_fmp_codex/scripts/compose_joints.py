"""Compose measured cuffs and arm rings with a symmetric skeleton inside the dress.
The long skirt fooled Meshy's knee/spine estimates; straight sleeves made line intersections unstable.
"""
import json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1];W=P/'work'
M=json.loads((W/'meshy_joints.json').read_text())['joints']
CL=json.loads((W/'centrelines.json').read_text())
TOP=json.loads((W/'topology_review.json').read_text())
J={k:np.array(v,dtype=float) for k,v in M.items()}
cx=-.004
for key in ('Clavicle','UpperArm'):
 a,b=J['L_'+key],J['R_'+key];mid=(a+b)/2;rx=abs(a[0]-b[0])/2
 for side,sg in [('L',1),('R',-1)]:J[side+'_'+key]=np.array([cx+sg*rx,mid[1],mid[2]])
for side,part in [('L','P02'),('R','P03')]:
 loops=next(x['boundary_loops'] for x in TOP if x['part']==part)
 J[side+'_Hand']=np.array(max(loops,key=lambda b:b['center'][2])['center'])
 # The A-pose elbow is nearly straight, so its intersection cannot constrain its distance along the arm.
 sh,wr=J[side+'_UpperArm'],J[side+'_Hand'];target=(sh+wr)/2;cs=np.array(CL[side+'_arm'])
 J[side+'_Forearm']=cs[np.argmin(np.linalg.norm(cs-target,axis=1))]
for key in ('Forearm','Hand'):
 a,b=J['L_'+key],J['R_'+key];mid=(a+b)/2;rx=abs(a[0]-b[0])/2
 for side,sg in [('L',1),('R',-1)]:J[side+'_'+key]=np.array([cx+sg*rx,mid[1],mid[2]])
# Axial centers are inside the inspected torso shell. Pelvis/upper legs are inferred beneath the opaque skirt.
for key,v in {'Pelvis':(cx,-.025,.90),'Spine':(cx,-.025,1.065),'Spine1':(cx,-.025,1.175),'Spine2':(cx,-.020,1.285),'Neck':(cx,-.005,1.370),'Head':(cx,-.025,1.450)}.items():J[key]=np.array(v)
for side,sg in [('L',1),('R',-1)]:
 for key,v in {'Thigh':(cx+sg*.092,-.025,.900),'Calf':(cx+sg*.116,-.027,.510),'Foot':(cx+sg*.140,.020,.115),'Toe0':(cx+sg*.140,-.090,.038)}.items():J[side+'_'+key]=np.array(v)
for side in ('L','R'):
 u=np.linalg.norm(J[side+'_Forearm']-J[side+'_UpperArm']);f=np.linalg.norm(J[side+'_Hand']-J[side+'_Forearm'])
 assert .75<u/f<1.35,(side,u,f)
 assert J[side+'_Toe0'][1]<J[side+'_Foot'][1]
report={'height_m':1.65,'joints':{k:list(v) for k,v in J.items()},'basis':'Symmetric Meshy shoulders; explicit hand cuff boundary centers; sleeve-ring midpoint elbows (straight-pose line intersection rejected); torso centers and symmetric lower legs fitted to silhouette. Knees and spine service guesses rejected behind/inside dress; see joints_estimates_v1.json.'}
(W/'joints_final.json').write_text(json.dumps(report,indent=2))
print('Composed symmetric joints; arm lengths',u,f)
