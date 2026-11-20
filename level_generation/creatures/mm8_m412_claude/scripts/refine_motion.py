import sys,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1];w=p/'work'
def run(n,*args):
 sys.argv=[n,'--',*[str(a) for a in args]];runpy.run_path(str(p/'scripts'/n),run_name='__main__')
run('swap_running.py',w/'rig_v5.blend',w/'rig_v2t.blend',w/'motion_runfit.blend')
run('fit_motion.py')
run('clip_timing.py')
