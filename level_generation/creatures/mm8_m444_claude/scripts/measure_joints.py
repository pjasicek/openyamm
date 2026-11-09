"""Measure the source skeleton and independent mesh-ring joints before rig fitting."""
from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];r=p.parents[2]
steps=[('source_rest.py',[str(r/'anim_library/humanoid_set/Armed.glb')]),
       ('proportions.py',['source',str(r/'anim_library/humanoid_set/Armed.glb')]),
       ('fit_joints.py',[str(p/'work/step1.blend'),'Body'])]
for name,args in steps:
 print('STAGE',name,flush=True)
 sys.argv=[str(p/'scripts'/name),'--']+args
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
