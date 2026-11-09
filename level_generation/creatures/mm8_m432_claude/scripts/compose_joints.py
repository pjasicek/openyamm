"""Compose the reviewed Meshy joints with measured glove-cuff wrist centres."""
import json
from pathlib import Path
import numpy as np
P=Path(__file__).resolve().parents[1]
m=json.loads((P/'work/meshy_joints.json').read_text())
s=json.loads((P/'work/shape_measurements.json').read_text())
j=m['joints']
# The repaired arms are symmetric, while the estimator has small left/right jitter.
for name in ('Clavicle','UpperArm','Forearm'):
    r=np.array(j['R_'+name]);l=np.array(j['L_'+name]);r[0]*=-1
    c=(r+l)/2
    j['L_'+name]=c.tolist();c[0]*=-1;j['R_'+name]=c.tolist()
for side in ('R','L'):
    assert s[side]['wrist_boundary_count']==13
    j[side+'_Hand']=s[side]['wrist_center']
    up=np.linalg.norm(np.array(j[side+'_UpperArm'])-j[side+'_Forearm'])
    fore=np.linalg.norm(np.array(j[side+'_Forearm'])-j[side+'_Hand'])
    assert .75<up/fore<1.25,(side,up,fore)
    print(side,'arm lengths',up,fore)
(P/'work/joints_final.json').write_text(json.dumps({'height_m':1.9,'joints':j,'basis':'Meshy axial/leg joints; symmetric arm estimates; measured open glove cuffs'},indent=1))
