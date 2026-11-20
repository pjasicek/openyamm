import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('fit_fingers.py',P/'work/rig_v1.blend')
run('finger_joints.py',P/'work/rig_v1.blend')
run('build_rig.py')
run('retarget_pipeline.py')
run('grip_pipeline.py')
