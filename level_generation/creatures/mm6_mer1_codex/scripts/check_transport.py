import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];sys.path.insert(0,str(P/'scripts'))
runpy.run_path(str(P/'scripts/fix_club_transport.py'),run_name='__main__')
sys.argv=['prop','--','work/reduction_master.blend','motion_final'];runpy.run_path(str(P/'scripts/candidate_prop.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/export_trace.py'),run_name='__main__')
