from pathlib import Path
import runpy,sys,json,math,numpy as np,bpy
from mathutils import Vector,Matrix
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'));import armik
api=runpy.run_path(str(p/'scripts/author_motion.py'));rig=api['rig'];records=api['records'][:60];hand=api['hand'];apply=api['apply'];current=api['current'];turn=api['turn']
from fit_boulder_arms import fit
results=[]
for raise_angle in [30,40,50,60,70]:
 for protract in [-40,-20,0,20,40]:
  for rock_extra in [0,20,40]:
   trial=[]
   for old in records:
    apply(old['pose']);h=float(np.clip((old['centre'].z-1.8)/.8,0,1))
    for side,sign in [('L',-1),('R',1)]:
     turn(f'B_{side}_Clavicle',(0,0,1),sign*15*h);turn(f'B_{side}_Clavicle',(0,1,0),-sign*10*h)
     turn(f'B_{side}_Clavicle',(0,1,0),sign*raise_angle*h);turn(f'B_{side}_Clavicle',(0,0,1),sign*protract*h)
    R=Matrix.Rotation(math.radians(rock_extra*h),3,'X');carry={side:{'target':old['centre']+R@(old['carry'][side]['target']-old['centre']),'rotation':R@old['carry'][side]['rotation']} for side in 'LR'}
    trial.append(dict(old,pose=current(),carry=carry))
   selected=fit(rig,trial,hand,apply);metrics={k:max(row[4][k] for side in 'LR' for row in selected[side]) for k in ['swing','twist','upper_roll']}
   metrics['reach']=max(row[4]['reach'] for side in 'LR' for row in selected[side][18:])
   score=1000000*max(0,metrics['reach']-.985)**2+max(0,metrics['swing']-68)**2+max(0,metrics['twist']-125)**2*.5+max(0,metrics['upper_roll']-58)**2*2
   row={'raise':raise_angle,'protract':protract,'rock_extra':rock_extra,'score':score,**metrics};results.append(row);print('SHOULDER_TRIAL',row,flush=True)
   (p/'work/shoulder_search.json').write_text(json.dumps(sorted(results,key=lambda r:r['score']),indent=2))
