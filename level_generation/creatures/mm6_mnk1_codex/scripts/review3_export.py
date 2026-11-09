import os,runpy
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
os.environ['TRACE_GLB']='export/mm6_mnk1_lod0.glb'
runpy.run_path(str(p/'scripts/run_trace.py'),run_name='__main__')
os.environ.pop('TRACE_GLB')
for name in ['check_master.py','review1_occlusion.py','review3_penetration.py','review3_anatomy.py','review3_cloth_metrics.py']:
 runpy.run_path(str(p/'scripts'/name),run_name='__main__')
