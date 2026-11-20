import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(name,*a):
 sys.argv=[name,'--',*map(str,a)]
 runpy.run_path(str(P/'scripts'/name),run_name='__main__')
run('finger_joints.py',P/'work/rig_v1.blend')
run('build_rig.py')
run('build_pilot.py')
run('solve_grips.py')
