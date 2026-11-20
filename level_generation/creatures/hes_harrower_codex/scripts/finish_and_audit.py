from pathlib import Path
import sys,runpy
P=Path(__file__).resolve().parents[1]
for name in ('polish_motion.py','foot_prepare.py','finish_motion.py','cloth_fit.py','final_fit.py'):
 sys.argv=[name];runpy.run_path(str(P/'scripts'/name),run_name='__main__')
sys.argv=['audit_all.py','--',str(P/'work/final.blend')]
runpy.run_path(str(P/'scripts/audit_all.py'),run_name='__main__')
