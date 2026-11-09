from pathlib import Path
import sys,runpy
p=Path(__file__).resolve().parents[1]
sys.argv=['reduce_rigged','--',str(p/'work/motion_final.blend'),str(p/'work/rig_reduced.blend')]
runpy.run_path(str(p/'scripts/reduce_rigged.py'),run_name='__main__')

runpy.run_path(str(p/'scripts/export_uploads.py'),run_name='__main__')
