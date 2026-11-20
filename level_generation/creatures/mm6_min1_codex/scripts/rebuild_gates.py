import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
jobs=[('weights_minotaur.py',[]),('finger_weights.py',[str(P/'work/rig_v3.blend'),str(P/'work/rig_v4.blend')]),('apply_grip.py',[str(P/'work/rig_v4.blend'),str(P/'work/rig_v5.blend')]),('build_axe.py',[]),('fit_motion.py',[]),('trim_hidden_body.py',[]),('rig_gates.py',['work/rig_v7.blend'])]
for n,args in jobs:
 sys.argv=[n,'--',*args] if args else [n];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
