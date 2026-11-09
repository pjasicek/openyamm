import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n,args in [('build_axe.py',[]),('fit_motion.py',[]),('trim_hidden_body.py',[]),('reduce_rigged.py',[str(P/'work/rig_v7.blend'),str(P/'work/rig_v8.blend')]),('finish_rig.py',[]),('solve_skirt.py',[]),('rig_gates.py',['work/gated_master.blend'])]:
 sys.argv=[n,'--',*args] if args else [n];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
