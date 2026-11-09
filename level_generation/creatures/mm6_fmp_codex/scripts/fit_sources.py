import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
for name,args in [('source_rest',['anim_library/humanoid_set/Relax.glb']),('proportions',['source','anim_library/humanoid_set/Relax.glb']),('fit_joints',[str(p/'work/step1.blend'),'Body'])]:
 sys.argv=[name+'.py','--',*args];runpy.run_path(str(p/'scripts'/(name+'.py')),run_name='__main__')
