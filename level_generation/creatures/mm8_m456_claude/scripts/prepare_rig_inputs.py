from pathlib import Path
import runpy,sys
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
for file,args in [('source_rest.py',[str(repo/'anim_library/humanoid_set/1Hand.glb')]),('fit_joints.py',[str(p/'work/step1.blend'),'Body'])]:
 sys.argv=[file,'--']+args;runpy.run_path(str(p/'scripts'/file),run_name='__main__')
