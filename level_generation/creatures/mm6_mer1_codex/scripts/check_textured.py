import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.path.insert(0,str(P/'scripts'))
sys.argv=['prop','--','work/prop_clear.blend'];runpy.run_path(str(P/'scripts/prop_audit.py'),run_name='__main__')
for n in ['elbow_gate.py','audit_motion.py']:
 sys.argv=[n,'--','work/prop_audited.blend','textured'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
