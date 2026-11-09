import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('adjust_motion.py')
run('twist_bones.py',P/'work/rig_motion.blend',P/'work/rig_motion_twist.blend')
run('scan_deformation.py',P/'work/rig_motion_twist.blend')
