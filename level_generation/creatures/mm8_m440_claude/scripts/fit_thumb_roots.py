"""Fit thumb metacarpals inside the palm; the connectivity cut isolates only their exposed distal halves."""
from pathlib import Path
import json
P=Path(__file__).resolve().parents[1]
j=json.loads((P/'work/finger_joints.json').read_text());fit=json.loads((P/'work/fingers_fit.json').read_text())
for side,sg in [('L',1),('R',-1)]:
 names=[f'B_{side}_Finger0',f'B_{side}_Finger01',f'B_{side}_Finger02'] if side=='L' else ['B_R_Finger0','B_R_Finger0.001','B_R_Finger0.002']
 pts=[[sg*.525,-.015,.760],[sg*.486,-.045,.712],[sg*.456,-.070,.682],[sg*.438,-.074,.660]]
 for name,pt in zip(names+[names[-1]+'_tip'],pts):j[side][name]=pt
 fit[side]['thumb']=pts
 assert all(.02<sum((a-b)**2 for a,b in zip(pts[i],pts[i+1]))**.5<.08 for i in range(3))
(P/'work/finger_joints.json').write_text(json.dumps(j,indent=2))
(P/'work/fingers_fit.json').write_text(json.dumps(fit,indent=2))
print('THUMB roots fitted inside palm; distal joints follow exposed thumb')
