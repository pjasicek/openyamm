"""Measure anatomical palm planes from the four metacarpals, excluding the opposable thumb."""
import runpy,json,numpy as np
from pathlib import Path
P=Path(__file__).resolve().parents[1];g=runpy.run_path(str(P.parent/'claude_shared/gates/run_gates.py'),run_name='probe');a=g['Glb'](P/'export/mm8_m576_lod0.glb');cfg=json.loads((P/'gates.json').read_text());rows={}
for side in 'LR':
 H=a.names[f'B_{side}_Hand'];F=[a.names[f'B_{side}_Finger{i}'] for i in range(1,5)];w=a.rest[H,:3,3];pts=a.rest[F,:3,3];forward=g['unit'](pts.mean(0)-w);across=g['unit'](pts[0]-pts[-1]);normal=g['unit'](np.cross(across,forward))*(1 if side=='L' else -1)
 old=np.cross(pts[0]-w,pts[-1]-w)*(1 if side=='R' else -1)
 if normal@old<0:normal=-normal
 local=a.rest[H,:3,:3].T@normal;rows[side]={'palm_axis':local.tolist(),'delta_degrees':float(g['angle'](normal,old))}
 # Print both the generated finger plane and the source frame; visual verification chooses the correct axis.
 print('PALM PLANE',side,rows[side],flush=True)
(P/'review/hand_axes.json').write_text(json.dumps(rows,indent=2)+'\n')
