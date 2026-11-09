import sys,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1]
for n in ('finish_motion.py','limit_influences.py'):
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
sys.argv=['reduce_rigged.py','--',str(P/'work/motion_limited.blend'),str(P/'work/motion_reduced.blend')]
runpy.run_path(str(P/'scripts/reduce_rigged.py'),run_name='__main__')
sys.argv=['clean_reduced.py','--',str(P/'work/motion_reduced.blend'),str(P/'work/motion_reduced.blend')]
runpy.run_path(str(P/'scripts/clean_reduced.py'),run_name='__main__')
runpy.run_path(str(P/'scripts/final_mesh_check.py'),run_name='__main__')
