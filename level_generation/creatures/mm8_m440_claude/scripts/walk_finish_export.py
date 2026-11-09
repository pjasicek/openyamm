from pathlib import Path
import sys,os,runpy
p=Path(__file__).resolve().parents[1];sys.path.insert(0,str(p/'scripts'))
def run(n,*a):
 sys.argv=[n,'--',*[str(x) for x in a]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('walk_source_feet.py')
run('author_carry.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend','Walking:.15')
os.environ['TWIST_POSES_ONLY']='1';os.environ['TWIST_ACTIONS']='Walking';os.environ['FA']='.6'
run('twist_bones.py',p/'work/full_repaired.blend',p/'work/full_repaired.blend')
run('export_full.py')
