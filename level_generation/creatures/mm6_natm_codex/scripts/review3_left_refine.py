"""Seat the shaft in the palm and refine the off-hand fingers against actual skin triangles."""
import json
from pathlib import Path
P=Path(__file__).resolve().parents[1]
g=json.loads((P/'work/round3_left_grip.json').read_text());g['handle_centre_hand_local'][1]-=.018;g['handle_centre_hand_local'][2]-=.002
(P/'work/round3_left_initial.json').write_text(json.dumps(g,indent=2))
s=(P/'scripts/refine_grip.py').read_text().split('# Render isolated')[0]
s=s.replace('rig_weighted.blend','runtime_lod0.blend').replace("['GripRef']","['Attack']").replace('frame_set(8)','frame_set(34)').replace('grip_pose_initial.json','round3_left_initial.json').replace('grip_pose.json','round3_left_grip.json').replace('grip_refinement.json','round3_left_refinement.json').replace('B_R_','B_L_').replace('Finger0.001','Finger01').replace('Finger0.002','Finger02').replace('co[:,0]<0','co[:,0]>0').replace('radius=.0157','radius=.012').replace('abs(y[j])>22','abs(y[j])>55')
exec(compile(s,str(P/'scripts/refine_grip.py'),'exec'))
