import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/refine_surface.py'),run_name='__main__')
for n in ['elbow_gate.py','audit_motion.py']:
 sys.argv=[n,'--','work/rig_ready.blend','ready'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
