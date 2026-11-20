import runpy,sys
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ['build_axe.py','fit_motion.py','trim_hidden_body.py','rig_gates.py']:
 sys.argv=[n]+(['--','work/rig_v7.blend'] if n=='rig_gates.py' else []);runpy.run_path(str(P/'scripts'/n),run_name='__main__')
