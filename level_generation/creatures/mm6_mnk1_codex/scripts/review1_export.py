import runpy,os
from pathlib import Path
p=Path(__file__).resolve().parents[1]
runpy.run_path(str(p/'scripts/export_runtime.py'),run_name='__main__')
os.environ['TRACE_GLB']='export/mm6_mnk1_lod0.glb'
runpy.run_path(str(p/'scripts/run_trace.py'),run_name='__main__')
runpy.run_path(str(p/'scripts/check_master.py'),run_name='__main__')
os.environ['GATE_BLEND']=str(p/'export/mm6_mnk1.blend')
runpy.run_path(str(p/'scripts/review1_occlusion.py'),run_name='__main__')
