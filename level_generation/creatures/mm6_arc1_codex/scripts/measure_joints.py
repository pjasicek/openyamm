import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
sys.path.insert(0,str(P/'scripts'))
def run(n,args):
 sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('meshy_joints.py',['meshy/rig_v1/result_rigged_character_glb_url.glb','work/step1.blend'])
run('proportions.py',['source',P.parents[2]/'anim_library/humanoid_set/2Hand Bow.glb'])
run('fit_joints.py',['work/step1.blend','Body'])
run('compose_joints.py',[])
