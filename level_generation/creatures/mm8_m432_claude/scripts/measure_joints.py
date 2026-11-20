"""Independent ring estimates and source proportions before joint composition."""
from pathlib import Path
import os,sys,runpy
p=Path(__file__).resolve().parents[1];repo=p.parents[2]
os.chdir(p);sys.path.insert(0,str(p/'scripts'));sys.dont_write_bytecode=True
for script,args in [('proportions.py',['source',str(repo/'anim_library/humanoid_set/2Hand Sword.glb')]),('fit_joints.py',['work/body_clean.blend','Body'])]:
 sys.argv=[script,'--',*args];runpy.run_path(str(p/'scripts'/script),run_name='__main__')
