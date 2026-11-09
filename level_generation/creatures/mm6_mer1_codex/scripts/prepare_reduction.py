import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/fix_club_final.py'),run_name='__main__')
sys.argv=['prop','--','work/prop_fixed.blend'];runpy.run_path(str(P/'scripts/prop_audit.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/apply_materials.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/close_sleeve_roots.py'),run_name='__main__')
for n in ['elbow_gate.py','audit_motion.py']:
 sys.argv=[n,'--','work/textured_master.blend','master'];runpy.run_path(str(P/'scripts'/n),run_name='__main__')
