import sys,os,runpy
from pathlib import Path
P=Path(__file__).resolve().parents[1];os.chdir(P);sys.dont_write_bytecode=True
for n in ['relax_idle.py','repair_neck_uv.py','export_runtime.py','build_lods.py','gate_equipment.py','export_trace_run.py']:
 runpy.run_path(str(P/'scripts'/n),run_name='__main__')
