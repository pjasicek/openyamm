import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/fix_club_v3.py'),run_name='__main__')
sys.argv=['prop','--','work/prop_fixed.blend'];runpy.run_path(str(P/'scripts/prop_audit.py'),run_name='__main__')
