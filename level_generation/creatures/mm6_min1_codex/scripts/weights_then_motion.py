import runpy,sys,os
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P)
def run(n,a=[]):
 sys.argv=[n,'--',*a];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
run('weights_minotaur.py');run('finger_weights.py',['work/rig_v3.blend','work/rig_v4.blend']);run('apply_grip.py',['work/rig_v4.blend','work/rig_v5.blend']);run('fit_motion.py')
