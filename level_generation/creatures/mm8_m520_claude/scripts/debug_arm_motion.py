from pathlib import Path
import runpy,sys,json,numpy as np
p=Path('level_generation/creatures/mm8_m520_claude').resolve();sys.path.insert(0,str(p/'scripts'));import armik
api=runpy.run_path(str(p/'scripts/author_motion.py'));rig=api['rig'];records=api['records'];hand=api['hand'];apply=api['apply']
from fit_boulder_arms import fit
rows=[]
for i in range(36,57):
 apply(records[i]['pose']);row={'frame':i,'sides':{}}
 for side in 'LR':
  U,F,H=[armik.W(rig,f'B_{side}_{n}') for n in ['UpperArm','Forearm','Hand']];S,E,W=[x.translation for x in [U,F,H]]
  row['sides'][side]={'elbow_cross':(E-S).cross(W-E).length,'determinants':[x.to_3x3().determinant() for x in [U,F,H]],'source_quats':{n:list(records[i]['pose'][f'B_{side}_{n}'][0]) for n in ['Clavicle','UpperArm','Forearm','Hand']}}
 selected=fit(rig,[records[i]],hand,apply)
 row['best']={s:selected[s][0][4] for s in 'LR'};rows.append(row)
(p/'work/arm_debug.json').write_text(json.dumps(rows,indent=2));print('INDIVIDUAL',[(r['frame'],r['best']) for r in rows],flush=True)
