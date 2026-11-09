from pathlib import Path
import sys,json,runpy
import numpy as np
p=Path(__file__).resolve().parents[1]
sys.argv=['fit_joints','--',str(p/'work/step1.blend'),'Body']
code=(p/'scripts/fit_joints.py').read_text().split('J, report = {}, {}')[0]
exec(compile(code,str(p/'scripts/fit_joints.py'),'exec'))
M=json.loads((p/'work/meshy_joints.json').read_text())['joints']
R=json.loads((p/'work/joints.json').read_text())
J={k:np.array(v) for k,v in M.items()};report={}
for side in ('R','L'):
    elbow=J[side+'_Forearm'];wr=J[side+'_Hand'];axis=wr-elbow;length=np.linalg.norm(axis);axis/=length
    samples=[]
    for t in np.linspace(-.015,.07,35):
        q=wr+axis*t;r=nearest_ring(q,axis,q)
        if r is not None and np.linalg.norm(r[0]-q)<.04 and r[1]>.10:
            samples.append((t,r[0],r[1]))
    assert samples
    t,centre,per=min(samples,key=lambda r:r[2])
    J[side+'_Hand']=centre
    J[side+'_Foot']=np.array(R['joints'][side+'_Foot'])
    # Claws stay rigid with the foot, and the toe pivot follows the actual forward axis.
    J[side+'_Toe0']=J[side+'_Foot']+np.array([0,-.095,-.095])
    report[side]={'wrist_offset_m':float(t),'perimeter_m':float(per),'samples':[[round(float(t),3),round(float(per),3)] for t,_,per in samples]}
    print('WRIST',side,centre,report[side])
J['Neck']=np.array([0,.015,1.46]);J['Head']=np.array([0,-.18,1.545])
out={'height_m':R['height_m'],'joints':{k:v.tolist() for k,v in J.items()},'report':report}
(p/'work/joints_final.json').write_text(json.dumps(out,indent=2))
sys.argv=['joint_xray','--',str(p/'work/step1.blend'),'Body',str(p/'work/joints_final.json'),str(p/'review/joints'),str(p/'work/meshy_joints.json')]
runpy.run_path(str(p/'scripts/joint_xray.py'),run_name='__main__')
