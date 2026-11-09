import runpy,os
from pathlib import Path
os.environ['TRACE_GLB']='export/mm6_mnk1_lod0.glb'
runpy.run_path(str(Path(__file__).with_name('run_trace.py')),run_name='__main__')
