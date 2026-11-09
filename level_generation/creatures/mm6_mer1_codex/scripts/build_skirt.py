import os,sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
def run(n,args=()):sys.argv=[n,'--',*map(str,args)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('twist_bones.py',['work/motion_v1.blend','work/motion_twist.blend'])
run('skirt_rig.py');run('skirt_sim.py',['skirt_v1.blend'])
