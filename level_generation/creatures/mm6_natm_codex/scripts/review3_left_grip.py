"""Fit the off hand to the actual wooden shaft, rather than mirroring the thicker wrapped grip."""
import sys,os,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1]
d=json.loads((P/'work/round3_pose_reference.json').read_text());g=json.loads((P/'work/grip_pose.json').read_text());rest={n:np.array(m)for n,m in d['rest'].items()}
axis=np.linalg.inv(rest['B_L_Hand'][:3,:3])@np.diag([-1,1,1])@rest['B_R_Hand'][:3,:3]@g['handle_axis_hand_local']
(P/'work/round3_left_source.json').write_text(json.dumps({'axis_hand':axis.tolist()}))
sys.argv=['grip_solve.py','--',str(P/'work/runtime_lod0.blend'),'Attack','34'];os.environ['R_HANDLE']='0.012'
s=(P/'scripts/grip_solve.py').read_text().replace('B_R_','B_L_').replace("['R']","['L']").replace('[:, 0] < 0','[:, 0] > 0').replace('Finger0.001','Finger01').replace('Finger0.002','Finger02').replace('grip_source.json','round3_left_source.json').replace('grip_pose.json','round3_left_grip.json')
exec(compile(s,str(P/'scripts/grip_solve.py'),'exec'))
