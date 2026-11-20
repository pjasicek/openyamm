import sys,runpy,os
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('finalize_motion.py')
run('jerk_probe.py',P/'work/master_complete.blend','Standing','Walking','Running','Attack','Hit','Death','Fidget')
os.environ['STEP']='.5'
run('sole_probe.py',P/'work/master_complete.blend','Standing','Walking','Running','Attack','Hit','Fidget')
run('export_runtime.py')
run('g6_sword_mesh.py',P/'export/mm8_m656_lod0.glb')
