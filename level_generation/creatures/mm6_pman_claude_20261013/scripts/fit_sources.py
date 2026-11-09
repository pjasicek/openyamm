from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
def run(name,*args):
 sys.argv=[name,'--',*map(str,args)];runpy.run_path(str(p/'scripts'/name),run_name='__main__')
run('source_rest.py',repo/'anim_library/humanoid_set/Relax.glb')
run('proportions.py','source',repo/'anim_library/humanoid_set/Relax.glb')
run('fit_joints.py',p/'work/step1.blend','Body')
