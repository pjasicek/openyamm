import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
def run(n,*a):
 sys.argv=[n,'--',*map(str,a)];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('grip_solve.py',P/'work/rig_uv.blend','Standing','0')
run('apply_grip.py',P/'work/rig_uv.blend',P/'work/rig_uv_grip.blend')
run('reduce_rigged.py',P/'work/rig_uv_grip.blend',P/'work/rig_reduced.blend')
run('assemble.py')
